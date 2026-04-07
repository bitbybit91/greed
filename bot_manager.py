import logging
import os
import threading
import time
from typing import Dict, Optional

import sqlalchemy
import sqlalchemy.ext.declarative as sed
import telegram

import database
import duckbot
import localization
import nuconfig
import worker as worker_module

log = logging.getLogger(__name__)

# Maximum number of bots that can be configured
MAX_BOTS = 7


class BotInstance:
    """Represents a single running bot instance with its own polling loop and worker pool."""

    # Commands that trigger a new worker
    BOOTSTRAP_COMMANDS = ["/start"]

    def __init__(self, name: str, token: str, directory: str, cfg: nuconfig.NuConfig,
                 engine, bot_key: str = None, swap_engine=None, max_workers: int = 50, idle_timeout: int = 1800):
        self.name = name
        self.token = token
        self.directory = directory
        self.cfg = cfg
        self.engine = engine
        self.bot_key = bot_key
        self.swap_engine = swap_engine
        self._max_workers = max_workers
        self._idle_timeout = idle_timeout
        self._chat_workers: Dict[int, worker_module.Worker] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._poll_count = 0

        # Create bot instance with the specific token
        self.bot = duckbot.factory_with_token(cfg, token)(
            request=telegram.utils.request.Request(cfg["Telegram"]["con_pool_size"])
        )

        # Create the default localization
        default_language = cfg["Language"]["default_language"]
        self.default_loc = localization.Localization(language=default_language, fallback=default_language)

    def start(self):
        """Start the bot polling loop in a daemon thread."""
        if self._running:
            log.warning(f"Bot {self.name} is already running")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._poll_loop,
            name=f"Bot-{self.name}",
            daemon=True
        )
        self._thread.start()
        log.info(f"Bot {self.name} started in thread {self._thread.name}")

    def stop(self):
        """Signal the bot to stop polling."""
        self._running = False
        if self._thread and self._thread.is_alive():
            log.info(f"Stopping bot {self.name}...")
            self._thread.join(timeout=10)

    def _poll_loop(self):
        """Main polling loop that fetches updates from Telegram and dispatches them."""
        # Validate the bot token
        try:
            me = self.bot.get_me()
            if me is None:
                log.error(f"Bot {self.name}: invalid token, stopping.")
                return
            log.info(f"Bot {self.name}: @{me.username} is online!")
        except Exception as e:
            log.error(f"Bot {self.name}: failed to connect: {e}")
            return

        next_update = None
        update_timeout = self.cfg["Telegram"]["long_polling_timeout"]

        while self._running:
            try:
                updates = self.bot.get_updates(offset=next_update, timeout=update_timeout)
            except Exception as e:
                log.error(f"Bot {self.name}: error getting updates: {e}")
                time.sleep(self.cfg["Telegram"]["error_pause"])
                continue

            for update in updates:
                try:
                    self._handle_update(update)
                except Exception as e:
                    log.error(f"Bot {self.name}: error handling update: {e}")

            if updates:
                next_update = updates[-1].update_id + 1

            # Periodic cleanup every 60 poll cycles
            self._poll_count += 1
            if self._poll_count % 60 == 0:
                self._cleanup_idle_workers()

    def _handle_update(self, update):
        """Route a single update to the appropriate worker."""
        if update.message is not None:
            self._handle_message(update)
        if isinstance(update.callback_query, telegram.CallbackQuery):
            self._handle_callback_query(update)
        if isinstance(update.pre_checkout_query, telegram.PreCheckoutQuery):
            self._handle_pre_checkout_query(update)

    def _handle_message(self, update):
        """Handle an incoming message update."""
        if update.message.chat.type != "private":
            self.bot.send_message(update.message.chat.id, self.default_loc.get("error_nonprivate_chat"))
            return

        chat_id = update.message.chat.id

        # Check for /start command
        if isinstance(update.message.text, str) and update.message.text.startswith("/start"):
            log.info(f"Bot {self.name}: received /start from {chat_id}")
            old_worker = self._chat_workers.get(chat_id)
            if old_worker:
                old_worker.stop("request")

            # Check worker limit — evict oldest idle worker if at max
            if len(self._chat_workers) >= self._max_workers:
                self._evict_oldest_idle_worker()

            new_worker = worker_module.Worker(
                bot=self.bot,
                chat=update.message.chat,
                telegram_user=update.message.from_user,
                cfg=self.cfg,
                engine=self.engine,
                bot_id=self.bot_key,
                daemon=True
            )
            new_worker.start()
            self._chat_workers[chat_id] = new_worker
            return

        # Forward to existing worker
        receiving_worker = self._chat_workers.get(chat_id)
        if receiving_worker is None:
            self.bot.send_message(chat_id, self.default_loc.get("error_no_worker_for_chat"),
                                  reply_markup=telegram.ReplyKeyboardRemove())
            return

        if not receiving_worker.is_ready():
            self.bot.send_message(chat_id, self.default_loc.get("error_worker_not_ready"),
                                  reply_markup=telegram.ReplyKeyboardRemove())
            return

        if update.message.text == receiving_worker.loc.get("menu_cancel"):
            receiving_worker.queue.put(worker_module.CancelSignal())
        else:
            receiving_worker.queue.put(update)

    def _handle_callback_query(self, update):
        """Handle an inline keyboard callback query."""
        user_id = update.callback_query.from_user.id
        receiving_worker = self._chat_workers.get(user_id)

        if receiving_worker is None:
            self.bot.send_message(user_id, self.default_loc.get("error_no_worker_for_chat"))
            return

        if update.callback_query.data == "cmd_cancel":
            receiving_worker.queue.put(worker_module.CancelSignal())
            self.bot.answer_callback_query(update.callback_query.id)
        else:
            receiving_worker.queue.put(update)

    def _handle_pre_checkout_query(self, update):
        """Handle a pre-checkout query for Telegram Payments."""
        user_id = update.pre_checkout_query.from_user.id
        receiving_worker = self._chat_workers.get(user_id)

        if receiving_worker is None or \
                update.pre_checkout_query.invoice_payload != receiving_worker.invoice_payload:
            try:
                self.bot.answer_pre_checkout_query(
                    update.pre_checkout_query.id,
                    ok=False,
                    error_message=self.default_loc.get("error_invoice_expired")
                )
            except telegram.error.BadRequest:
                log.error("Pre-checkout query expired before an answer could be sent!")
            return

        receiving_worker.queue.put(update)

    def _evict_oldest_idle_worker(self):
        """Evict the worker that has been idle the longest to make room for a new one."""
        oldest_chat_id = None
        oldest_activity = time.time()

        for chat_id, w in self._chat_workers.items():
            activity = getattr(w, 'last_activity', 0)
            if activity < oldest_activity:
                oldest_activity = activity
                oldest_chat_id = chat_id

        if oldest_chat_id is not None:
            old_worker = self._chat_workers.pop(oldest_chat_id, None)
            if old_worker and old_worker.is_alive():
                log.info(f"Bot {self.name}: evicting idle worker for chat {oldest_chat_id}")
                old_worker.stop("evicted")

    def _cleanup_idle_workers(self):
        """Remove workers that have been idle beyond the timeout or are no longer alive."""
        now = time.time()
        to_remove = []

        for chat_id, w in self._chat_workers.items():
            # Remove dead workers
            if not w.is_alive():
                to_remove.append(chat_id)
                continue
            # Remove idle workers
            activity = getattr(w, 'last_activity', 0)
            if activity > 0 and (now - activity) > self._idle_timeout:
                to_remove.append(chat_id)

        for chat_id in to_remove:
            old_worker = self._chat_workers.pop(chat_id, None)
            if old_worker and old_worker.is_alive():
                log.debug(f"Bot {self.name}: cleaning up idle worker for chat {chat_id}")
                old_worker.stop("idle_timeout")

        if to_remove:
            log.info(f"Bot {self.name}: cleaned up {len(to_remove)} idle/dead workers, "
                     f"{len(self._chat_workers)} remaining")


