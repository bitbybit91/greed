import collections
import logging
import sys
import threading
import time
import traceback

import telegram.error

import nuconfig

log = logging.getLogger(__name__)


def _make_duckbot_class(cfg: nuconfig.NuConfig, token: str):
    """Internal factory that creates a DuckBot class bound to *cfg* and *token*."""

    # ------------------------------------------------------------------ #
    # Rate-limit state (per DuckBot class — shared between instances of   #
    # the same class, but independent between different factories).        #
    # ------------------------------------------------------------------ #
    _global_lock = threading.Lock()
    # Global: max 30 messages/second across all chats
    _global_timestamps: collections.deque = collections.deque()
    _GLOBAL_MAX = 30
    _GLOBAL_WINDOW = 1.0  # seconds

    # Per-chat: max 1 message/second
    _chat_timestamps: dict = {}

    def _rate_limit(chat_id=None):
        """Block until both the global and per-chat rate limits allow a call."""
        with _global_lock:
            # --- global limit ---
            now = time.monotonic()
            # Remove entries older than the sliding window
            while _global_timestamps and now - _global_timestamps[0] > _GLOBAL_WINDOW:
                _global_timestamps.popleft()
            if len(_global_timestamps) >= _GLOBAL_MAX:
                sleep_time = _GLOBAL_WINDOW - (now - _global_timestamps[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
            _global_timestamps.append(time.monotonic())

            # --- per-chat limit ---
            if chat_id is not None:
                now_chat = time.monotonic()
                last_sent = _chat_timestamps.get(chat_id, 0)
                if now_chat - last_sent < 1.0:
                    time.sleep(1.0 - (now_chat - last_sent))
                _chat_timestamps[chat_id] = time.monotonic()

    def catch_telegram_errors(func):
        """Decorator: retry on transient Telegram errors; skip on Unauthorized."""

        def result_func(*args, **kwargs):
            while True:
                try:
                    return func(*args, **kwargs)
                except telegram.error.Unauthorized:
                    log.debug(f"Unauthorized to call {func.__name__}(), skipping.")
                    return None
                except telegram.error.TimedOut:
                    pause = cfg["Telegram"]["timed_out_pause"]
                    log.warning(
                        f"Timed out while calling {func.__name__}(),"
                        f" retrying in {pause} secs..."
                    )
                    time.sleep(pause)
                    continue
                except telegram.error.NetworkError as error:
                    pause = cfg["Telegram"]["error_pause"]
                    log.error(
                        f"Network error while calling {func.__name__}(),"
                        f" retrying in {pause} secs...\n"
                        f"Full error: {error.message}"
                    )
                    time.sleep(pause)
                    continue
                except telegram.error.TelegramError as error:
                    if error.message.lower() in ["bad gateway", "invalid server response"]:
                        pause = cfg["Telegram"]["error_pause"]
                        log.warning(
                            f"Bad Gateway while calling {func.__name__}(),"
                            f" retrying in {pause} secs..."
                        )
                        time.sleep(pause)
                        continue
                    elif error.message.lower() == "timed out":
                        pause = cfg["Telegram"]["timed_out_pause"]
                        log.warning(
                            f"Timed out while calling {func.__name__}(),"
                            f" retrying in {pause} secs..."
                        )
                        time.sleep(pause)
                        continue
                    else:
                        pause = cfg["Telegram"]["error_pause"]
                        log.error(
                            f"Telegram error while calling {func.__name__}(),"
                            f" retrying in {pause} secs...\n"
                            f"Full error: {error.message}"
                        )
                        traceback.print_exception(*sys.exc_info())
                        time.sleep(pause)
                        continue

        return result_func

    class DuckBot:
        def __init__(self, *args, **kwargs):
            self.bot = telegram.Bot(token=token, *args, **kwargs)

        # ------------------------------------------------------------------ #
        # Message sending methods (rate-limited)                               #
        # ------------------------------------------------------------------ #

        @catch_telegram_errors
        def send_message(self, chat_id, *args, **kwargs):
            _rate_limit(chat_id)
            return self.bot.send_message(chat_id, parse_mode="HTML", *args, **kwargs)

        @catch_telegram_errors
        def send_photo(self, chat_id, *args, **kwargs):
            _rate_limit(chat_id)
            return self.bot.send_photo(chat_id, parse_mode="HTML", *args, **kwargs)

        @catch_telegram_errors
        def send_document(self, chat_id, *args, **kwargs):
            _rate_limit(chat_id)
            return self.bot.send_document(chat_id, *args, **kwargs)

        @catch_telegram_errors
        def send_invoice(self, chat_id, *args, **kwargs):
            _rate_limit(chat_id)
            return self.bot.send_invoice(chat_id, *args, **kwargs)

        @catch_telegram_errors
        def send_chat_action(self, chat_id, *args, **kwargs):
            _rate_limit(chat_id)
            return self.bot.send_chat_action(chat_id, *args, **kwargs)

        @catch_telegram_errors
        def send_sticker(self, chat_id, *args, **kwargs):
            _rate_limit(chat_id)
            return self.bot.send_sticker(chat_id, *args, **kwargs)

        @catch_telegram_errors
        def pin_chat_message(self, chat_id, *args, **kwargs):
            _rate_limit(chat_id)
            return self.bot.pin_chat_message(chat_id, *args, **kwargs)

        # ------------------------------------------------------------------ #
        # Edit / delete methods                                                #
        # ------------------------------------------------------------------ #

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
        def delete_message(self, *args, **kwargs):
            return self.bot.delete_message(*args, **kwargs)

        # ------------------------------------------------------------------ #
        # Query / polling methods                                              #
        # ------------------------------------------------------------------ #

        @catch_telegram_errors
        def get_updates(self, *args, **kwargs):
            return self.bot.get_updates(*args, **kwargs)

        @catch_telegram_errors
        def get_me(self, *args, **kwargs):
            return self.bot.get_me(*args, **kwargs)

        @catch_telegram_errors
        def answer_callback_query(self, *args, **kwargs):
            return self.bot.answer_callback_query(*args, **kwargs)

        @catch_telegram_errors
        def answer_pre_checkout_query(self, *args, **kwargs):
            return self.bot.answer_pre_checkout_query(*args, **kwargs)

        @catch_telegram_errors
        def get_file(self, *args, **kwargs):
            return self.bot.get_file(*args, **kwargs)

    return DuckBot


def factory(cfg: nuconfig.NuConfig):
    """Construct a DuckBot type using the token from *cfg*[Telegram][token].

    This is the original single-bot factory kept for backward compatibility.
    """
    token = cfg["Telegram"]["token"]
    return _make_duckbot_class(cfg, token)


def factory_with_token(cfg: nuconfig.NuConfig, token: str):
    """Construct a DuckBot type using an explicit *token*.

    Use this factory when managing multiple bots, each with their own token.
    """
    return _make_duckbot_class(cfg, token)
