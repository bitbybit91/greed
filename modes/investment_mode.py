"""
modes/investment_mode.py
Investment Mode — users deposit crypto, view plans/ROI, request withdrawals.
"""
from __future__ import annotations

import datetime
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import worker as _w

log = logging.getLogger(__name__)

# Default plans (owner can extend via DB or config)
DEFAULT_PLANS = [
    {"id": 1, "name": "Starter",  "min_usd": 50,   "roi_pct": 5,  "days": 7},
    {"id": 2, "name": "Growth",   "min_usd": 200,  "roi_pct": 12, "days": 14},
    {"id": 3, "name": "Premium",  "min_usd": 500,  "roi_pct": 25, "days": 30},
    {"id": 4, "name": "VIP",      "min_usd": 2000, "roi_pct": 50, "days": 30},
]


def run_investment_menu(w: "_w.Worker") -> None:
    """Main entry point for the investment mode user flow."""
    import telegram
    from worker import CancelSignal

    while True:
        keyboard = [
            [telegram.KeyboardButton("\U0001f4c8 View Plans")],
            [telegram.KeyboardButton("\U0001f4b0 My Balance")],
            [telegram.KeyboardButton("\U0001f4e4 Deposit")],
            [telegram.KeyboardButton("\U0001f4e5 Withdraw")],
            [telegram.KeyboardButton(w.loc.get("menu_cancel"))],
        ]
        w.bot.send_message(
            w.chat.id,
            "\U0001f4bc <b>Investment Portal</b>\nSelect an option:",
            parse_mode="HTML",
            reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
        )
        sel = w._Worker__wait_for_specific_message(
            ["\U0001f4c8 View Plans", "\U0001f4b0 My Balance",
             "\U0001f4e4 Deposit", "\U0001f4e5 Withdraw"],
            cancellable=True,
        )
        if isinstance(sel, CancelSignal):
            return
        if sel == "\U0001f4c8 View Plans":
            _show_plans(w)
        elif sel == "\U0001f4b0 My Balance":
            _show_balance(w)
        elif sel == "\U0001f4e4 Deposit":
            _deposit_flow(w)
        elif sel == "\U0001f4e5 Withdraw":
            _withdraw_flow(w)


def _show_plans(w: "_w.Worker") -> None:
    import telegram
    lines = ["\U0001f4ca <b>Investment Plans</b>\n"]
    for p in DEFAULT_PLANS:
        roi = p["roi_pct"]
        days = p["days"]
        lines.append(
            f"<b>{p['name']}</b>\n"
            f"  Min: ${p['min_usd']}  |  ROI: {roi}%  |  Duration: {days} days\n"
            f"  Return: ${p['min_usd'] * (1 + roi/100):.2f} after {days} days\n"
        )
    w.bot.send_message(w.chat.id, "\n".join(lines), parse_mode="HTML",
                       reply_markup=telegram.ReplyKeyboardRemove())


def _show_balance(w: "_w.Worker") -> None:
    import database as db
    import telegram
    deposits = (
        w.session.query(db.InvestmentDeposit)
        .filter_by(user_id=w.user.user_id)
        .order_by(db.InvestmentDeposit.id.desc())
        .limit(10)
        .all()
    )
    if not deposits:
        w.bot.send_message(w.chat.id, "You have no active investments.",
                           reply_markup=telegram.ReplyKeyboardRemove())
        return
    lines = ["\U0001f4b0 <b>My Investments</b>\n"]
    for d in deposits:
        status = "Active" if not d.paid_out else "\u2705 Completed"
        lines.append(
            f"#{d.id} | {d.coin} {d.amount:.6f} | "
            f"Plan: {d.plan_name} | {status}\n"
            f"  Deposited: {d.created_at.strftime('%Y-%m-%d')}"
        )
    w.bot.send_message(w.chat.id, "\n".join(lines), parse_mode="HTML",
                       reply_markup=telegram.ReplyKeyboardRemove())


