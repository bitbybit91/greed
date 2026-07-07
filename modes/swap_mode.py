"""
modes/swap_mode.py
Swap Mode — user selects coin-in / coin-out, gets live CoinGecko rate quote,
deposits to payout flow with owner-set spread %.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import worker as _w

log = logging.getLogger(__name__)


def run_swap_menu(w: "_w.Worker") -> None:
    """Main swap mode entry point."""
    import telegram
    import toml
    from crypto_manager import CryptoPaymentManager

    mgr: CryptoPaymentManager = w._crypto_manager()
    coins = mgr.get_available_coins()
    if len(coins) < 2:
        w.bot.send_message(w.chat.id,
                           "Swap requires at least 2 configured coin addresses.")
        return

    # Read owner spread from config/mode_config.toml
    spread_pct = 1.5
    try:
        cfg = toml.load("config/mode_config.toml")
        spread_pct = float(cfg.get("swap_spread_pct", 1.5))
    except Exception:
        pass

    # Coin-in selection
    kb_in = [[telegram.KeyboardButton(c)] for c in coins]
    kb_in.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(
        w.chat.id,
        "\U0001f504 <b>Crypto Swap</b>\n\nSelect coin to <b>send</b> (coin-in):",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardMarkup(kb_in, one_time_keyboard=True),
    )
    coin_in = w._Worker__wait_for_specific_message(coins, cancellable=True)
    if hasattr(coin_in, "__class__") and coin_in.__class__.__name__ == "CancelSignal":
        return

    # Coin-out selection (exclude coin-in)
    out_coins = [c for c in coins if c != coin_in]
    kb_out = [[telegram.KeyboardButton(c)] for c in out_coins]
    kb_out.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(
        w.chat.id,
        f"Select coin to <b>receive</b> (coin-out):",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardMarkup(kb_out, one_time_keyboard=True),
    )
    coin_out = w._Worker__wait_for_specific_message(out_coins, cancellable=True)
    if hasattr(coin_out, "__class__") and coin_out.__class__.__name__ == "CancelSignal":
        return

    # Amount to send
    w.bot.send_message(
        w.chat.id,
        f"How much <b>{coin_in}</b> do you want to swap?\n"
        f"Enter amount (e.g. <code>0.05</code>):",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )
    amount_str = w._Worker__wait_for_regex(r"([0-9]+(?:[.,][0-9]+)?)", cancellable=True)
    if hasattr(amount_str, "__class__") and amount_str.__class__.__name__ == "CancelSignal":
        return
    amount_in = float(str(amount_str).replace(",", "."))

    # Fetch rates and calculate
    fiat = w.cfg["Payments"]["currency"].lower()
    rate_in = mgr.get_live_rate(coin_in, fiat)
    rate_out = mgr.get_live_rate(coin_out, fiat)
    if not rate_in or not rate_out:
        w.bot.send_message(w.chat.id, "\u274c Could not fetch live rates. Try again later.")
        return

    fiat_val = amount_in * rate_in
    amount_out_gross = fiat_val / rate_out
    amount_out_net = round(amount_out_gross * (1 - spread_pct / 100), 8)
    cs = w.cfg["Payments"].get("currency_symbol", "€")

    quote_msg = (
        f"\U0001f4cb <b>Swap Quote</b>\n\n"
        f"Send:    <code>{amount_in} {coin_in}</code> (≈ {cs}{fiat_val:.2f})\n"
        f"Receive: <code>{amount_out_net} {coin_out}</code>\n"
        f"Spread:  {spread_pct}%\n\n"
        f"Deposit address for <b>{coin_in}</b>:\n"
        f"<code>{mgr.addresses.get(coin_in.upper(), 'N/A')}</code>\n\n"
        f"After depositing, send your transaction ID below."
    )
    w.bot.send_message(w.chat.id, quote_msg, parse_mode="HTML")

    # Confirm or cancel
    confirm_kb = telegram.ReplyKeyboardMarkup(
        [["\u2705 Confirm Swap"], [w.loc.get("menu_cancel")]],
        one_time_keyboard=True,
    )
    w.bot.send_message(w.chat.id, "Proceed with this swap?", reply_markup=confirm_kb)
    confirm = w._Worker__wait_for_specific_message(
        ["\u2705 Confirm Swap"], cancellable=True)
    if hasattr(confirm, "__class__") and confirm.__class__.__name__ == "CancelSignal":
        return

    # Get TX ID
    w.bot.send_message(w.chat.id, "Enter your transaction ID / hash:",
                       reply_markup=telegram.ReplyKeyboardRemove())
    tx = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if hasattr(tx, "__class__") and tx.__class__.__name__ == "CancelSignal":
        tx = "not provided"

    w.bot.send_message(
        w.chat.id,
        f"\u23f3 Swap request submitted!\n"
        f"You will receive <b>{amount_out_net} {coin_out}</b> "
        f"to your wallet after the owner processes your deposit.",
        parse_mode="HTML",
    )

    # Notify admins
    import database as db
    admins = w.session.query(db.Admin).filter_by(receive_orders=True).all()
    swap_msg = (
        f"\U0001f504 <b>Swap Request</b>\n"
        f"User: {w.user.mention()} ({w.user.user_id})\n"
        f"Coin-in: {amount_in} {coin_in}\n"
        f"Coin-out: {amount_out_net} {coin_out}\n"
        f"TX ref: {str(tx).strip()}\n"
        f"Deposit address: {mgr.addresses.get(coin_in.upper(), 'N/A')}"
    )
    for admin in admins:
        try:
            w.bot.send_message(admin.user_id, swap_msg, parse_mode="HTML")
        except Exception as exc:
            log.warning(f"Could not notify admin {admin.user_id}: {exc}")
