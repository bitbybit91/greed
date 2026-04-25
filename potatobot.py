"""potatobot.py — Potato Chat DuckBot factory.

Equivalent of duckbot.py but targets the Potato Chat Bot API
(https://www.potatochat.com/api/bot/) instead of the Telegram Bot API.

Key differences from duckbot.py:
- telegram.Bot is constructed with an overridden base_url pointing to the
  Potato Chat API endpoint.
- send_invoice() and answer_pre_checkout_query() are no-ops (Potato Chat
  does not support Telegram Payments).
- send_chat_action() is a no-op (not meaningful on Potato Chat).
- Config keys are read from cfg["PotatoChat"] instead of cfg["Telegram"].
- factory_with_token() also accepts an explicit base_url parameter.
"""

import logging
import sys
import time
import traceback

import telegram
import telegram.error
import telegram.utils.request

import nuconfig

log = logging.getLogger(__name__)


def factory(cfg: nuconfig.NuConfig):
    """Construct a PotatoBot type based on the passed config.

    Reads token and API settings from cfg["PotatoChat"].
    """

    def catch_telegram_errors(func):
        """Decorator: retry on transient Telegram/network errors."""

        def result_func(*args, **kwargs):
            while True:
                try:
                    return func(*args, **kwargs)
                # Bot was blocked by the user
                except telegram.error.Unauthorized:
                    log.debug(f"Unauthorized to call {func.__name__}(), skipping.")
                    return None
                # API didn't answer in time
                except telegram.error.TimedOut:
                    log.warning(
                        f"Timed out while calling {func.__name__}(),"
                        f" retrying in {cfg['PotatoChat']['timed_out_pause']} secs..."
                    )
                    time.sleep(cfg["PotatoChat"]["timed_out_pause"])
                    continue
                # Network unreachable
                except telegram.error.NetworkError as error:
                    log.error(
                        f"Network error while calling {func.__name__}(),"
                        f" retrying in {cfg['PotatoChat']['error_pause']} secs...\n"
                        f"Full error: {error.message}"
                    )
                    time.sleep(cfg["PotatoChat"]["error_pause"])
                    continue
                # Generic Telegram/API error
                except telegram.error.TelegramError as error:
                    if error.message.lower() in ["bad gateway", "invalid server response"]:
                        log.warning(
                            f"Bad Gateway while calling {func.__name__}(),"
                            f" retrying in {cfg['PotatoChat']['error_pause']} secs..."
                        )
                        time.sleep(cfg["PotatoChat"]["error_pause"])
                        continue
                    elif error.message.lower() == "timed out":
                        log.warning(
                            f"Timed out while calling {func.__name__}(),"
                            f" retrying in {cfg['PotatoChat']['timed_out_pause']} secs..."
                        )
                        time.sleep(cfg["PotatoChat"]["timed_out_pause"])
                        continue
                    else:
                        log.error(
                            f"Telegram error while calling {func.__name__}(),"
                            f" retrying in {cfg['PotatoChat']['error_pause']} secs...\n"
                            f"Full error: {error.message}"
                        )
                        traceback.print_exception(*sys.exc_info())
                        time.sleep(cfg["PotatoChat"]["error_pause"])
                        continue

        return result_func

    class PotatoBot:
        def __init__(self, *args, **kwargs):
            base_url = cfg["PotatoChat"]["api_base_url"]
            token = cfg["PotatoChat"]["token"]
            self.bot = telegram.Bot(token=token, base_url=base_url, *args, **kwargs)

        @catch_telegram_errors
        def send_message(self, *args, **kwargs):
            # All messages are sent in HTML parse mode
            return self.bot.send_message(parse_mode="HTML", *args, **kwargs)

        @catch_telegram_errors
        def send_photo(self, *args, **kwargs):
            return self.bot.send_photo(parse_mode="HTML", *args, **kwargs)

        @catch_telegram_errors
        def edit_message_text(self, *args, **kwargs):
            # All messages are sent in HTML parse mode
            return self.bot.edit_message_text(parse_mode="HTML", *args, **kwargs)

        @catch_telegram_errors
        def edit_message_caption(self, *args, **kwargs):
            # All messages are sent in HTML parse mode
            return self.bot.edit_message_caption(parse_mode="HTML", *args, **kwargs)

        @catch_telegram_errors
        def edit_message_reply_markup(self, *args, **kwargs):
            return self.bot.edit_message_reply_markup(*args, **kwargs)

        @catch_telegram_errors
        def get_updates(self, *args, **kwargs):
            return self.bot.get_updates(*args, **kwargs)

        @catch_telegram_errors
        def get_me(self, *args, **kwargs):
            return self.bot.get_me(*args, **kwargs)

        @catch_telegram_errors
        def answer_callback_query(self, *args, **kwargs):
            return self.bot.answer_callback_query(*args, **kwargs)

        def answer_pre_checkout_query(self, *args, **kwargs):
            """No-op: Potato Chat does not support Telegram Payments."""
            log.warning("answer_pre_checkout_query() called but is not supported on Potato Chat — ignoring.")
            return None

        def send_invoice(self, *args, **kwargs):
            """No-op: Potato Chat does not support Telegram Payments (sendInvoice)."""
            log.warning("send_invoice() called but is not supported on Potato Chat — ignoring.")
            return None

        @catch_telegram_errors
        def get_file(self, *args, **kwargs):
            return self.bot.get_file(*args, **kwargs)

        def send_chat_action(self, *args, **kwargs):
            """No-op: send_chat_action is not meaningful on Potato Chat."""
            return None

        @catch_telegram_errors
        def delete_message(self, *args, **kwargs):
            return self.bot.delete_message(*args, **kwargs)

        @catch_telegram_errors
        def send_document(self, *args, **kwargs):
            return self.bot.send_document(*args, **kwargs)

        # More methods can be added here

    return PotatoBot


