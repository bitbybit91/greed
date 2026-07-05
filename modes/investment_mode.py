"""
investment_mode.py
==================
Investment bot mode: user deposits crypto, browses plans, tracks ROI, requests withdrawal.
Entry point: run_investment_mode(worker_instance)
"""
import logging
import datetime
from typing import Optional

import telegram

log = logging.getLogger(__name__)

# ── Investment plans — owner can extend these in mode_config.toml ──────────────
DEFAULT_PLANS = [
    {"id": "basic",    "name": "Basic Plan",    "duration_days": 7,  "roi_percent": 5.0,   "min_usd": 50},
    {"id": "standard", "name": "Standard Plan", "duration_days": 14, "roi_percent": 12.0,  "min_usd": 100},
    {"id": "premium",  "name": "Premium Plan",  "duration_days": 30, "roi_percent": 30.0,  "min_usd": 250},
]


def _load_plans(cfg_path: str):
    """Load investment plans from mode_config.toml if present."""
    try:
        import toml, os
        if not os.path.exists(cfg_path):
            return DEFAULT_PLANS
        with open(cfg_path) as fh:
            data = toml.load(fh)
        plans = data.get("investment", {}).get("plans", [])
        return plans if plans else DEFAULT_PLANS
    except Exception as exc:
        log.warning("Could not load investment plans: %s", exc)
        return DEFAULT_PLANS


def run_investment_mode(w) -> None:
    """Main user-menu loop for INVESTMENT_BOT mode."""
    import database as db
    from worker import CancelSignal

    cfg_path = str(w.cfg["Database"].get("engine", "").replace("sqlite:///", "") or "config/mode_config.toml")
    try:
        cfg_path = "config/mode_config.toml"
    except Exception:
        cfg_path = "config/mode_config.toml"

    while True:
        keyboard = [
            [telegram.KeyboardButton("📊 View Investment Plans")],
            [telegram.KeyboardButton("💰 Deposit Crypto")],
            [telegram.KeyboardButton("📈 My Portfolio")],
            [telegram.KeyboardButton("💸 Request Withdrawal")],
            [telegram.KeyboardButton(w.loc.get("menu_help"))],
        ]
        w.bot.send_message(
            w.chat.id,
            f"🏦 <b>Investment Dashboard</b>\n\nWallet Balance: <b>{w.Price(w.user.credit)}</b>\n\nChoose an option:",
            reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
        )

        valid = [
            "📊 View Investment Plans",
            "💰 Deposit Crypto",
            "📈 My Portfolio",
            "💸 Request Withdrawal",
            w.loc.get("menu_help"),
        ]
        selection = w._wait_for_message(valid)

        if selection == "📊 View Investment Plans":
            _show_plans(w, cfg_path)
        elif selection == "💰 Deposit Crypto":
            w._add_credit_crypto()
        elif selection == "📈 My Portfolio":
            _show_portfolio(w)
        elif selection == "💸 Request Withdrawal":
            _request_withdrawal(w)
        elif selection == w.loc.get("menu_help"):
            w._help_menu()


def _show_plans(w, cfg_path: str) -> None:
    """Display available investment plans."""
    plans = _load_plans(cfg_path)
    text = "📊 <b>Available Investment Plans</b>\n\n"
    buttons = []
    for plan in plans:
        text += (
            f"🔹 <b>{plan['name']}</b>\n"
            f"   Duration: {plan['duration_days']} days\n"
            f"   ROI: +{plan['roi_percent']}%\n"
            f"   Minimum: ${plan['min_usd']}\n\n"
        )
        buttons.append([telegram.InlineKeyboardButton(
            f"Invest in {plan['name']}",
            callback_data=f"invest_{plan['id']}"
        )])

    buttons.append([telegram.InlineKeyboardButton("← Back", callback_data="cmd_cancel")])
    markup = telegram.InlineKeyboardMarkup(buttons)
    w.bot.send_message(w.chat.id, text, reply_markup=markup)
    cb = w._wait_for_callback(cancellable=True)
    if not cb or cb == "cmd_cancel":
        return

    plan_id = cb.replace("invest_", "")
    plan = next((p for p in plans if p["id"] == plan_id), None)
    if not plan:
        return
    _confirm_investment(w, plan)


