#!/usr/bin/env python3
"""
fix_worker.py — Standalone patch script for worker.py.

Run as:  python3 fix_worker.py

Applies three bug-fixes to worker.py in place:
  1. Dynamic __wait_for_specific_message list in __user_menu (mode-aware).
  2. Owner buttons added to __wait_for_specific_message in __admin_menu
     plus the missing elif handlers.
  3. Injects missing methods (_crypto_manager, __add_credit_crypto,
     __admin_mode_panel, __admin_reload_crypto, __admin_woo_import)
     before __bot_info.

Idempotency: A marker comment "# GREED_WORKER_FIXED" is written at the
top of the file on first run.  Subsequent runs detect it and exit early.
"""

import re
import shutil
import sys
from pathlib import Path

WORKER_PATH = Path(__file__).parent / "worker.py"
BACKUP_PATH = Path(__file__).parent / "worker.py.bak2"
FIXED_MARKER = "# GREED_WORKER_FIXED\n"

# ---------------------------------------------------------------------------
# Patch 1 – dynamic __wait_for_specific_message in __user_menu
# ---------------------------------------------------------------------------
_OLD_USER_MENU_WAIT = """\
            # Wait for a reply from the user
            selection = self.__wait_for_specific_message([
                self.loc.get("menu_order"),
                self.loc.get("menu_order_status"),
                self.loc.get("menu_add_credit"),
                self.loc.get("menu_language"),
                self.loc.get("menu_help"),
                self.loc.get("menu_bot_info"),
            ])"""

_NEW_USER_MENU_WAIT = """\
            # Wait for a reply from the user
            # Build accepted messages based on active mode
            _accepted = []
            if _active_mode == "SHOP_BOT":
                _accepted += [self.loc.get("menu_order"), self.loc.get("menu_order_status")]
            elif _active_mode == "INVESTMENT_BOT":
                _accepted.append("\\U0001f4bc Investment Portal")
            elif _active_mode == "SWAP_BOT":
                _accepted.append("\\U0001f504 Swap Crypto")
            _accepted += [
                self.loc.get("menu_add_credit"),
                self.loc.get("menu_language"),
                self.loc.get("menu_help"),
                self.loc.get("menu_bot_info"),
            ]
            selection = self.__wait_for_specific_message(_accepted)"""

# ---------------------------------------------------------------------------
# Patch 2 – owner buttons in __admin_menu wait + missing elif handlers
# ---------------------------------------------------------------------------
_OLD_ADMIN_MENU_WAIT = """\
            # Wait for a reply from the user
            selection = self.__wait_for_specific_message([self.loc.get("menu_products"),
                                                          self.loc.get("menu_orders"),
                                                          self.loc.get("menu_user_mode"),
                                                          self.loc.get("menu_edit_credit"),
                                                          self.loc.get("menu_transactions"),
                                                          self.loc.get("menu_csv"),
                                                          self.loc.get("menu_edit_admins")])"""

_NEW_ADMIN_MENU_WAIT = """\
            # Wait for a reply from the user
            selection = self.__wait_for_specific_message([self.loc.get("menu_products"),
                                                          self.loc.get("menu_orders"),
                                                          self.loc.get("menu_user_mode"),
                                                          self.loc.get("menu_edit_credit"),
                                                          self.loc.get("menu_transactions"),
                                                          self.loc.get("menu_csv"),
                                                          self.loc.get("menu_edit_admins"),
                                                          "\\U0001f916 Bot Mode",
                                                          "\\U0001f4b0 Crypto Addresses",
                                                          "\\U0001f4e6 Import Products (WooCommerce)"])"""

_OLD_ADMIN_MENU_ELIF = """\
            # If the user has selected the .csv option and has the privileges to perform the action...
            elif selection == self.loc.get("menu_csv") and self.admin.create_transactions:
                # Generate the .csv file
                self.__transactions_file()

    def __products_menu(self):"""

