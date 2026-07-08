from __future__ import annotations

import datetime
import logging
from html import escape
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import worker as _w

log = logging.getLogger(__name__)

PLANS = [
    {"name": "Starter", "min_amount": 50, "roi_pct": 5, "duration_days": 7},
    {"name": "Growth", "min_amount": 200, "roi_pct": 12, "duration_days": 14},
    {"name": "Premium", "min_amount": 500, "roi_pct": 25, "duration_days": 30},
    {"name": "VIP", "min_amount": 2000, "roi_pct": 50, "duration_days": 30},
]


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


def _format_plan(plan: dict, symbol: str) -> str:
    return (
        f"<b>{plan['name']}</b>\n"
        f"Minimum: {symbol}{plan['min_amount']:.2f}\n"
        f"ROI: {plan['roi_pct']}%\n"
        f"Duration: {plan['duration_days']} days"
    )


def run_investment_menu(w: "_w.Worker") -> None:
    import telegram

    actions = ["📊 View Plans", "💼 Active Investments", "💰 New Deposit", "📤 Withdraw"]
    while True:
        keyboard = [[telegram.KeyboardButton(action)] for action in actions]
        keyboard.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
        w.bot.send_message(
            w.chat.id,
            "💼 <b>Investment Portal</b>\n\nChoose an action.",
            parse_mode="HTML",
            reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
        )
        selection = w._Worker__wait_for_specific_message(actions, cancellable=True)
        if _is_cancel(selection):
            return
        if selection == actions[0]:
            _show_plans(w)
        elif selection == actions[1]:
            _show_active_investments(w)
        elif selection == actions[2]:
            _run_deposit_flow(w)
        elif selection == actions[3]:
            _run_withdraw_flow(w)


def _show_plans(w: "_w.Worker") -> None:
    symbol = w.cfg["Payments"].get("currency_symbol", "€")
    lines = ["📊 <b>Investment Plans</b>"]
    for plan in PLANS:
        lines.append(_format_plan(plan, symbol))
    w.bot.send_message(w.chat.id, "\n\n".join(lines), parse_mode="HTML")


def _show_active_investments(w: "_w.Worker") -> None:
    import database as db

    deposits = (
        w.session.query(db.InvestmentDeposit)
        .filter_by(user_id=w.user.user_id)
        .order_by(db.InvestmentDeposit.created_at.desc())
        .all()
    )
    if not deposits:
        w.bot.send_message(w.chat.id, "You do not have any investment deposits yet.")
        return
    lines = ["💼 <b>Your Investments</b>"]
    for deposit in deposits:
        created_at = deposit.created_at.strftime("%Y-%m-%d") if deposit.created_at else "unknown"
        maturity = "—"
        if deposit.created_at and deposit.duration_days:
            maturity = (deposit.created_at + datetime.timedelta(days=deposit.duration_days)).strftime("%Y-%m-%d")
        status = "Paid out" if deposit.paid_out else "Active"
        lines.append(
            f"#{deposit.id} • <b>{escape(deposit.plan_name or 'Plan')}</b>\n"
            f"Amount: <code>{escape(str(deposit.amount))} {escape(deposit.coin)}</code>\n"
            f"ROI: {deposit.roi_pct or 0}% • Duration: {deposit.duration_days or 0} days\n"
            f"Deposited: {created_at} • Matures: {maturity}\n"
            f"Status: {status}"
        )
    w.bot.send_message(w.chat.id, "\n\n".join(lines), parse_mode="HTML")