def _deposit_flow(w: "_w.Worker") -> None:
    import telegram
    import database as db
    from crypto_manager import CryptoPaymentManager
    from worker import CancelSignal

    mgr: CryptoPaymentManager = w._crypto_manager()
    coins = mgr.get_available_coins() if mgr else []
    if not coins:
        w.bot.send_message(w.chat.id, "No crypto addresses configured.")
        return

    # Select plan
    plan_names = [p["name"] for p in DEFAULT_PLANS]
    kb = [[telegram.KeyboardButton(n)] for n in plan_names]
    kb.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(w.chat.id, "Select an investment plan:",
                       reply_markup=telegram.ReplyKeyboardMarkup(kb, one_time_keyboard=True))
    plan_sel = w._Worker__wait_for_specific_message(plan_names, cancellable=True)
    if isinstance(plan_sel, CancelSignal):
        return
    plan = next(p for p in DEFAULT_PLANS if p["name"] == plan_sel)

    # Select coin
    kb2 = [[telegram.KeyboardButton(c)] for c in coins]
    kb2.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(w.chat.id, "Select coin to deposit:",
                       reply_markup=telegram.ReplyKeyboardMarkup(kb2, one_time_keyboard=True))
    coin_sel = w._Worker__wait_for_specific_message(coins, cancellable=True)
    if isinstance(coin_sel, CancelSignal):
        return

    # Determine amount
    rate = mgr.get_live_rate(coin_sel, w.cfg["Payments"]["currency"].lower())
    if not rate:
        w.bot.send_message(w.chat.id, f"Could not fetch rate for {coin_sel}.")
        return
    min_crypto = round(plan["min_usd"] / rate, 8)
    address = mgr.addresses.get(coin_sel.upper(), "")
    w.bot.send_message(
        w.chat.id,
        f"\U0001f4b0 <b>Investment Deposit</b>\n\n"
        f"Plan: <b>{plan['name']}</b> | ROI: {plan['roi_pct']}% in {plan['days']} days\n\n"
        f"Send at least <code>{min_crypto} {coin_sel}</code>\n"
        f"To: <code>{address}</code>\n\n"
        f"After sending, enter your transaction ID below.",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )
    tx = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if isinstance(tx, CancelSignal):
        return

    # Store pending deposit
    try:
        dep = db.InvestmentDeposit(
            user_id=w.user.user_id,
            coin=coin_sel.upper(),
            amount=str(min_crypto),
            plan_name=plan["name"],
            roi_pct=plan["roi_pct"],
            duration_days=plan["days"],
            tx_ref=str(tx).strip(),
            paid_out=False,
            created_at=datetime.datetime.now(),
        )
        w.session.add(dep)
        w.session.commit()
    except Exception as exc:
        log.warning(f"Could not save InvestmentDeposit: {exc}")
        w.session.rollback()

    w.bot.send_message(
        w.chat.id,
        "\u2705 Deposit request recorded! The owner will verify and activate your plan.",
    )

    # Notify admins
    admins = w.session.query(db.Admin).filter_by(receive_orders=True).all()
    for admin in admins:
        try:
            w.bot.send_message(
                admin.user_id,
                f"\U0001f4bc <b>Investment Deposit Request</b>\n"
                f"User: {w.user.mention()} ({w.user.user_id})\n"
                f"Plan: {plan['name']} | ROI: {plan['roi_pct']}% in {plan['days']} days\n"
                f"Coin: {coin_sel.upper()} — min {min_crypto}\n"
                f"Address: <code>{address}</code>\n"
                f"TX ref: {str(tx).strip()}",
                parse_mode="HTML",
            )
        except Exception as exc:
            log.warning(f"Could not notify admin {admin.user_id}: {exc}")


def _withdraw_flow(w: "_w.Worker") -> None:
    import telegram
    import database as db
    from worker import CancelSignal
    w.bot.send_message(
        w.chat.id,
        "\U0001f4e5 <b>Withdrawal Request</b>\n\n"
        "Please provide your withdrawal address and amount:\n"
        "Format: <code>COIN ADDRESS AMOUNT</code>\n"
        "Example: <code>BTC bc1qxxx 0.01</code>",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )
    reply = w._Worker__wait_for_regex(r"(\S+ \S+ [0-9.]+)", cancellable=True)
    if isinstance(reply, CancelSignal):
        return
    parts = str(reply).strip().split()
    if len(parts) != 3:
        w.bot.send_message(w.chat.id, "\u274c Invalid format. Please try again.")
        return
    coin, addr, amount = parts
    w.bot.send_message(
        w.chat.id,
        f"\u23f3 Withdrawal request for {amount} {coin.upper()} to\n"
        f"<code>{addr}</code>\nsubmitted. Owner will process it shortly.",
        parse_mode="HTML",
    )
    # Notify admins
    admins = w.session.query(db.Admin).filter_by(receive_orders=True).all()
    for admin in admins:
        try:
            w.bot.send_message(
                admin.user_id,
                f"\U0001f4e5 <b>Withdrawal Request</b>\n"
                f"User: {w.user.mention()} ({w.user.user_id})\n"
                f"Coin: {coin.upper()}\nAmount: {amount}\nAddress: {addr}",
                parse_mode="HTML",
            )
        except Exception as exc:
            log.warning(f"Could not notify admin {admin.user_id}: {exc}")