_NEW_ADMIN_MENU_ELIF = """\
            # If the user has selected the .csv option and has the privileges to perform the action...
            elif selection == self.loc.get("menu_csv") and self.admin.create_transactions:
                # Generate the .csv file
                self.__transactions_file()
            elif selection == "\\U0001f916 Bot Mode" and self.admin.is_owner:
                self.__admin_mode_panel()
            elif selection == "\\U0001f4b0 Crypto Addresses" and self.admin.is_owner:
                self.__admin_reload_crypto()
            elif selection == "\\U0001f4e6 Import Products (WooCommerce)" and self.admin.is_owner:
                self.__admin_woo_import()

    def __products_menu(self):"""

# ---------------------------------------------------------------------------
# Patch 3 – inject missing methods before __bot_info
# ---------------------------------------------------------------------------
_NEW_METHODS = '''\
    # ── Crypto Manager (lazily initialised) ─────────────────────────────────
    def _crypto_manager(self):
        """Return the shared CryptoPaymentManager instance."""
        if self._crypto_mgr is None:
            try:
                from crypto_manager import CryptoPaymentManager
                self._crypto_mgr = CryptoPaymentManager()
            except ImportError:
                log.error("crypto_manager module not found.")
                self._crypto_mgr = None
        return self._crypto_mgr

    # ── Crypto Credit Top-Up ─────────────────────────────────────────────────
    def __add_credit_crypto(self):
        """Add wallet credit via a cryptocurrency deposit."""
        log.debug("Displaying __add_credit_crypto")
        mgr = self._crypto_manager()
        if not mgr:
            self.bot.send_message(
                self.chat.id,
                "\\u26a0\\ufe0f Crypto payment is not configured. Contact the owner.",
            )
            return
        coins = mgr.get_available_coins()
        if not coins:
            self.bot.send_message(
                self.chat.id,
                "\\u26a0\\ufe0f No deposit addresses configured yet.",
            )
            return
        cancel = telegram.InlineKeyboardMarkup(
            [[telegram.InlineKeyboardButton(self.loc.get("menu_cancel"),
                                            callback_data="cmd_cancel")]]
        )
        self.bot.send_message(
            self.chat.id,
            "\\U0001f4b0 How much would you like to add to your wallet?\\n"
            f"Enter amount in {self.cfg[\'Payments\'][\'currency\']} "
            f"(e.g. <code>20.00</code>):",
            parse_mode="HTML",
            reply_markup=cancel,
        )
        amount_str = self.__wait_for_regex(
            r"([0-9]+(?:[.,][0-9]{1,2})?)", cancellable=True)
        if isinstance(amount_str, CancelSignal):
            return
        amount_price = self.Price(amount_str)
        fiat_cents = int(amount_price)

        keyboard = [[telegram.KeyboardButton(c)] for c in coins]
        keyboard.append([telegram.KeyboardButton(self.loc.get("menu_cancel"))])
        self.bot.send_message(
            self.chat.id,
            "Select cryptocurrency:",
            reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
        )
        coin = self.__wait_for_specific_message(coins, cancellable=True)
        if isinstance(coin, CancelSignal):
            return

        info = mgr.get_payment_info(
            fiat_cents=fiat_cents,
            coin=coin,
            currency_exp=self.cfg["Payments"]["currency_exp"],
            fiat=self.cfg["Payments"]["currency"].lower(),
            currency_symbol=self.cfg["Payments"].get("currency_symbol", "\\u20ac"),
        )
        if not info:
            self.bot.send_message(
                self.chat.id,
                f"\\u274c Could not get rate for {coin}.",
            )
            return

        self.bot.send_message(
            self.chat.id,
            "\\U0001f4cb <b>Payment Details</b>\\n\\n" + info["display"],
            parse_mode="HTML",
            reply_markup=telegram.ReplyKeyboardRemove(),
        )
        self.bot.send_message(
            self.chat.id,
            "\\u23f3 After sending, please type your transaction ID below "
            "or press Cancel:",
            reply_markup=telegram.InlineKeyboardMarkup(
                [[telegram.InlineKeyboardButton(self.loc.get("menu_cancel"),
                                                callback_data="cmd_cancel")]]
            ),
        )
        tx_id = self.__wait_for_regex(r"(.+)", cancellable=True)
        if isinstance(tx_id, CancelSignal):
            return
        transaction = db.Transaction(
            user=self.user,
            value=0,
            provider=f"Crypto:{info[\'coin\']}",
            notes=(
                f"PENDING | {info[\'coin\']} {info[\'amount\']} | "
                f"addr:{info[\'address\']} | tx:{str(tx_id).strip()}"
            ),
        )
        self.session.add(transaction)
        self.session.commit()
        self.bot.send_message(
            self.chat.id,
            "\\u2705 Payment submitted for review. The owner will confirm "
            "and credit your wallet shortly.",
        )
        admins = (
            self.session.query(db.Admin)
            .filter_by(receive_orders=True)
            .all()
        )
        for admin in admins:
            try:
                self.bot.send_message(
                    admin.user_id,
                    f"\\U0001f4b0 <b>Pending Crypto Top-Up</b>\\n"
                    f"User: {self.user.mention()} ({self.user.user_id})\\n"
                    f"Amount: {self.Price(fiat_cents)}\\n"
                    f"Coin: {info[\'coin\']} {info[\'amount\']}\\n"
                    f"TX: {str(tx_id).strip()}\\n"
                    f"Transaction #{transaction.transaction_id}: "
                    f"use /edit_credit to confirm.",
                    parse_mode="HTML",
                )
            except Exception:
                pass

    # ── Admin: Mode Panel ────────────────────────────────────────────────────
    def __admin_mode_panel(self):
        """Let the owner switch the active bot mode."""
        log.debug("Displaying __admin_mode_panel")
        try:
            import modes as _modes
        except ImportError:
            self.bot.send_message(self.chat.id, "modes package not found.")
            return
        current = _modes.get_active_mode()
        keyboard = telegram.ReplyKeyboardMarkup(
            [
                [telegram.KeyboardButton("\\U0001f6cd SHOP_BOT")],
                [telegram.KeyboardButton("\\U0001f4c8 INVESTMENT_BOT")],
                [telegram.KeyboardButton("\\U0001f504 SWAP_BOT")],
                [telegram.KeyboardButton(self.loc.get("menu_cancel"))],
            ],
            one_time_keyboard=True,
        )
        self.bot.send_message(
            self.chat.id,
            f"\\U0001f916 <b>Bot Mode</b>\\nCurrent: <b>{current}</b>\\n\\n"
            "Select new mode:",
            parse_mode="HTML",
            reply_markup=keyboard,
        )
        modes_list = ["\\U0001f6cd SHOP_BOT", "\\U0001f4c8 INVESTMENT_BOT",
                      "\\U0001f504 SWAP_BOT"]
        sel = self.__wait_for_specific_message(modes_list, cancellable=True)
        if isinstance(sel, CancelSignal):
            return
        new_mode = sel.split()[-1]
        _modes.set_active_mode(new_mode)
        self.bot.send_message(
            self.chat.id,
            f"\\u2705 Bot mode switched to <b>{new_mode}</b>",
            parse_mode="HTML",
        )

    # ── Admin: Reload Crypto Addresses ───────────────────────────────────────
    def __admin_reload_crypto(self):
        """Reload crypto deposit addresses from config file."""
        mgr = self._crypto_manager()
        if mgr:
            mgr.load_addresses()
            self.bot.send_message(
                self.chat.id,
                f"\\u2705 Crypto addresses reloaded: "
                f"{mgr.get_available_coins()}",
            )
        else:
            self.bot.send_message(self.chat.id, "\\u274c Crypto manager unavailable.")

    # ── Admin: WooCommerce XML Import ─────────────────────────────────────────
    def __admin_woo_import(self):
        """Trigger a WooCommerce XML product import."""
        self.bot.send_message(
            self.chat.id,
            "\\U0001f4e6 Enter path to WooCommerce XML file:",
            reply_markup=telegram.InlineKeyboardMarkup(
                [[telegram.InlineKeyboardButton(self.loc.get("menu_cancel"),
                                                callback_data="cmd_cancel")]]
            ),
        )
        path_raw = self.__wait_for_regex(r"(.+)", cancellable=True)
        if isinstance(path_raw, CancelSignal):
            return
        xml_path = str(path_raw).strip()
        try:
            from woo_importer import WooCommerceXMLImporter
            importer = WooCommerceXMLImporter(self.session, xml_path=xml_path)
            n = importer.import_products()
            self.bot.send_message(
                self.chat.id,
                f"\\u2705 WooCommerce import done: {n} products processed.",
            )
        except Exception as exc:
            self.bot.send_message(
                self.chat.id,
                f"\\u274c Import failed: {exc}",
            )

    def __bot_info(self):'''

