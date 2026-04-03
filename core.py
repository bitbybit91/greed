import logging
import os, sys
import signal
import threading

import sqlalchemy
import sqlalchemy.ext.declarative as sed
import telegram

import bot_manager
import crypto_swap
import database
import duckbot
import localization
import nuconfig
import worker

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

    # Optionally initialize the crypto swap engine
    swap_engine = None
    crypto_cfg = user_cfg.data.get("CryptoSwap")
    if crypto_cfg and crypto_cfg.get("enabled", False):
        log.info("CryptoSwap is enabled — initializing swap engine.")
        try:
            swap_engine = crypto_swap.SwapEngine(user_cfg, engine)
            log.info("Swap engine initialized successfully.")
        except Exception as exc:
            log.error(f"Failed to initialize swap engine: {exc}. Swap features will be disabled.")
            swap_engine = None

    # Build and start bots via BotManager
    manager = bot_manager.BotManager(user_cfg, engine, swap_engine=swap_engine)
    manager.build_from_config()

    # Validate that at least one bot was configured
    if not manager.instances():
        log.fatal("No bot instances could be configured. Check your token(s) in config.toml.")
        sys.exit(1)

    # Register graceful shutdown signal handlers
    shutdown_event = threading.Event()

    def _shutdown(signum, frame):
        sig_name = signal.Signals(signum).name
        log.info(f"Received {sig_name} — shutting down gracefully...")
        manager.stop_all()
        shutdown_event.set()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Start all bot polling threads
    manager.start_all()

    log.info(f"All {len(manager.instances())} bot(s) started. Waiting for shutdown signal.")

    # Block the main thread until shutdown is requested
    shutdown_event.wait()
    log.info("Shutdown complete.")


# Run the main function only in the main process
if __name__ == "__main__":
    main()