def _run_deposit_flow(w: "_w.Worker") -> None:
    import database as db
    import telegram

    mgr = w._crypto_manager()
    if mgr is None:
        w.bot.send_message(w.chat.id, "⚠️ Crypto investments are not available right now.")
        return
    coins = mgr.get_available_coins()
    if not coins:
        w.bot.send_message(w.chat.id, "⚠️ No investment deposit coins are configured yet.")
        return

    plan_names = [plan["name"] for plan in PLANS]
    plan_keyboard = [[telegram.KeyboardButton(name)] for name in plan_names]
    plan_keyboard.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(
        w.chat.id,
        "Choose an investment plan.",
        reply_markup=telegram.ReplyKeyboardMarkup(plan_keyboard, one_time_keyboard=True),
    )
    plan_name = w._Worker__wait_for_specific_message(plan_names, cancellable=True)
    if _is_cancel(plan_name):
        return
    plan = next((item for item in PLANS if item["name"] == plan_name), None)
    if plan is None:
        w.bot.send_message(w.chat.id, "❌ Invalid plan selection.")
        return

    coin_keyboard = [[telegram.KeyboardButton(coin)] for coin in coins]
    coin_keyboard.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(
        w.chat.id,
        "Choose the coin you want to deposit.",
        reply_markup=telegram.ReplyKeyboardMarkup(coin_keyboard, one_time_keyboard=True),
    )
    coin = w._Worker__wait_for_specific_message(coins, cancellable=True)
    if _is_cancel(coin):
        return

    symbol = w.cfg["Payments"].get("currency_symbol", "€")
    currency = w.cfg["Payments"]["currency"]
    w.bot.send_message(
        w.chat.id,
        (
            f"Enter your investment amount in {currency}.\n"
            f"Minimum for <b>{escape(plan['name'])}</b>: {symbol}{plan['min_amount']:.2f}"
        ),
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )
    amount_reply = w._Worker__wait_for_regex(r"([0-9]+(?:[.,][0-9]{1,2})?)", cancellable=True)
    if _is_cancel(amount_reply):
        return
    fiat_cents = int(w.Price(amount_reply))
    if fiat_cents < int(w.Price(plan["min_amount"])):
        w.bot.send_message(
            w.chat.id,
            f"❌ The minimum for {plan['name']} is {symbol}{plan['min_amount']:.2f}.",
        )
        return

    info = mgr.get_payment_info(
        fiat_cents=fiat_cents,
        coin=str(coin),
        currency_exp=w.cfg["Payments"]["currency_exp"],
        fiat=currency.lower(),
        currency_symbol=symbol,
    )
    if info is None:
        w.bot.send_message(w.chat.id, "❌ Could not generate a crypto deposit quote right now.")
        return

    w.bot.send_message(
        w.chat.id,
        (
            f"💰 <b>{escape(plan['name'])} Deposit</b>\n\n"
            f"ROI: {plan['roi_pct']}% over {plan['duration_days']} days\n\n"
            f"{info['display']}\n\n"
            "Reply with your transaction ID after sending the deposit."
        ),
        parse_mode="HTML",
    )
    tx_reply = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if _is_cancel(tx_reply):
        return
    tx_ref = str(tx_reply).strip()

    deposit = db.InvestmentDeposit(
        user_id=w.user.user_id,
        coin=info["coin"],
        amount=str(info["amount"]),
        plan_name=plan["name"],
        roi_pct=plan["roi_pct"],
        duration_days=plan["duration_days"],
        tx_ref=tx_ref,
        paid_out=False,
        created_at=datetime.datetime.utcnow(),
    )
    w.session.add(deposit)
    w.session.commit()

    _notify_admins(
        w,
        (
            "💼 <b>New Investment Deposit</b>\n"
            f"User: {escape(w.user.mention())} ({w.user.user_id})\n"
            f"Plan: {escape(plan['name'])}\n"
            f"Amount: <code>{escape(str(info['amount']))} {escape(info['coin'])}</code>\n"
            f"Fiat snapshot: {symbol}{info['fiat_amount']:.2f}\n"
            f"Address: <code>{escape(info['address'])}</code>\n"
            f"TX ID: <code>{escape(tx_ref)}</code>\n"
            f"Deposit #: {deposit.id}"
        ),
    )
    w.bot.send_message(
        w.chat.id,
        f"✅ Investment deposit #{deposit.id} recorded. Admins have been notified.",
    )


def _run_withdraw_flow(w: "_w.Worker") -> None:
    import database as db
    import telegram

    active_deposits = (
        w.session.query(db.InvestmentDeposit)
        .filter_by(user_id=w.user.user_id, paid_out=False)
        .order_by(db.InvestmentDeposit.created_at.desc())
        .all()
    )
    if not active_deposits:
        w.bot.send_message(w.chat.id, "You do not have any active investments to withdraw from.")
        return

    deposit_options = [f"#{deposit.id} {deposit.plan_name}" for deposit in active_deposits]
    keyboard = [[telegram.KeyboardButton(option)] for option in deposit_options]
    keyboard.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(
        w.chat.id,
        "Select the investment you want to withdraw.",
        reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
    )
    selection = w._Worker__wait_for_specific_message(deposit_options, cancellable=True)
    if _is_cancel(selection):
        return
    deposit_id = int(str(selection).split()[0].lstrip("#"))
    deposit = next((item for item in active_deposits if item.id == deposit_id), None)
    if deposit is None:
        w.bot.send_message(w.chat.id, "❌ Invalid investment selection.")
        return

    w.bot.send_message(w.chat.id, "Enter the payout wallet address.", reply_markup=telegram.ReplyKeyboardRemove())
    address_reply = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if _is_cancel(address_reply):
        return
    payout_address = str(address_reply).strip()

    w.bot.send_message(w.chat.id, "Add any withdrawal notes, or type N/A.")
    note_reply = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if _is_cancel(note_reply):
        return
    notes = str(note_reply).strip()

    _notify_admins(
        w,
        (
            "📤 <b>Investment Withdrawal Request</b>\n"
            f"User: {escape(w.user.mention())} ({w.user.user_id})\n"
            f"Investment #: {deposit.id}\n"
            f"Plan: {escape(deposit.plan_name or 'Plan')}\n"
            f"Amount: <code>{escape(str(deposit.amount))} {escape(deposit.coin)}</code>\n"
            f"Payout address: <code>{escape(payout_address)}</code>\n"
            f"Notes: {escape(notes)}"
        ),
    )
    w.bot.send_message(w.chat.id, "✅ Withdrawal request sent to the admins.")
