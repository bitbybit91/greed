"""potato_core.py — Standalone Potato Chat entry point for the greed bot.

Equivalent of core.py but targets the Potato Chat messaging platform instead
of Telegram.  Existing Telegram functionality in core.py is unchanged.

Differences from core.py:
- Imports potatobot instead of duckbot.
- Reads [PotatoChat] config section; exits early if enabled = false.
- Does NOT handle PreCheckoutQuery updates (Potato Chat has no Payments API).
- Does NOT start BotManager (single-bot only for Potato Chat).
- Uses cfg["PotatoChat"]["long_polling_timeout"] for the polling loop.
- Creates a SwapEngine when [CryptoSwap] is enabled (crypto-only checkout).

Run with:
    python3 potato_core.py
"""

import logging
import os
import sys
import threading

import sqlalchemy
import sqlalchemy.ext.declarative as sed
import telegram

import database
import localization
import nuconfig
import potatobot
import worker

try:
    import crypto_swap
except ImportError:
    crypto_swap = None  # type: ignore[assignment]

try:
    import coloredlogs
except ImportError:
    coloredlogs = None


def main():
    """Entry point for the Potato Chat bot. Should be run only in the main process."""
    # Rename the main thread for presentation purposes
    threading.current_thread().name = "PotatoCore"

    # Start logging setup
    log = logging.getLogger("potato_core")
    logging.root.setLevel("INFO")
    log.debug("Set logging level to INFO while the config is being loaded")

    # Ensure the template config file exists
    if not os.path.isfile("config/template_config.toml"):
        log.fatal("config/template_config.toml does not exist!")
        exit(254)

    # Check where the config path is located from the CONFIG_PATH environment variable
    config_path = os.environ.get("CONFIG_PATH", "config/config.toml")

    # If the config file does not exist, clone the template and exit
    if not os.path.isfile(config_path):
        log.debug("config/config.toml does not exist.")

        with open("config/template_config.toml", encoding="utf8") as template_cfg_file, \
                open(config_path, "w", encoding="utf8") as user_cfg_file:
            user_cfg_file.write(template_cfg_file.read())

        log.fatal("A config file has been created. Customize it, then restart greed!")
        exit(1)

    # Compare the template config with the user-made one
    with open("config/template_config.toml", encoding="utf8") as template_cfg_file, \
            open(config_path, encoding="utf8") as user_cfg_file:
        template_cfg = nuconfig.NuConfig(template_cfg_file)
        user_cfg = nuconfig.NuConfig(user_cfg_file)
        if not template_cfg.cmplog(user_cfg):
            log.fatal("There were errors while parsing the config file. Please fix them and restart greed!")
            exit(2)
        else:
            log.debug("Configuration parsed successfully!")

    # Check that the [PotatoChat] section exists and is enabled
    try:
        potato_cfg = user_cfg["PotatoChat"]
    except KeyError:
        print("The [PotatoChat] section is missing from your config file.")
        print("Add it (set enabled = true) and restart.")
        sys.exit(1)

    if not potato_cfg.get("enabled", False):
        print("Potato Chat support is disabled in the config (enabled = false).")
        print("Set enabled = true in [PotatoChat] and restart.")
        sys.exit(0)

    # Finish logging setup
    logging.root.setLevel(user_cfg["Logging"]["level"])
    stream_handler = logging.StreamHandler()
    if coloredlogs is not None:
        stream_handler.formatter = coloredlogs.ColoredFormatter(user_cfg["Logging"]["format"], style="{")
    else:
        stream_handler.formatter = logging.Formatter(user_cfg["Logging"]["format"], style="{")
    logging.root.handlers.clear()
    logging.root.addHandler(stream_handler)
    log.debug("Logging setup successfully!")

    # Ignore most python-telegram-bot logs
    logging.getLogger("telegram").setLevel("ERROR")

    # Find the database URI
    if db_engine := os.environ.get("DB_ENGINE"):
        log.debug("Sqlalchemy engine overridden by the DB_ENGINE envvar.")
    else:
        db_engine = user_cfg["Database"]["engine"]
        log.debug("Using sqlalchemy engine set in the configuration file.")

    # Create the database engine
    log.debug("Creating the sqlalchemy engine...")
    engine = sqlalchemy.create_engine(db_engine)
    log.debug("Binding metadata to the engine...")
    database.TableDeclarativeBase.metadata.bind = engine
    log.debug("Creating all missing tables...")
    database.TableDeclarativeBase.metadata.create_all()
    log.debug("Preparing the tables through deferred reflection...")
    sed.DeferredReflection.prepare(engine)

    # Create the Potato Chat bot instance
    bot = potatobot.factory(user_cfg)(
        request=telegram.utils.request.Request(potato_cfg["con_pool_size"])
    )

    # Test the token
    log.debug("Testing bot token...")
    me = bot.get_me()
    if me is None:
        logging.fatal("The token you have entered in the config file is invalid. Fix it, then restart greed.")
        sys.exit(1)
    log.debug("Bot token is valid!")

    # Build a SwapEngine if CryptoSwap is enabled (crypto-only checkout on Potato Chat)
    swap_engine = None
    try:
        crypto_cfg = user_cfg["CryptoSwap"]
        if crypto_cfg.get("enabled", False) and crypto_swap is not None:
            log.info("CryptoSwap is enabled — building SwapEngine...")
            swap_engine = crypto_swap.SwapEngine(user_cfg)
            log.info("SwapEngine ready.")
    except KeyError:
        pass  # [CryptoSwap] section is optional

    # Finding default language
    default_language = user_cfg["Language"]["default_language"]
    # Creating localization object
    default_loc = localization.Localization(language=default_language, fallback=default_language)

    # Create a dictionary linking the chat ids to the Worker objects
    chat_workers = {}

    # Current update offset; if None it will get the last 100 unparsed messages
    next_update = None

    log.info(f"@{me.username} is starting on Potato Chat!")

    # Main polling loop
    while True:
        update_timeout = potato_cfg["long_polling_timeout"]
        log.debug(f"Getting updates from Potato Chat with a timeout of {update_timeout} seconds")
        updates = bot.get_updates(offset=next_update, timeout=update_timeout)

        for update in updates:
            # If the update is a message...
            if update.message is not None:
                # Ensure the message has been sent in a private chat
                if update.message.chat.type != "private":
                    log.debug(f"Received a message from a non-private chat: {update.message.chat.id}")
                    bot.send_message(update.message.chat.id, default_loc.get("error_nonprivate_chat"))
                    continue
                # If the message is a start command...
                if isinstance(update.message.text, str) and update.message.text.startswith("/start"):
                    log.info(f"Received /start from: {update.message.chat.id}")
                    old_worker = chat_workers.get(update.message.chat.id)
                    if old_worker:
                        log.debug(f"Received request to stop {old_worker.name}")
                        old_worker.stop("request")
                    new_worker = worker.Worker(
                        bot=bot,
                        chat=update.message.chat,
                        telegram_user=update.message.from_user,
                        cfg=user_cfg,
                        engine=engine,
                        swap_engine=swap_engine,
                        daemon=True,
                    )
                    log.debug(f"Starting {new_worker.name}")
                    new_worker.start()
                    chat_workers[update.message.chat.id] = new_worker
                    continue
                # Forward the update to the corresponding worker
                receiving_worker = chat_workers.get(update.message.chat.id)
                if receiving_worker is None:
                    log.debug(f"Received a message in a chat without worker: {update.message.chat.id}")
                    bot.send_message(update.message.chat.id, default_loc.get("error_no_worker_for_chat"),
                                     reply_markup=telegram.ReplyKeyboardRemove())
                    continue
                if not receiving_worker.is_ready():
                    log.debug(f"Received a message in a chat where the worker wasn't ready yet: {update.message.chat.id}")
                    bot.send_message(update.message.chat.id, default_loc.get("error_worker_not_ready"),
                                     reply_markup=telegram.ReplyKeyboardRemove())
                    continue
                if update.message.text == receiving_worker.loc.get("menu_cancel"):
                    log.debug(f"Forwarding CancelSignal to {receiving_worker}")
                    receiving_worker.queue.put(worker.CancelSignal())
                else:
                    log.debug(f"Forwarding message to {receiving_worker}")
                    receiving_worker.queue.put(update)

            # If the update is an inline keyboard press...
            if isinstance(update.callback_query, telegram.CallbackQuery):
                receiving_worker = chat_workers.get(update.callback_query.from_user.id)
                if receiving_worker is None:
                    log.debug(f"Received a callback query in a chat without worker: {update.callback_query.from_user.id}")
                    bot.send_message(update.callback_query.from_user.id, default_loc.get("error_no_worker_for_chat"))
                    continue
                if update.callback_query.data == "cmd_cancel":
                    log.debug(f"Forwarding CancelSignal to {receiving_worker}")
                    receiving_worker.queue.put(worker.CancelSignal())
                    bot.answer_callback_query(update.callback_query.id)
                else:
                    log.debug(f"Forwarding callback query to {receiving_worker}")
                    receiving_worker.queue.put(update)

            # NOTE: PreCheckoutQuery updates are intentionally skipped on Potato Chat
            # because Telegram Payments are not supported.

        if len(updates):
            next_update = updates[-1].update_id + 1


# Run the main function only in the main process
if __name__ == "__main__":
    main()
