import logging
import sys
import threading

import sqlalchemy
import sqlalchemy.ext.declarative as sed
import telegram

import database
import duckbot
import localization
import nuconfig
import worker

log = logging.getLogger(__name__)

# Conditionally import the crypto_swap module if available
try:
    import crypto_swap
except ImportError:
    crypto_swap = None


class BotInstance(threading.Thread):
    """A single bot instance that runs its own update loop with its own database engine."""

    # Bootstrap commands that trigger a new worker
    BOOTSTRAP_COMMANDS = {"/start"}

    def __init__(self, bot, engine, cfg, default_loc, swap_engine=None, name="BotInstance"):
        super().__init__(name=name, daemon=True)
        self.bot = bot
        self.engine = engine
        self.cfg = cfg
        self.default_loc = default_loc
        self.swap_engine = swap_engine
        self.chat_workers = {}
        self.next_update = None

    def run(self):
        """The main update loop for this bot instance."""
        log.info(f"{self.name} is starting!")
        while True:
            update_timeout = self.cfg["Telegram"]["long_polling_timeout"]
            log.debug(f"[{self.name}] Getting updates with timeout {update_timeout}s")
            try:
                updates = self.bot.get_updates(offset=self.next_update, timeout=update_timeout)
            except Exception as e:
                log.error(f"[{self.name}] Error getting updates: {e}")
                continue
            if updates is None:
                continue
            for update in updates:
                self._handle_update(update)
            if updates:
                self.next_update = updates[-1].update_id + 1

    def _handle_update(self, update):
        """Process a single update, mirroring the logic in core.py's main loop."""
        # Handle messages
        if update.message is not None:
            if update.message.chat.type != "private":
                log.debug(f"[{self.name}] Non-private chat: {update.message.chat.id}")
                self.bot.send_message(update.message.chat.id, self.default_loc.get("error_nonprivate_chat"))
                return
            if isinstance(update.message.text, str) and update.message.text.startswith("/start"):
                log.info(f"[{self.name}] /start from: {update.message.chat.id}")
                old_worker = self.chat_workers.get(update.message.chat.id)
                if old_worker:
                    old_worker.stop("request")
                new_worker = worker.Worker(
                    bot=self.bot,
                    chat=update.message.chat,
                    telegram_user=update.message.from_user,
                    cfg=self.cfg,
                    engine=self.engine,
                    daemon=True,
                )
                new_worker.start()
                self.chat_workers[update.message.chat.id] = new_worker
                return
            receiving_worker = self.chat_workers.get(update.message.chat.id)
            if receiving_worker is None:
                self.bot.send_message(
                    update.message.chat.id,
                    self.default_loc.get("error_no_worker_for_chat"),
                    reply_markup=telegram.ReplyKeyboardRemove(),
                )
                return
            if not receiving_worker.is_ready():
                self.bot.send_message(
                    update.message.chat.id,
                    self.default_loc.get("error_worker_not_ready"),
                    reply_markup=telegram.ReplyKeyboardRemove(),
                )
                return
            if update.message.text == receiving_worker.loc.get("menu_cancel"):
                receiving_worker.queue.put(worker.CancelSignal())
            else:
                receiving_worker.queue.put(update)

        # Handle callback queries
        if isinstance(update.callback_query, telegram.CallbackQuery):
            receiving_worker = self.chat_workers.get(update.callback_query.from_user.id)
            if receiving_worker is None:
                self.bot.send_message(
                    update.callback_query.from_user.id,
                    self.default_loc.get("error_no_worker_for_chat"),
                )
                return
            if update.callback_query.data == "cmd_cancel":
                receiving_worker.queue.put(worker.CancelSignal())
                self.bot.answer_callback_query(update.callback_query.id)
            else:
                receiving_worker.queue.put(update)

        # Handle pre-checkout queries
        if isinstance(update.pre_checkout_query, telegram.PreCheckoutQuery):
            receiving_worker = self.chat_workers.get(update.pre_checkout_query.from_user.id)
            if receiving_worker is None or \
                    update.pre_checkout_query.invoice_payload != receiving_worker.invoice_payload:
                log.debug(f"[{self.name}] Expired invoice: {update.pre_checkout_query.from_user.id}")
                try:
                    self.bot.answer_pre_checkout_query(
                        update.pre_checkout_query.id,
                        ok=False,
                        error_message=self.default_loc.get("error_invoice_expired"),
                    )
                except telegram.error.BadRequest:
                    log.error(f"[{self.name}] Pre-checkout query expired before answer could be sent!")
                return
            receiving_worker.queue.put(update)


