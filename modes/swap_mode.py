from __future__ import annotations

import datetime
import logging
from html import escape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import worker as _w

log = logging.getLogger(__name__)


def _is_cancel(value) -> bool:
    from worker import CancelSignal

    return isinstance(value, CancelSignal)


def _load_spread_pct() -> float:
    try:
        import modes

        config = modes._read_mode_config()  # type: ignore[attr-defined]
        spread = float(config.get("swap_spread_pct", 1.5))
        return max(spread, 0.0)
    except Exception:
        return 1.5


def _notify_admins(w: "_w.Worker", message: str) -> None:
    import database as db

    admins = w.session.query(db.Admin).filter_by(receive_orders=True).all()
    for admin in admins:
        try:
            w.bot.send_message(admin.user_id, message, parse_mode="HTML")
        except Exception as exc:
            log.warning("Could not notify admin %s: %s", admin.user_id, exc)


def run_swap_menu(w: "_w.Worker") -> None:
    import database as db
    import telegram

    mgr = w._crypto_manager()
    if mgr is None:
        w.bot.send_message(w.chat.id, "⚠️ Crypto swaps are not available right now.")
        return
    coins = mgr.get_available_coins()
    if len(coins) < 2:
        w.bot.send_message(w.chat.id, "⚠️ Swap mode needs at least two configured coin addresses.")
        return

    spread_pct = _load_spread_pct()
    coin_keyboard = [[telegram.KeyboardButton(coin)] for coin in coins]
    coin_keyboard.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(
        w.chat.id,
        "🔄 <b>Swap Crypto</b>\n\nChoose the coin you will send.",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardMarkup(coin_keyboard, one_time_keyboard=True),
    )
    coin_in = w._Worker__wait_for_specific_message(coins, cancellable=True)
    if _is_cancel(coin_in):
        return

    payout_coins = [coin for coin in coins if coin != coin_in]
    payout_keyboard = [[telegram.KeyboardButton(coin)] for coin in payout_coins]
    payout_keyboard.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(
        w.chat.id,
        "Choose the coin you want to receive.",
        reply_markup=telegram.ReplyKeyboardMarkup(payout_keyboard, one_time_keyboard=True),
    )
    coin_out = w._Worker__wait_for_specific_message(payout_coins, cancellable=True)
    if _is_cancel(coin_out):
        return

    w.bot.send_message(
        w.chat.id,
        f"Enter the amount of <b>{escape(str(coin_in))}</b> you want to swap.",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )
    amount_reply = w._Worker__wait_for_regex(r"([0-9]+(?:[.,][0-9]+)?)", cancellable=True)
    if _is_cancel(amount_reply):
        return
    amount_in = float(str(amount_reply).replace(",", "."))
    if amount_in <= 0:
        w.bot.send_message(w.chat.id, "❌ The swap amount must be greater than zero.")
        return

    fiat = w.cfg["Payments"]["currency"].lower()
    currency_symbol = w.cfg["Payments"].get("currency_symbol", "€")
    rate_in = mgr.get_live_rate(str(coin_in), fiat)
    rate_out = mgr.get_live_rate(str(coin_out), fiat)
    if rate_in is None or rate_out is None:
        w.bot.send_message(w.chat.id, "❌ Live rates are unavailable right now. Please try again later.")
        return

    fiat_value = amount_in * rate_in
    gross_amount_out = fiat_value / rate_out
    net_amount_out = round(gross_amount_out * (1 - (spread_pct / 100.0)), 8)
    deposit_address = mgr.addresses.get(str(coin_in).upper(), "")
    if not deposit_address:
        w.bot.send_message(w.chat.id, "❌ No deposit address is configured for that coin.")
        return

    confirm_button = "✅ Confirm Swap"
    confirm_keyboard = telegram.ReplyKeyboardMarkup(
        [[telegram.KeyboardButton(confirm_button)], [telegram.KeyboardButton(w.loc.get("menu_cancel"))]],
        one_time_keyboard=True,
    )
    w.bot.send_message(
        w.chat.id,
        (
            "📋 <b>Swap Quote</b>\n\n"
            f"Send: <code>{amount_in:.8f} {coin_in}</code>\n"
            f"Receive: <code>{net_amount_out:.8f} {coin_out}</code>\n"
            f"Estimated fiat value: {currency_symbol}{fiat_value:.2f}\n"
            f"Spread: {spread_pct:.2f}%"
        ),
        parse_mode="HTML",
        reply_markup=confirm_keyboard,
    )
    confirmation = w._Worker__wait_for_specific_message([confirm_button], cancellable=True)
    if _is_cancel(confirmation):
        return

    w.bot.send_message(
        w.chat.id,
        (
            f"💰 Send <code>{amount_in:.8f} {coin_in}</code> to:\n"
            f"<code>{escape(deposit_address)}</code>\n\n"
            "After sending the payment, reply with your transaction ID."
        ),
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )
    tx_reply = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if _is_cancel(tx_reply):
        return
    tx_ref = str(tx_reply).strip()

    swap = db.SwapRequest(
        user_id=w.user.user_id,
        coin_in=str(coin_in).upper(),
        amount_in=f"{amount_in:.8f}",
        coin_out=str(coin_out).upper(),
        amount_out=f"{net_amount_out:.8f}",
        spread_pct=f"{spread_pct:.2f}",
        deposit_addr=deposit_address,
        tx_ref=tx_ref,
        status="pending",
        created_at=datetime.datetime.utcnow(),
    )
    w.session.add(swap)
    w.session.commit()

    admin_message = (
        "🔄 <b>New Swap Request</b>\n"
        f"User: {escape(w.user.mention())} ({w.user.user_id})\n"
        f"Send: <code>{amount_in:.8f} {coin_in}</code>\n"
        f"Receive: <code>{net_amount_out:.8f} {coin_out}</code>\n"
        f"Fiat estimate: {currency_symbol}{fiat_value:.2f}\n"
        f"Spread: {spread_pct:.2f}%\n"
        f"Deposit address: <code>{escape(deposit_address)}</code>\n"
        f"TX ID: <code>{escape(tx_ref)}</code>\n"
        f"Swap request #: {swap.id}"
    )
    _notify_admins(w, admin_message)
    w.bot.send_message(
        w.chat.id,
        f"✅ Swap request #{swap.id} submitted. The admin team will review your payment soon.",
    )