def factory_with_token(cfg: nuconfig.NuConfig, token: str, base_url: str):
    """Construct a PotatoBot type using an explicit token and base_url.

    Useful for testing or when the token / URL differ from the config values.
    Retry timing is still read from cfg["PotatoChat"].
    """

    def catch_telegram_errors(func):
        """Decorator: retry on transient Telegram/network errors."""

        def result_func(*args, **kwargs):
            while True:
                try:
                    return func(*args, **kwargs)
                except telegram.error.Unauthorized:
                    log.debug(f"Unauthorized to call {func.__name__}(), skipping.")
                    return None
                except telegram.error.TimedOut:
                    log.warning(
                        f"Timed out while calling {func.__name__}(),"
                        f" retrying in {cfg['PotatoChat']['timed_out_pause']} secs..."
                    )
                    time.sleep(cfg["PotatoChat"]["timed_out_pause"])
                    continue
                except telegram.error.NetworkError as error:
                    log.error(
                        f"Network error while calling {func.__name__}(),"
                        f" retrying in {cfg['PotatoChat']['error_pause']} secs...\n"
                        f"Full error: {error.message}"
                    )
                    time.sleep(cfg["PotatoChat"]["error_pause"])
                    continue
                except telegram.error.TelegramError as error:
                    if error.message.lower() in ["bad gateway", "invalid server response"]:
                        log.warning(
                            f"Bad Gateway while calling {func.__name__}(),"
                            f" retrying in {cfg['PotatoChat']['error_pause']} secs..."
                        )
                        time.sleep(cfg["PotatoChat"]["error_pause"])
                        continue
                    elif error.message.lower() == "timed out":
                        log.warning(
                            f"Timed out while calling {func.__name__}(),"
                            f" retrying in {cfg['PotatoChat']['timed_out_pause']} secs..."
                        )
                        time.sleep(cfg["PotatoChat"]["timed_out_pause"])
                        continue
                    else:
                        log.error(
                            f"Telegram error while calling {func.__name__}(),"
                            f" retrying in {cfg['PotatoChat']['error_pause']} secs...\n"
                            f"Full error: {error.message}"
                        )
                        traceback.print_exception(*sys.exc_info())
                        time.sleep(cfg["PotatoChat"]["error_pause"])
                        continue

        return result_func

    class PotatoBot:
        def __init__(self, *args, **kwargs):
            self.bot = telegram.Bot(token=token, base_url=base_url, *args, **kwargs)

        @catch_telegram_errors
        def send_message(self, *args, **kwargs):
            return self.bot.send_message(parse_mode="HTML", *args, **kwargs)

        @catch_telegram_errors
        def send_photo(self, *args, **kwargs):
            return self.bot.send_photo(parse_mode="HTML", *args, **kwargs)

        @catch_telegram_errors
        def edit_message_text(self, *args, **kwargs):
            return self.bot.edit_message_text(parse_mode="HTML", *args, **kwargs)

        @catch_telegram_errors
        def edit_message_caption(self, *args, **kwargs):
            return self.bot.edit_message_caption(parse_mode="HTML", *args, **kwargs)

        @catch_telegram_errors
        def edit_message_reply_markup(self, *args, **kwargs):
            return self.bot.edit_message_reply_markup(*args, **kwargs)

        @catch_telegram_errors
        def get_updates(self, *args, **kwargs):
            return self.bot.get_updates(*args, **kwargs)

        @catch_telegram_errors
        def get_me(self, *args, **kwargs):
            return self.bot.get_me(*args, **kwargs)

        @catch_telegram_errors
        def answer_callback_query(self, *args, **kwargs):
            return self.bot.answer_callback_query(*args, **kwargs)

        def answer_pre_checkout_query(self, *args, **kwargs):
            """No-op: Potato Chat does not support Telegram Payments."""
            log.warning("answer_pre_checkout_query() called but is not supported on Potato Chat — ignoring.")
            return None

        def send_invoice(self, *args, **kwargs):
            """No-op: Potato Chat does not support Telegram Payments (sendInvoice)."""
            log.warning("send_invoice() called but is not supported on Potato Chat — ignoring.")
            return None

        @catch_telegram_errors
        def get_file(self, *args, **kwargs):
            return self.bot.get_file(*args, **kwargs)

        def send_chat_action(self, *args, **kwargs):
            """No-op: send_chat_action is not meaningful on Potato Chat."""
            return None

        @catch_telegram_errors
        def delete_message(self, *args, **kwargs):
            return self.bot.delete_message(*args, **kwargs)

        @catch_telegram_errors
        def send_document(self, *args, **kwargs):
            return self.bot.send_document(*args, **kwargs)

    return PotatoBot
