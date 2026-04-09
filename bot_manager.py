"""bot_manager.py — Multi-bot orchestrator for the greed crypto swap platform.

Manages the lifecycle of multiple Telegram bot instances that share a common
database engine and :class:`~crypto_swap.CryptoSwapEngine`.  Each bot runs its
own update-polling loop on a dedicated daemon thread.
"""

import logging
import signal
import threading
import time
from typing import Dict, List, Optional

import sqlalchemy
import sqlalchemy.ext.declarative as sed
import telegram

import database
import duckbot
import localization
import nuconfig
import worker
from crypto_swap import CryptoSwapEngine

log = logging.getLogger(__name__)


class BotInstance:
    """Represents a single running bot with its own polling thread and worker dict."""

    # Commands that trigger a new Worker thread for a chat.
    BOOTSTRAP_COMMANDS = ("/start", "/swap", "/price", "/wallet", "/history")

    def __init__(
        self,
        name: str,
        bot,
        cfg: nuconfig.NuConfig,
        engine,
        swap_engine: CryptoSwapEngine,
        default_loc: localization.Localization,
    ):
        self.name = name
        self.bot = bot
        self.cfg = cfg
        self.engine = engine
        self.swap_engine = swap_engine
        self.default_loc = default_loc

        # Maps chat_id -> Worker thread
        self.chat_workers: Dict[int, worker.Worker] = {}
        self._next_update: Optional[int] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the polling loop in a background daemon thread."""
        if self._running:
            log.warning(f"BotInstance '{self.name}' is already running.")
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop,
            name=f"Bot-{self.name}",
            daemon=True,
        )
        self._thread.start()
        log.info(f"BotInstance '{self.name}' started.")

    def stop(self, reason: str = "stop requested") -> None:
        """Signal the polling loop to exit and wait for the thread to finish."""
        self._running = False
        # Stop all active workers
        for chat_id, w in list(self.chat_workers.items()):
            if w.is_alive():
                log.debug(f"Stopping worker for chat {chat_id} in bot '{self.name}'")
                w.queue.put(worker.StopSignal(reason))
        if self._thread is not None:
            self._thread.join(timeout=10)
        log.info(f"BotInstance '{self.name}' stopped.")

    def is_alive(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _poll_loop(self) -> None:
        """Long-poll Telegram for updates and dispatch them to Worker threads."""
        update_timeout = self.cfg["Telegram"].get("long_polling_timeout", 30)
        log.debug(f"[{self.name}] Starting poll loop with timeout={update_timeout}s")

        while self._running:
            try:
                updates = self.bot.get_updates(
                    offset=self._next_update,
                    timeout=update_timeout,
                )
            except Exception as exc:
                log.error(f"[{self.name}] Error fetching updates: {exc}")
                time.sleep(self.cfg["Telegram"].get("error_pause", 5))
                continue

            for update in updates:
                self._dispatch_update(update)

            # Clean up dead workers
            dead = [cid for cid, w in self.chat_workers.items() if not w.is_alive()]
            for cid in dead:
                log.debug(f"[{self.name}] Removing dead worker for chat {cid}")
                del self.chat_workers[cid]

            if updates:
                self._next_update = updates[-1].update_id + 1

    def _dispatch_update(self, update: telegram.Update) -> None:
        """Route a single Telegram update to the correct Worker."""
        if update.message is not None:
            self._handle_message(update)
        elif isinstance(update.callback_query, telegram.CallbackQuery):
            self._handle_callback_query(update)
        elif isinstance(update.pre_checkout_query, telegram.PreCheckoutQuery):
            self._handle_pre_checkout(update)

    def _handle_message(self, update: telegram.Update) -> None:
        msg = update.message
        # Only allow private chats
        if msg.chat.type != "private":
            log.debug(f"[{self.name}] Ignoring non-private message from {msg.chat.id}")
            self.bot.send_message(msg.chat.id, self.default_loc.get("error_nonprivate_chat"))
            return

        text = msg.text or ""
        # /start or swap-related commands bootstrap a new worker
        if any(text.startswith(cmd) for cmd in self.BOOTSTRAP_COMMANDS):
            log.info(f"[{self.name}] Received '{text.split()[0]}' from chat {msg.chat.id}")
            old_worker = self.chat_workers.get(msg.chat.id)
            if old_worker and old_worker.is_alive():
                old_worker.stop("request")
            new_worker = worker.Worker(
                bot=self.bot,
                chat=msg.chat,
                telegram_user=msg.from_user,
                cfg=self.cfg,
                engine=self.engine,
                swap_engine=self.swap_engine,
                daemon=True,
            )
            new_worker.start()
            self.chat_workers[msg.chat.id] = new_worker
            return

        receiving_worker = self.chat_workers.get(msg.chat.id)
        if receiving_worker is None or not receiving_worker.is_alive():
            log.debug(f"[{self.name}] No active worker for chat {msg.chat.id}")
            self.bot.send_message(
                msg.chat.id,
                self.default_loc.get("error_no_worker_for_chat"),
                reply_markup=telegram.ReplyKeyboardRemove(),
            )
            return

        if not receiving_worker.is_ready():
            log.debug(f"[{self.name}] Worker not ready for chat {msg.chat.id}")
            self.bot.send_message(
                msg.chat.id,
                self.default_loc.get("error_worker_not_ready"),
                reply_markup=telegram.ReplyKeyboardRemove(),
            )
            return

        if text == receiving_worker.loc.get("menu_cancel"):
            receiving_worker.queue.put(worker.CancelSignal())
        else:
            receiving_worker.queue.put(update)

    def _handle_callback_query(self, update: telegram.Update) -> None:
        cq = update.callback_query
        receiving_worker = self.chat_workers.get(cq.from_user.id)
        if receiving_worker is None:
            self.bot.send_message(
                cq.from_user.id,
                self.default_loc.get("error_no_worker_for_chat"),
            )
            return
        if cq.data == "cmd_cancel":
            receiving_worker.queue.put(worker.CancelSignal())
            self.bot.answer_callback_query(cq.id)
        else:
            receiving_worker.queue.put(update)

    def _handle_pre_checkout(self, update: telegram.Update) -> None:
        pcq = update.pre_checkout_query
        receiving_worker = self.chat_workers.get(pcq.from_user.id)
        if receiving_worker is None or pcq.invoice_payload != receiving_worker.invoice_payload:
            try:
                self.bot.answer_pre_checkout_query(
                    pcq.id,
                    ok=False,
                    error_message=self.default_loc.get("error_invoice_expired"),
                )
            except telegram.error.BadRequest:
                log.error(f"[{self.name}] pre-checkout query expired before answer.")
            return
        receiving_worker.queue.put(update)


class BotManager:
    """Orchestrates multiple :class:`BotInstance` objects.

    Loads bot configurations from ``[Bots]`` config sections as well as the
    legacy single-bot ``[Telegram]`` token so backward compatibility is
    preserved.
    """

    def __init__(self, cfg: nuconfig.NuConfig, engine, swap_engine: CryptoSwapEngine):
        self._cfg = cfg
        self._engine = engine
        self._swap_engine = swap_engine
        self._instances: Dict[str, BotInstance] = {}
        self._shutdown_event = threading.Event()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def load_bots(self) -> None:
        """Instantiate bot instances from the configuration."""
        default_language = self._cfg["Language"]["default_language"]
        default_loc = localization.Localization(
            language=default_language, fallback=default_language
        )

        # Multi-bot entries under [Bots.*]
        bots_cfg = self._cfg.data.get("Bots", {})
        for bot_name, bot_section in bots_cfg.items():
            if not bot_section.get("enabled", True):
                log.info(f"Bot '{bot_name}' is disabled, skipping.")
                continue
            token = bot_section.get("token", "")
            if not token or token.startswith("123456"):
                log.warning(f"Bot '{bot_name}' has no valid token configured, skipping.")
                continue
            log.info(f"Loading bot '{bot_name}'…")
            bot = duckbot.factory_with_token(self._cfg, token)(
                request=telegram.utils.request.Request(
                    self._cfg["Telegram"].get("con_pool_size", 10)
                )
            )
            instance = BotInstance(
                name=bot_name,
                bot=bot,
                cfg=self._cfg,
                engine=self._engine,
                swap_engine=self._swap_engine,
                default_loc=default_loc,
            )
            self._instances[bot_name] = instance

        # Backward-compatible single-bot token under [Telegram]
        if not self._instances:
            log.info("No [Bots] entries found; using legacy [Telegram] token.")
            bot = duckbot.factory(self._cfg)(
                request=telegram.utils.request.Request(
                    self._cfg["Telegram"].get("con_pool_size", 10)
                )
            )
            instance = BotInstance(
                name="default",
                bot=bot,
                cfg=self._cfg,
                engine=self._engine,
                swap_engine=self._swap_engine,
                default_loc=default_loc,
            )
            self._instances["default"] = instance

    def start_all(self) -> None:
        """Start all loaded bot instances."""
        for name, instance in self._instances.items():
            log.info(f"Starting bot '{name}'…")
            instance.start()

    def stop_all(self, reason: str = "shutdown") -> None:
        """Stop all running bot instances."""
        for name, instance in self._instances.items():
            log.info(f"Stopping bot '{name}'…")
            instance.stop(reason)
        self._shutdown_event.set()

    def get_instance(self, name: str) -> Optional[BotInstance]:
        return self._instances.get(name)

    def list_instances(self) -> List[str]:
        return list(self._instances.keys())

    def wait_for_shutdown(self) -> None:
        """Block until :meth:`stop_all` is called (e.g. from a signal handler)."""
        self._shutdown_event.wait()

    def is_shutdown_requested(self) -> bool:
        """Return ``True`` if a shutdown has been requested via :meth:`stop_all`."""
        return self._shutdown_event.is_set()

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def log_heartbeat(self) -> None:
        """Log a status line for each bot instance (for monitoring)."""
        for name, instance in self._instances.items():
            alive = instance.is_alive()
            worker_count = len(instance.chat_workers)
            log.info(
                f"[heartbeat] bot='{name}' alive={alive} active_workers={worker_count}"
            )
