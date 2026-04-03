import logging
import os
import signal
import sys
import threading
import time

import sqlalchemy
import sqlalchemy.ext.declarative as sed
import telegram

import database
import duckbot
import localization
import nuconfig
import worker
from bot_manager import BotManager
from crypto_swap import CryptoSwapEngine

try:
    import coloredlogs
except ImportError:
    coloredlogs = None


def main():
    """The core code of the program. Should be run only in the main process!"""
    # Rename the main thread for presentation purposes
    threading.current_thread().name = "Core"

    # Start logging setup
    log = logging.getLogger("core")
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
            # Copy the template file to the config file
            user_cfg_file.write(template_cfg_file.read())

        log.fatal("A config file has been created."
                  " Customize it, then restart greed!")
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

    # Ignore most python-telegram-bot logs, as they are useless most of the time
    logging.getLogger("telegram").setLevel("ERROR")

    # Find the database URI
    # Through environment variables first
    if db_engine := os.environ.get("DB_ENGINE"):
        log.debug("Sqlalchemy engine overridden by the DB_ENGINE envvar.")
    # Then via the config file
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

    # Create the crypto swap engine (shared across all bots / workers)
    swap_engine = CryptoSwapEngine(user_cfg)
    log.debug("CryptoSwapEngine initialised.")

    # Create and populate the bot manager
    bot_manager = BotManager(cfg=user_cfg, engine=engine, swap_engine=swap_engine)
    bot_manager.load_bots()

    # Verify that at least one bot has a valid token
    log.debug("Testing bot token(s)…")
    for bot_name in bot_manager.list_instances():
        instance = bot_manager.get_instance(bot_name)
        me = instance.bot.get_me()
        if me is None:
            log.fatal(
                f"The token for bot '{bot_name}' is invalid. Fix it, then restart greed."
            )
            sys.exit(1)
        log.info(f"@{me.username} (bot='{bot_name}') token verified.")

    # ------------------------------------------------------------------ #
    # Graceful shutdown signal handlers                                    #
    # ------------------------------------------------------------------ #

    def _shutdown(signum, frame):
        log.info(f"Received signal {signum}, shutting down…")
        bot_manager.stop_all("shutdown")

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # ------------------------------------------------------------------ #
    # Start all bots                                                       #
    # ------------------------------------------------------------------ #

    bot_manager.start_all()
    log.info("All bots started.")

    # ------------------------------------------------------------------ #
    # Heartbeat loop — keep the main thread alive and log health status   #
    # ------------------------------------------------------------------ #

    heartbeat_interval = 300  # seconds between heartbeat log entries
    last_heartbeat = time.monotonic()

    try:
        while not bot_manager._shutdown_event.is_set():
            # Sleep in short increments to remain responsive to signals
            time.sleep(1)
            now = time.monotonic()
            if now - last_heartbeat >= heartbeat_interval:
                bot_manager.log_heartbeat()
                last_heartbeat = now
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt received, shutting down…")
        bot_manager.stop_all("keyboard_interrupt")

    log.info("greed has shut down.")


# Run the main function only in the main process
if __name__ == "__main__":
    main()