def _confirm_investment(w, plan: dict) -> None:
    """Confirm and record an investment in a specific plan."""
    import database as db
    from worker import CancelSignal

    min_cents = int(plan["min_usd"] * (10 ** w.cfg["Payments"]["currency_exp"]))
    if w.user.credit < min_cents:
        w.bot.send_message(
            w.chat.id,
            f"❌ Insufficient balance. You need at least ${plan['min_usd']:.2f}.\n"
            f"Your balance: {w.Price(w.user.credit)}\n\n"
            f"Use <b>💰 Deposit Crypto</b> to top up first."
        )
        return

    w.bot.send_message(
        w.chat.id,
        f"✅ <b>Confirm Investment</b>\n\n"
        f"Plan: <b>{plan['name']}</b>\n"
        f"Amount to invest: <b>{w.Price(min_cents)}</b>\n"
        f"Duration: <b>{plan['duration_days']} days</b>\n"
        f"Expected return: <b>+{plan['roi_percent']}%</b> = "
        f"<b>{w.Price(int(min_cents * (1 + plan['roi_percent']/100)))}</b>\n\n"
        f"Reply YES to confirm or NO to cancel.",
        reply_markup=telegram.ReplyKeyboardMarkup(
            [["YES", "NO"]], one_time_keyboard=True
        )
    )
    confirm = w._wait_for_message(["YES", "NO"])
    if confirm != "YES":
        w.bot.send_message(w.chat.id, "Investment cancelled.")
        return

    # Debit the wallet via a transaction
    note = (
        f"Investment: {plan['name']} | "
        f"ROI {plan['roi_percent']}% in {plan['duration_days']}d | "
        f"Started {datetime.datetime.now().date()}"
    )
    txn = db.Transaction(
        user  = w.user,
        value = -min_cents,
        notes = note,
    )
    w.session.add(txn)
    w.session.commit()
    w.user.recalculate_credit()
    w.session.commit()

    w.bot.send_message(
        w.chat.id,
        f"🎉 Investment confirmed!\n\n"
        f"Plan: <b>{plan['name']}</b>\n"
        f"Amount: <b>{w.Price(min_cents)}</b>\n"
        f"Expected return date: <b>{(datetime.datetime.now() + datetime.timedelta(days=plan['duration_days'])).date()}</b>\n\n"
        f"The owner will credit your profits when the plan matures.\n"
        f"Your current balance: <b>{w.Price(w.user.credit)}</b>"
    )


def _show_portfolio(w) -> None:
    """Show the user's transaction history as their portfolio."""
    import database as db

    txns = (
        w.session.query(db.Transaction)
        .filter(db.Transaction.user == w.user)
        .order_by(db.Transaction.transaction_id.desc())
        .limit(15)
        .all()
    )
    if not txns:
        w.bot.send_message(w.chat.id, "📈 No investment activity found yet.")
        return

    lines = ["📈 <b>Your Transaction History</b>\n"]
    for txn in txns:
        sign = "+" if txn.value > 0 else ""
        status = " [REFUNDED]" if txn.refunded else ""
        lines.append(
            f"• T{txn.transaction_id}: {sign}{w.Price(txn.value)}{status}"
            + (f"\n  <i>{txn.notes}</i>" if txn.notes else "")
        )
    lines.append(f"\n💰 Current Balance: <b>{w.Price(w.user.credit)}</b>")
    w.bot.send_message(w.chat.id, "\n".join(lines))


def _request_withdrawal(w) -> None:
    """Collect withdrawal request details and notify owner."""
    import database as db
    from worker import CancelSignal

    if w.user.credit <= 0:
        w.bot.send_message(w.chat.id, "❌ Your balance is zero. Nothing to withdraw.")
        return

    w.bot.send_message(
        w.chat.id,
        f"💸 <b>Withdrawal Request</b>\n\n"
        f"Available balance: <b>{w.Price(w.user.credit)}</b>\n\n"
        f"Please enter your crypto wallet address to receive the withdrawal,\n"
        f"or send /cancel to abort."
    )
    from worker import CancelSignal
    address = w._wait_for_regex(r"(.+)", cancellable=True)
    if isinstance(address, CancelSignal):
        w.bot.send_message(w.chat.id, "Withdrawal cancelled.")
        return

    w.bot.send_message(
        w.chat.id,
        f"Which coin do you want to receive? (e.g. BTC, ETH, XMR, USDT)"
    )
    coin = w._wait_for_regex(r"([A-Za-z]+)", cancellable=True)
    if isinstance(coin, CancelSignal):
        w.bot.send_message(w.chat.id, "Withdrawal cancelled.")
        return
    coin = coin.upper()

    # Notify owner
    owner_admin = (
        w.session.query(db.Admin).filter_by(is_owner=True).first()
    )
    note = (
        f"💸 WITHDRAWAL REQUEST\n"
        f"User: {w.user.mention()} (ID: {w.user.user_id})\n"
        f"Amount: {w.Price(w.user.credit)}\n"
        f"Coin: {coin}\n"
        f"Address: {address}"
    )
    if owner_admin:
        w.bot.send_message(owner_admin.user_id, note)

    w.bot.send_message(
        w.chat.id,
        f"✅ Withdrawal request submitted!\n\n"
        f"Amount: <b>{w.Price(w.user.credit)}</b> in <b>{coin}</b>\n"
        f"Address: <code>{address}</code>\n\n"
        f"The owner will process your request shortly."
    )
