"""
modes/shop_mode.py
Shop Mode — Product catalog, cart, crypto checkout, shipping follow-up.
Functions receive a Worker instance and use its internal helpers.
"""
from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import worker as _w

log = logging.getLogger(__name__)


# ── Crypto Checkout (called after cart is confirmed) ───────────────────────
def run_crypto_checkout(w: "_w.Worker", order_total_cents: int) -> dict | None:
    """
    Present all available crypto coins, let the user pick one, show the
    payment address + exact amount, and wait for owner confirmation.
    Returns a dict with payment details on success, None on cancel.
    """
    import telegram
    from crypto_manager import CryptoPaymentManager

    mgr: CryptoPaymentManager = w._crypto_manager()
    coins = mgr.get_available_coins()
    if not coins:
        w.bot.send_message(
            w.chat.id,
            "\u26a0\ufe0f No cryptocurrency addresses are configured. "
            "Please contact the shop owner.",
        )
        return None

    # Build coin-selection keyboard
    keyboard = [[telegram.KeyboardButton(c)] for c in coins]
    keyboard.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(
        w.chat.id,
        "\U0001f4b0 <b>Select cryptocurrency to pay with:</b>",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
    )
    selection = w._Worker__wait_for_specific_message(coins, cancellable=True)
    if hasattr(selection, "__class__") and selection.__class__.__name__ == "CancelSignal":
        return None

    coin = selection.upper()
    info = mgr.get_payment_info(
        fiat_cents=order_total_cents,
        coin=coin,
        currency_exp=w.cfg["Payments"]["currency_exp"],
        fiat=w.cfg["Payments"]["currency"].lower(),
        currency_symbol=w.cfg["Payments"].get("currency_symbol", "€"),
    )
    if not info:
        w.bot.send_message(
            w.chat.id,
            f"\u274c Could not get rate for {coin}. Try another coin or contact support.",
        )
        return None

    # Show payment details
    w.bot.send_message(
        w.chat.id,
        "\U0001f4cb <b>Payment Instructions</b>\n\n" + info["display"],
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )
    w.bot.send_message(
        w.chat.id,
        "\u23f3 Waiting for the owner to confirm your payment. "
        "Please send your transaction ID or a screenshot as proof.",
    )

    # Wait for user to provide tx reference
    w.bot.send_message(w.chat.id, "Please send your transaction ID / hash:")
    tx_ref_msg = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if hasattr(tx_ref_msg, "__class__") and tx_ref_msg.__class__.__name__ == "CancelSignal":
        tx_ref = "not provided"
    else:
        tx_ref = str(tx_ref_msg).strip()

    return {
        "coin": info["coin"],
        "address": info["address"],
        "amount": info["amount"],
        "fiat_amount": info["fiat_amount"],
        "fiat_symbol": info["fiat_symbol"],
        "tx_ref": tx_ref,
        "qr_string": info["qr_string"],
    }


# ── Shipping Details Collection ─────────────────────────────────────────────
def collect_shipping_details(w: "_w.Worker") -> dict | None:
    """
    FSM-style conversation to collect shipping details after payment.
    Returns dict with name/address/phone/notes, or None on cancel.
    """
    import telegram

    cancel_kb = telegram.InlineKeyboardMarkup(
        [[telegram.InlineKeyboardButton(w.loc.get("menu_cancel"), callback_data="cmd_cancel")]]
    )

    w.bot.send_message(
        w.chat.id,
        "\U0001f69a <b>Shipping Details</b>\n\nPlease provide the following information.",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )

    # Full name
    w.bot.send_message(w.chat.id, "\U0001f464 Full name:", reply_markup=cancel_kb)
    name = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if hasattr(name, "__class__") and name.__class__.__name__ == "CancelSignal":
        return None

    # Delivery address
    w.bot.send_message(w.chat.id, "\U0001f3e0 Delivery address (street, city, country):",
                       reply_markup=cancel_kb)
    address = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if hasattr(address, "__class__") and address.__class__.__name__ == "CancelSignal":
        return None

    # Phone
    w.bot.send_message(w.chat.id, "\U0001f4f1 Phone number:", reply_markup=cancel_kb)
    phone = w._Worker__wait_for_regex(r"(\+?[0-9\s\-]{7,})", cancellable=True)
    if hasattr(phone, "__class__") and phone.__class__.__name__ == "CancelSignal":
        return None

    # Notes
    skip_kb = telegram.InlineKeyboardMarkup(
        [[telegram.InlineKeyboardButton("Skip", callback_data="cmd_cancel")]]
    )
    w.bot.send_message(w.chat.id, "\U0001f4dd Additional notes (or press Skip):",
                       reply_markup=skip_kb)
    notes_raw = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    notes = "" if (hasattr(notes_raw, "__class__") and
                   notes_raw.__class__.__name__ == "CancelSignal") else str(notes_raw).strip()

    return {
        "name": str(name).strip(),
        "address": str(address).strip(),
        "phone": str(phone).strip(),
        "notes": notes,
    }


# ── Notify Owner After Order ─────────────────────────────────────────────────
def notify_owner_of_order(
    w: "_w.Worker",
    order,
    payment_info: dict,
    shipping: dict,
) -> None:
    """Send a full order summary to all admins with receive_orders permission."""
    import database as db

    admins = (
        w.session.query(db.Admin)
        .filter_by(receive_orders=True)
        .all()
    )
    lines = [
        "\U0001f6d2 <b>NEW ORDER — Crypto Payment</b>",
        f"\U0001f464 Customer: {w.user.mention()} (ID {w.user.user_id})",
        f"\U0001f4e6 Order #: {order.order_id}",
        "",
        "<b>Items:</b>",
    ]
    for item in order.items:
        lines.append(f"  • {item.product.name} — {str(w.Price(item.product.price))}")

    lines += [
        "",
        f"<b>Payment:</b>",
        f"  Coin: {payment_info['coin']}",
        f"  Amount: {payment_info['amount']} {payment_info['coin']}",
        f"  Fiat: {payment_info['fiat_symbol']}{payment_info['fiat_amount']:.2f}",
        f"  Tx ref: {payment_info['tx_ref']}",
        f"  Address: <code>{payment_info['address']}</code>",
        "",
        "<b>Shipping:</b>",
        f"  Name: {shipping['name']}",
        f"  Address: {shipping['address']}",
        f"  Phone: {shipping['phone']}",
    ]
    if shipping.get("notes"):
        lines.append(f"  Notes: {shipping['notes']}")

    msg = "\n".join(lines)
    for admin in admins:
        try:
            w.bot.send_message(admin.user_id, msg, parse_mode="HTML")
        except Exception as exc:
            log.warning(f"Could not notify admin {admin.user_id}: {exc}")
