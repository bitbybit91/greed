from __future__ import annotations

import datetime
import logging
from html import escape
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import worker as _w

log = logging.getLogger(__name__)


def _is_cancel(value) -> bool:
    from worker import CancelSignal

    return isinstance(value, CancelSignal)


def _notify_admins(w: "_w.Worker", message: str) -> None:
    import database as db

    admins = w.session.query(db.Admin).filter_by(receive_orders=True).all()
    for admin in admins:
        try:
            w.bot.send_message(admin.user_id, message, parse_mode="HTML")
        except Exception as exc:
            log.warning("Could not notify admin %s: %s", admin.user_id, exc)


def run_shop_checkout(w: "_w.Worker", order, order_total_cents: int) -> bool:
    import database as db
    import telegram

    payment_info = run_crypto_checkout(w, order_total_cents)
    if payment_info is None:
        return False

    shipping = collect_shipping_details(w)
    if shipping is None:
        return False

    w.session.flush()
    transaction = db.Transaction(
        user=w.user,
        value=0,
        order=order,
        provider=f"Crypto:{payment_info['coin']}",
        notes=(
            f"ORDER_TOTAL_CENTS={int(order_total_cents)}|"
            f"CRYPTO_AMOUNT={payment_info['amount']}|"
            f"TX={payment_info['tx_ref']}"
        ),
    )
    crypto_deposit = db.CryptoDeposit(
        user_id=w.user.user_id,
        coin=payment_info["coin"],
        address=payment_info["address"],
        amount=str(payment_info["amount"]),
        fiat_amount=f"{payment_info['fiat_amount']:.2f}",
        tx_ref=payment_info["tx_ref"],
        confirmed=False,
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    shipping_details = db.ShippingDetails(
        order=order,
        name=shipping["name"],
        address=shipping["address"],
        phone=shipping["phone"],
        notes=shipping.get("notes", ""),
        created_at=datetime.datetime.now(datetime.timezone.utc),
    )
    w.session.add(transaction)
    w.session.add(crypto_deposit)
    w.session.add(shipping_details)
    w.session.commit()

    notify_owner_of_order(w, order, payment_info, shipping)
    w.bot.send_message(
        w.chat.id,
        f"✅ Order #{order.order_id} received. Your crypto payment is now pending manual review.",
    )
    return True


def run_crypto_checkout(w: "_w.Worker", order_total_cents: int) -> Optional[dict]:
    import telegram

    mgr = w._crypto_manager()
    if mgr is None:
        w.bot.send_message(w.chat.id, "⚠️ Crypto checkout is not available right now.")
        return None
    coins = mgr.get_available_coins()
    if not coins:
        w.bot.send_message(w.chat.id, "⚠️ No payment coins are configured yet. Please contact the owner.")
        return None

    keyboard = [[telegram.KeyboardButton(coin)] for coin in coins]
    keyboard.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(
        w.chat.id,
        "💰 <b>Select the cryptocurrency you want to pay with.</b>",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
    )
    coin = w._Worker__wait_for_specific_message(coins, cancellable=True)
    if _is_cancel(coin):
        return None

    info = mgr.get_payment_info(
        fiat_cents=int(order_total_cents),
        coin=str(coin),
        currency_exp=w.cfg["Payments"]["currency_exp"],
        fiat=w.cfg["Payments"]["currency"].lower(),
        currency_symbol=w.cfg["Payments"].get("currency_symbol", "€"),
    )
    if info is None:
        w.bot.send_message(w.chat.id, "❌ Could not fetch a payment quote for that coin. Please try again.")
        return None

    w.bot.send_message(
        w.chat.id,
        f"📋 <b>Payment Instructions</b>\n\n{info['display']}",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )
    w.bot.send_message(w.chat.id, "Reply with your TX ID or proof reference after sending the payment.")
    tx_reply = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if _is_cancel(tx_reply):
        return None
    info["tx_ref"] = str(tx_reply).strip()
    return info


def collect_shipping_details(w: "_w.Worker") -> Optional[dict]:
    import telegram

    cancel = telegram.InlineKeyboardMarkup(
        [[telegram.InlineKeyboardButton(w.loc.get("menu_cancel"), callback_data="cmd_cancel")]]
    )
    w.bot.send_message(
        w.chat.id,
        "🚚 <b>Shipping Details</b>",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )

    w.bot.send_message(w.chat.id, "Full name:", reply_markup=cancel)
    name = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if _is_cancel(name):
        return None

    w.bot.send_message(w.chat.id, "Shipping address:", reply_markup=cancel)
    address = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if _is_cancel(address):
        return None

    w.bot.send_message(w.chat.id, "Phone number:", reply_markup=cancel)
    phone = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if _is_cancel(phone):
        return None

    skip_keyboard = telegram.InlineKeyboardMarkup(
        [[telegram.InlineKeyboardButton("Skip", callback_data="cmd_cancel")]]
    )
    w.bot.send_message(w.chat.id, "Order notes (or press Skip):", reply_markup=skip_keyboard)
    notes = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if _is_cancel(notes):
        notes = ""

    return {
        "name": str(name).strip(),
        "address": str(address).strip(),
        "phone": str(phone).strip(),
        "notes": str(notes).strip(),
    }


def notify_owner_of_order(w: "_w.Worker", order, payment_info: dict, shipping: dict) -> None:
    lines = [
        "🛒 <b>New Crypto Order</b>",
        f"Customer: {escape(w.user.mention())} ({w.user.user_id})",
        f"Order #: {order.order_id}",
        "",
        "<b>Items</b>",
    ]
    for item in order.items:
        lines.append(f"• {escape(item.product.name)} — {escape(str(w.Price(item.product.price)))}")
    if order.notes:
        lines.extend(["", f"Order notes: {escape(order.notes)}"])
    lines.extend(
        [
            "",
            "<b>Payment</b>",
            f"Coin: {escape(payment_info['coin'])}",
            f"Amount: <code>{escape(str(payment_info['amount']))} {escape(payment_info['coin'])}</code>",
            f"Fiat snapshot: {payment_info['fiat_symbol']}{payment_info['fiat_amount']:.2f}",
            f"Deposit address: <code>{escape(payment_info['address'])}</code>",
            f"TX / proof: <code>{escape(payment_info['tx_ref'])}</code>",
            "",
            "<b>Shipping</b>",
            f"Name: {escape(shipping['name'])}",
            f"Address: {escape(shipping['address'])}",
            f"Phone: {escape(shipping['phone'])}",
        ]
    )
    if shipping.get("notes"):
        lines.append(f"Shipping notes: {escape(shipping['notes'])}")
    _notify_admins(w, "\n".join(lines))