_BOT_INFO_ANCHOR = "    def __bot_info(self):"

# ---------------------------------------------------------------------------


def _apply_patch(source: str, old: str, new: str, label: str) -> tuple[str, bool]:
    """Replace *old* with *new* in *source*.  Returns (result, changed)."""
    if old not in source:
        return source, False
    result = source.replace(old, new, 1)
    print(f"  ✔  {label}")
    return result, True


def main() -> int:
    if not WORKER_PATH.exists():
        print(f"ERROR: {WORKER_PATH} not found.", file=sys.stderr)
        return 1

    source = WORKER_PATH.read_text(encoding="utf-8")

    # Idempotency guard
    if FIXED_MARKER.rstrip() in source:
        print("worker.py has already been patched — nothing to do.")
        return 0

    print(f"Backing up original to {BACKUP_PATH} …")
    shutil.copy2(WORKER_PATH, BACKUP_PATH)

    changed_any = False

    # --- Patch 1 ---
    source, ok = _apply_patch(
        source, _OLD_USER_MENU_WAIT, _NEW_USER_MENU_WAIT,
        "Bug 1: dynamic __wait_for_specific_message in __user_menu",
    )
    changed_any = changed_any or ok
    if not ok:
        print("  ⚠  Bug 1 pattern not found — already patched or source differs.")

    # --- Patch 2a: wait list ---
    source, ok = _apply_patch(
        source, _OLD_ADMIN_MENU_WAIT, _NEW_ADMIN_MENU_WAIT,
        "Bug 2a: owner buttons in __admin_menu wait list",
    )
    changed_any = changed_any or ok
    if not ok:
        print("  ⚠  Bug 2a pattern not found — already patched or source differs.")

    # --- Patch 2b: elif handlers ---
    source, ok = _apply_patch(
        source, _OLD_ADMIN_MENU_ELIF, _NEW_ADMIN_MENU_ELIF,
        "Bug 2b: missing elif handlers in __admin_menu",
    )
    changed_any = changed_any or ok
    if not ok:
        print("  ⚠  Bug 2b pattern not found — already patched or source differs.")

    # --- Patch 3: inject methods before __bot_info ---
    if _BOT_INFO_ANCHOR in source:
        # Only inject if the methods aren't already present
        if "def _crypto_manager(" not in source:
            source = source.replace(_BOT_INFO_ANCHOR, _NEW_METHODS, 1)
            print("  ✔  Bug 3: injected missing methods before __bot_info")
            changed_any = True
        else:
            print("  ⚠  Bug 3: methods already present — skipping injection.")
    else:
        print("  ⚠  Bug 3: __bot_info anchor not found — skipping injection.")

    if not changed_any:
        print("No changes were needed; worker.py appears to already be patched.")
        return 0

    # Prepend marker
    source = FIXED_MARKER + source

    WORKER_PATH.write_text(source, encoding="utf-8")
    print(f"\n✅  worker.py successfully patched.  Backup saved as {BACKUP_PATH}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
