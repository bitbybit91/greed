"""
shop_mode.py
============
Standard shop flow: product catalogue → cart → crypto checkout → shipping follow-up.
Entry point: run_shop_mode(worker_instance)
"""
import logging
import datetime
import re
from typing import Optional

import telegram

log = logging.getLogger(__name__)


def run_shop_mode(w) -> None:
    """Main user-menu loop for SHOP_BOT mode."""
    import database as db
    from worker import CancelSignal

    while True:
        coins = list(w._get_crypto_manager().get_available_coins().keys())
        crypto_label = "💳 Top-up with Crypto" if coins else "💳 Crypto Top-up (N/A)"

        keyboard = [
            [telegram.KeyboardButton(w.loc.get("menu_order"))],
            [telegram.KeyboardButton(w.loc.get("menu_order_status"))],
            [telegram.KeyboardButton(crypto_label)],
            [telegram.KeyboardButton(w.loc.get("menu_language"))],
            [
                telegram.KeyboardButton(w.loc.get("menu_help")),
                telegram.KeyboardButton(w.loc.get("menu_bot_info")),
            ],
        ]
        w.bot.send_message(
            w.chat.id,
            w.loc.get("conversation_open_user_menu", credit=w.Price(w.user.credit)),
            reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
        )

        valid = [
            w.loc.get("menu_order"),
            w.loc.get("menu_order_status"),
            crypto_label,
            w.loc.get("menu_language"),
            w.loc.get("menu_help"),
            w.loc.get("menu_bot_info"),
        ]
        selection = w._wait_for_message(valid)
        w.update_user()

        if selection == w.loc.get("menu_order"):
            w._order_menu()
        elif selection == w.loc.get("menu_order_status"):
            w._order_status()
        elif selection == crypto_label:
            if coins:
                w._add_credit_crypto()
            else:
                w.bot.send_message(
                    w.chat.id,
                    "⚠️ No crypto addresses configured yet. Please contact the owner."
                )
        elif selection == w.loc.get("menu_language"):
            w._language_menu()
        elif selection == w.loc.get("menu_bot_info"):
            w._bot_info()
        elif selection == w.loc.get("menu_help"):
            w._help_menu()
