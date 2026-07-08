"""
modes/swap_mode.py
Swap Mode — user selects coin-in / coin-out, gets live CoinGecko rate quote,
deposits to payout flow with owner-set spread %.
"""
from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import worker as _w

log = logging.getLogger(__name__)


def run_swap_menu(w: "_w.Worker") -> None:
    """Main swap mode entry point."""
    import telegram
    import database as db
    from worker import CancelSignal
    from crypto_manager import CryptoPaymentManager

    mgr: CryptoPaymentManager = w._crypto_manager()
    if mgr is None:
        w.bot.send_message(w.chat.id, "\u274c Crypto manager not available.")
        return
    coins = mgr.get_available_coins()
    if len(coins) < 2:
        w.bot.send_message(w.chat.id,
                           "Swap requires at least 2 configured coin addresses.")
        return

    # Read owner spread from config/mode_config.toml (with fallback)
    spread_pct = 1.5
    try:
        from modes import _load_toml
        cfg = _load_toml("config/mode_config.toml")
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
    if isinstance(coin_in, CancelSignal):
        return

    # Coin-out selection (exclude coin-in)
    out_coins = [c for c in coins if c != coin_in]
    kb_out = [[telegram.KeyboardButton(c)] for c in out_coins]
    kb_out.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(
        w.chat.id,
        "Select coin to <b>receive</b> (coin-out):",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardMarkup(kb_out, one_time_keyboard=True),
    )
    coin_out = w._Worker__wait_for_specific_message(out_coins, cancellable=True)
    if isinstance(coin_out, CancelSignal):
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
    if isinstance(amount_str, CancelSignal):
        return
    amount_in = float(str(amount_str).replace(",", "."))

    # Fetch rates and calculate
    fiat = w.cfg["Payments"]["currency"].lower()
    quote = mgr.get_swap_quote(coin_in, coin_out, amount_in, fiat=fiat,
                                spread_pct=spread_pct)
    if quote is None:
        w.bot.send_message(w.chat.id, "\u274c Could not fetch live rates. Try again later.")
        return

    cs = w.cfg["Payments"].get("currency_symbol", "€")
    deposit_address = mgr.addresses.get(coin_in.upper(), "N/A")
    quote_msg = (
        f"\U0001f4cb <b>Swap Quote</b>\n\n"
        f"Send:    <code>{amount_in} {coin_in}</code> (≈ {cs}{quote['fiat_value']:.2f})\n"
        f"Receive: <code>{quote['amount_out']} {coin_out}</code>\n"
        f"Spread:  {spread_pct}%\n\n"
        f"Deposit address for <b>{coin_in}</b>:\n"
        f"<code>{deposit_address}</code>\n\n"
        f"After depositing, send your transaction ID below."
    )
    w.bot.send_message(w.chat.id, quote_msg, parse_mode="HTML")

    # Confirm or cancel
    confirm_kb = telegram.ReplyKeyboardMarkup(
        [["\u2705 Confirm Swap"], [w.loc.get("menu_cancel")]],
        one_time_keyboard=True,
    )
    w.bot.send_message(w.chat.id, "Proceed with this swap?", reply_markup=confirm_kb)
    confirm = w._Worker__wait_for_specific_message(["\u2705 Confirm Swap"], cancellable=True)
    if isinstance(confirm, CancelSignal):
        return

    # Get TX ID
    w.bot.send_message(w.chat.id, "Enter your transaction ID / hash:",
                       reply_markup=telegram.ReplyKeyboardRemove())
    tx = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    tx_str = "not provided" if isinstance(tx, CancelSignal) else str(tx).strip()

    # Store SwapRequest in DB
    try:
        swap_rec = db.SwapRequest(
            user_id=w.user.user_id,
            coin_in=coin_in.upper(),
            coin_out=coin_out.upper(),
            amount_in=str(amount_in),
            amount_out=str(quote["amount_out"]),
            deposit_addr=deposit_address,
            tx_ref=tx_str,
            status="pending",
            created_at=datetime.datetime.now(),
        )
        w.session.add(swap_rec)
        w.session.commit()
    except Exception as exc:
        log.warning(f"Could not save SwapRequest: {exc}")
        w.session.rollback()

    w.bot.send_message(
        w.chat.id,
        f"\u23f3 Swap request submitted!\n"
        f"You will receive <b>{quote['amount_out']} {coin_out}</b> "
        f"to your wallet after the owner processes your deposit.",
        parse_mode="HTML",
    )

    # Notify admins
    admins = w.session.query(db.Admin).filter_by(receive_orders=True).all()
    swap_msg = (
        f"\U0001f504 <b>Swap Request</b>\n"
        f"User: {w.user.mention()} ({w.user.user_id})\n"
        f"Coin-in: {amount_in} {coin_in}\n"
        f"Coin-out: {quote['amount_out']} {coin_out}\n"
        f"TX ref: {tx_str}\n"
        f"Deposit address: {deposit_address}"
    )
    for admin in admins:
        try:
            w.bot.send_message(admin.user_id, swap_msg, parse_mode="HTML")
        except Exception as exc:
            log.warning(f"Could not notify admin {admin.user_id}: {exc}")
