"""bot_manager.py — Multi-bot orchestrator for greed.

Manages multiple Telegram bot instances that all share a single database
engine and crypto swap engine. Each bot runs its own long-polling loop in
a dedicated daemon thread.
"""

import logging
import threading
from typing import Dict, List, Optional

import telegram

import database as db
import duckbot
import localization
import worker

log = logging.getLogger(__name__)


class BotInstance:
    """Encapsulates a single Telegram bot and its update dispatch loop."""

    # Commands that should spawn a new Worker instead of forwarding to an existing one
    BOOTSTRAP_COMMANDS = ("/start",)

    def __init__(
        self,
        name: str,
        bot,
        cfg,
        engine,
        swap_engine=None,
    ):
        self.name = name
        self.bot = bot
        self.cfg = cfg
        self.engine = engine
        self.swap_engine = swap_engine

        self._chat_workers: Dict[int, worker.Worker] = {}
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        default_language = cfg["Language"]["default_language"]
        self._default_loc = localization.Localization(
            language=default_language, fallback=default_language
        )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Start the polling thread for this bot."""
        me = self.bot.get_me()
        if me is None:
            log.error(f"[{self.name}] Token is invalid, bot will not start.")
            return
        log.info(f"[{self.name}] @{me.username} is starting!")
        self._thread = threading.Thread(
            target=self._poll_loop,
            name=f"Bot-{self.name}",
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        """Signal the polling loop to stop."""
        log.info(f"[{self.name}] Stop requested.")
        self._stop_event.set()

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ------------------------------------------------------------------
    # Update polling
    # ------------------------------------------------------------------

    def _poll_loop(self):
        """Main polling loop. Runs in a dedicated daemon thread."""
        next_update = None
        update_timeout = self.cfg["Telegram"]["long_polling_timeout"]
        log.info(f"[{self.name}] Polling started.")
        while not self._stop_event.is_set():
            try:
                updates = self.bot.get_updates(
                    offset=next_update, timeout=update_timeout
                )
            except Exception as exc:
                log.error(f"[{self.name}] Error fetching updates: {exc}")
                continue

            for update in updates:
                self._dispatch(update)

            if updates:
                next_update = updates[-1].update_id + 1
        log.info(f"[{self.name}] Polling stopped.")

    def _dispatch(self, update: telegram.Update):
        """Dispatch a single Telegram update to the appropriate worker."""
        if update.message is not None:
            self._handle_message(update)
        elif isinstance(update.callback_query, telegram.CallbackQuery):
            self._handle_callback_query(update)
        elif isinstance(update.pre_checkout_query, telegram.PreCheckoutQuery):
            self._handle_pre_checkout_query(update)

    def _handle_message(self, update: telegram.Update):
        message = update.message
        if message.chat.type != "private":
            log.debug(f"[{self.name}] Non-private message from {message.chat.id}, ignoring.")
            self.bot.send_message(
                message.chat.id, self._default_loc.get("error_nonprivate_chat")
            )
            return

        text = message.text or ""
        is_bootstrap = any(text.startswith(cmd) for cmd in self.BOOTSTRAP_COMMANDS)

        if is_bootstrap:
            log.info(f"[{self.name}] Bootstrap command from {message.chat.id}")
            old = self._chat_workers.get(message.chat.id)
            if old:
                old.stop("request")
            new_worker = worker.Worker(
                bot=self.bot,
                chat=message.chat,
                telegram_user=message.from_user,
                cfg=self.cfg,
                engine=self.engine,
                swap_engine=self.swap_engine,
                daemon=True,
            )
            new_worker.start()
            self._chat_workers[message.chat.id] = new_worker
            return

        receiving_worker = self._chat_workers.get(message.chat.id)
        if receiving_worker is None:
            log.debug(f"[{self.name}] No worker for {message.chat.id}")
            self.bot.send_message(
                message.chat.id,
                self._default_loc.get("error_no_worker_for_chat"),
                reply_markup=telegram.ReplyKeyboardRemove(),
            )
            return
        if not receiving_worker.is_ready():
            log.debug(f"[{self.name}] Worker not ready for {message.chat.id}")
            self.bot.send_message(
                message.chat.id,
                self._default_loc.get("error_worker_not_ready"),
                reply_markup=telegram.ReplyKeyboardRemove(),
            )
            return
        if text == receiving_worker.loc.get("menu_cancel"):
            receiving_worker.queue.put(worker.CancelSignal())
        else:
            receiving_worker.queue.put(update)

    def _handle_callback_query(self, update: telegram.Update):
        cq = update.callback_query
        receiving_worker = self._chat_workers.get(cq.from_user.id)
        if receiving_worker is None:
            log.debug(f"[{self.name}] No worker for callback from {cq.from_user.id}")
            self.bot.send_message(
                cq.from_user.id, self._default_loc.get("error_no_worker_for_chat")
            )
            return
        if cq.data == "cmd_cancel":
            receiving_worker.queue.put(worker.CancelSignal())
            self.bot.answer_callback_query(cq.id)
        else:
            receiving_worker.queue.put(update)

    def _handle_pre_checkout_query(self, update: telegram.Update):
        pcq = update.pre_checkout_query
        receiving_worker = self._chat_workers.get(pcq.from_user.id)
        if receiving_worker is None or pcq.invoice_payload != receiving_worker.invoice_payload:
            log.debug(f"[{self.name}] Expired invoice for {pcq.from_user.id}")
            try:
                self.bot.answer_pre_checkout_query(
                    pcq.id,
                    ok=False,
                    error_message=self._default_loc.get("error_invoice_expired"),
                )
            except telegram.error.BadRequest:
                log.error(f"[{self.name}] pre-checkout query expired before answer could be sent!")
            return
        receiving_worker.queue.put(update)


# ---------------------------------------------------------------------------
# BotManager
# ---------------------------------------------------------------------------

class BotManager:
    """Manages multiple BotInstance objects, all sharing a database engine."""

    def __init__(self, cfg, engine, swap_engine=None):
        self._cfg = cfg
        self._engine = engine
        self._swap_engine = swap_engine
        self._instances: List[BotInstance] = []

    def build_from_config(self):
        """Instantiate BotInstances from the [Bots] config section or fall back to single-bot mode."""
        bots_cfg = self._cfg.data.get("Bots")
        if bots_cfg:
            for bot_name, bot_section in bots_cfg.items():
                if not bot_section.get("enabled", True):
                    log.info(f"Bot '{bot_name}' is disabled, skipping.")
                    continue
                token = bot_section.get("token")
                if not token:
                    log.warning(f"Bot '{bot_name}' has no token, skipping.")
                    continue
                DuckBotClass = duckbot.factory_with_token(self._cfg, token)
                bot = DuckBotClass(
                    request=telegram.utils.request.Request(
                        self._cfg["Telegram"]["con_pool_size"]
                    )
                )
                instance = BotInstance(
                    name=bot_section.get("name", bot_name),
                    bot=bot,
                    cfg=self._cfg,
                    engine=self._engine,
                    swap_engine=self._swap_engine,
                )
                self._instances.append(instance)
                log.info(f"Registered bot '{bot_name}'.")
        else:
            # Single-bot fallback
            DuckBotClass = duckbot.factory(self._cfg)
            bot = DuckBotClass(
                request=telegram.utils.request.Request(
                    self._cfg["Telegram"]["con_pool_size"]
                )
            )
            instance = BotInstance(
                name="main",
                bot=bot,
                cfg=self._cfg,
                engine=self._engine,
                swap_engine=self._swap_engine,
            )
            self._instances.append(instance)

    def start_all(self):
        """Start all registered BotInstances."""
        for instance in self._instances:
            instance.start()

    def stop_all(self):
        """Stop all registered BotInstances gracefully."""
        for instance in self._instances:
            instance.stop()

    def instances(self) -> List[BotInstance]:
        return list(self._instances)