class BotManager:
    """Manages multiple bot instances, each with its own independent database."""

    def __init__(self, cfg, fallback_db_uri):
        self.cfg = cfg
        self.fallback_db_uri = fallback_db_uri
        self.instances = []

    def build_from_config(self):
        """Read [Bots.*] sections from config and create a BotInstance for each enabled bot."""
        bots_cfg = self.cfg.data.get("Bots", {})
        default_language = self.cfg["Language"]["default_language"]
        fallback_language = self.cfg["Language"]["fallback_language"]

        for bot_key, bot_section in bots_cfg.items():
            if not bot_section.get("enabled", False):
                log.info(f"Bot '{bot_key}' is disabled, skipping.")
                continue

            bot_name = bot_section.get("name", bot_key)
            token = bot_section.get("token")
            if not token:
                log.error(f"Bot '{bot_key}' has no token, skipping.")
                continue

            # --- Per-bot database engine ---
            per_bot_db_uri = bot_section.get("database", self.fallback_db_uri)
            log.debug(f"Bot '{bot_key}': creating engine for {per_bot_db_uri}")
            per_bot_engine = sqlalchemy.create_engine(per_bot_db_uri)
            log.debug(f"Bot '{bot_key}': creating tables...")
            database.TableDeclarativeBase.metadata.create_all(bind=per_bot_engine)
            log.debug(f"Bot '{bot_key}': preparing deferred reflection...")
            sed.DeferredReflection.prepare(per_bot_engine)

            # --- Per-bot swap engine (if crypto_swap module is available and configured) ---
            per_bot_swap_engine = None
            if crypto_swap is not None and "CryptoSwap" in self.cfg.data:
                try:
                    per_bot_swap_engine = crypto_swap.SwapEngine(self.cfg, per_bot_engine)
                    log.debug(f"Bot '{bot_key}': crypto swap engine created.")
                except Exception as e:
                    log.warning(f"Bot '{bot_key}': failed to create swap engine: {e}")

            # --- Per-bot DuckBot ---
            log.debug(f"Bot '{bot_key}': creating DuckBot with token...")
            DuckBotClass = duckbot.factory_with_token(self.cfg, token)
            bot = DuckBotClass(
                request=telegram.utils.request.Request(self.cfg["Telegram"]["con_pool_size"])
            )

            # Test the token
            log.debug(f"Bot '{bot_key}': testing token...")
            me = bot.get_me()
            if me is None:
                log.error(f"Bot '{bot_key}': invalid token, skipping.")
                continue
            log.info(f"Bot '{bot_key}': @{me.username} token is valid.")

            # --- Per-bot localization ---
            default_loc = localization.Localization(
                language=default_language, fallback=fallback_language
            )

            # --- Create the BotInstance ---
            instance = BotInstance(
                bot=bot,
                engine=per_bot_engine,
                cfg=self.cfg,
                default_loc=default_loc,
                swap_engine=per_bot_swap_engine,
                name=f"Bot-{bot_name}",
            )
            self.instances.append(instance)
            log.info(f"Bot '{bot_key}' ({bot_name}) configured successfully.")

        if not self.instances:
            log.fatal("No enabled bots found in [Bots] config. Check your configuration.")
            sys.exit(1)

    def start_all(self):
        """Start all bot instances and block until they all finish (they run forever)."""
        for instance in self.instances:
            log.info(f"Starting {instance.name}...")
            instance.start()

        # Block main thread until all bot threads complete (they run forever as daemons,
        # so this effectively keeps the process alive)
        for instance in self.instances:
            instance.join()