class BotManager:
    """Manages multiple bot instances, reading configuration from [Bots.*] sections."""

    def __init__(self):
        self._bots: Dict[str, BotInstance] = {}

    @classmethod
    def build_from_config(cls, cfg: nuconfig.NuConfig, engine, swap_engine=None) -> "BotManager":
        """Build a BotManager from the config file's [Bots.*] sections."""
        manager = cls()

        try:
            bots_cfg = cfg["Bots"]
        except (KeyError, TypeError):
            log.info("No [Bots] section in config, multi-bot disabled.")
            return manager

        max_workers = bots_cfg.get("max_workers_per_bot", 50)
        idle_timeout = bots_cfg.get("worker_idle_timeout", 1800)

        bot_count = 0
        for key, value in bots_cfg.items():
            # Skip non-dict entries (max_workers_per_bot, worker_idle_timeout)
            if not isinstance(value, dict):
                continue

            if bot_count >= MAX_BOTS:
                log.warning(f"Maximum of {MAX_BOTS} bots reached, ignoring additional bot sections.")
                break

            bot_section = value
            if not bot_section.get("enabled", False):
                log.info(f"Bot [{key}] is disabled, skipping.")
                continue

            token = bot_section.get("token", "")
            name = bot_section.get("name", key)
            directory = bot_section.get("directory", name)

            if not token or token.endswith("_HERE"):
                log.warning(f"Bot [{key}] ({name}): no valid token configured, skipping.")
                continue

            # Create the bot's working directory if it doesn't exist
            if directory:
                os.makedirs(directory, exist_ok=True)
                log.debug(f"Bot [{key}] ({name}): ensured directory '{directory}' exists.")

            bot_instance = BotInstance(
                name=name,
                token=token,
                directory=directory,
                cfg=cfg,
                engine=engine,
                bot_key=key,
                swap_engine=swap_engine,
                max_workers=max_workers,
                idle_timeout=idle_timeout,
            )
            manager._bots[key] = bot_instance
            bot_count += 1
            log.info(f"Configured bot [{key}]: {name} (directory: {directory})")

        log.info(f"BotManager: {len(manager._bots)} bot(s) configured.")
        return manager

    def start_all(self):
        """Start all enabled bot instances."""
        for key, bot in self._bots.items():
            bot.start()
        log.info(f"BotManager: started {len(self._bots)} bot(s).")

    def stop_all(self):
        """Stop all running bot instances."""
        for key, bot in self._bots.items():
            bot.stop()
        log.info("BotManager: all bots stopped.")

    @property
    def bot_count(self) -> int:
        """Return the number of configured bots."""
        return len(self._bots)

    @property
    def bots(self) -> Dict[str, BotInstance]:
        """Return the dictionary of bot instances."""
        return self._bots
