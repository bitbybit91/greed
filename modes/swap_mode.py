"""
swap_mode.py
============
Swap bot mode: user selects coin-in / coin-out, gets live CoinGecko rate quote,
deposits coin-in, and owner pays out coin-out after applying spread.
Entry point: run_swap_mode(worker_instance)
"""
import logging
import datetime
from typing import Optional

import telegram

log = logging.getLogger(__name__)

DEFAULT_SPREAD_PERCENT = 2.0   # owner profit margin


def _get_spread(cfg_path: str = "config/mode_config.toml") -> float:
    try:
        import toml, os
        if not os.path.exists(cfg_path):
            return DEFAULT_SPREAD_PERCENT
        with open(cfg_path) as fh:
            data = toml.load(fh)
        return float(data.get("swap", {}).get("spread_percent", DEFAULT_SPREAD_PERCENT))
    except Exception:
        return DEFAULT_SPREAD_PERCENT


def run_swap_mode(w) -> None:
    """Main user-menu loop for SWAP_BOT mode."""
    from worker import CancelSignal

    while True:
        keyboard = [
            [telegram.KeyboardButton("🔄 Get Swap Quote")],
            [telegram.KeyboardButton("📜 Swap History")],
            [telegram.KeyboardButton(w.loc.get("menu_help"))],
        ]
        w.bot.send_message(
            w.chat.id,
            "🔄 <b>Crypto Swap Service</b>\n\nInstant peer-to-peer crypto swaps.\n\nChoose an option:",
            reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
        )
        valid = ["🔄 Get Swap Quote", "📜 Swap History", w.loc.get("menu_help")]
        selection = w._wait_for_message(valid)

        if selection == "🔄 Get Swap Quote":
            _swap_flow(w)
        elif selection == "📜 Swap History":
            _show_swap_history(w)
        elif selection == w.loc.get("menu_help"):
            w._help_menu()


def _swap_flow(w) -> None:
    """Walk the user through the swap selection → quote → deposit flow."""
    from worker import CancelSignal
    import database as db

    mgr = w._get_crypto_manager()
    available = list(mgr.get_available_coins().keys())
    all_supported = list(mgr.COIN_GECKO_IDS.keys())

    if not available:
        w.bot.send_message(
            w.chat.id,
            "⚠️ No payout coins configured yet. Please contact the owner."
        )
        return

    # Step 1: Choose coin to send
    coin_buttons = [[telegram.InlineKeyboardButton(c, callback_data=f"coin_in_{c}")]
                    for c in all_supported]
    coin_buttons.append([telegram.InlineKeyboardButton("← Cancel", callback_data="cmd_cancel")])
    w.bot.send_message(
        w.chat.id,
        "🔄 <b>Step 1:</b> Select the coin you want to <b>send</b>:",
        reply_markup=telegram.InlineKeyboardMarkup(coin_buttons)
    )
    cb = w._wait_for_callback(cancellable=True)
    if not cb or cb == "cmd_cancel":
        return
    coin_in = cb.replace("coin_in_", "")

    # Step 2: Choose coin to receive
    out_buttons = [[telegram.InlineKeyboardButton(c, callback_data=f"coin_out_{c}")]
                   for c in available if c != coin_in]
    out_buttons.append([telegram.InlineKeyboardButton("← Cancel", callback_data="cmd_cancel")])
    if not out_buttons:
        w.bot.send_message(w.chat.id, "No payout coins available after filtering. Contact owner.")
        return
    w.bot.send_message(
        w.chat.id,
        "🔄 <b>Step 2:</b> Select the coin you want to <b>receive</b>:",
        reply_markup=telegram.InlineKeyboardMarkup(out_buttons)
    )
    cb = w._wait_for_callback(cancellable=True)
    if not cb or cb == "cmd_cancel":
        return
    coin_out = cb.replace("coin_out_", "")

    # Step 3: Amount to send
    w.bot.send_message(
        w.chat.id,
        f"🔄 <b>Step 3:</b> Enter the amount of <b>{coin_in}</b> you want to send\n"
        f"(e.g. <code>0.005</code>):"
    )
    amount_str = w._wait_for_regex(r"([0-9]+(?:\.[0-9]+)?)", cancellable=True)
    if isinstance(amount_str, CancelSignal):
        return
    try:
        amount_in = float(amount_str)
    except ValueError:
        w.bot.send_message(w.chat.id, "Invalid amount. Please start over.")
        return

    # Fetch prices
    price_in  = mgr.get_price(coin_in)
    price_out = mgr.get_price(coin_out)
    if not price_in or not price_out:
        w.bot.send_message(
            w.chat.id,
            "⚠️ Could not fetch live rates right now. Please try again."
        )
        return

    spread = _get_spread()
    fiat_value    = amount_in * price_in
    fiat_after_spread = fiat_value * (1 - spread / 100)
    amount_out    = fiat_after_spread / price_out

    deposit_address = mgr.get_available_coins().get(coin_in, "")

    quote_text = (
        f"🔄 <b>Swap Quote</b>\n\n"
        f"You send:    <code>{amount_in:.8f} {coin_in}</code>\n"
        f"Rate {coin_in}: ${price_in:,.4f}\n"
        f"Rate {coin_out}: ${price_out:,.4f}\n"
        f"Service fee: {spread}%\n"
        f"You receive: <code>{amount_out:.8f} {coin_out}</code>\n\n"
        f"📬 Send <b>exactly</b> <code>{amount_in:.8f} {coin_in}</code> to:\n"
        f"<code>{deposit_address}</code>\n\n"
        f"After sending, press <b>I have sent</b> to notify the owner."
    )

    markup = telegram.InlineKeyboardMarkup([
        [telegram.InlineKeyboardButton("✅ I have sent", callback_data="swap_sent")],
        [telegram.InlineKeyboardButton("❌ Cancel",      callback_data="cmd_cancel")],
    ])
    w.bot.send_message(w.chat.id, quote_text, reply_markup=markup)

    cb = w._wait_for_callback(cancellable=True)
    if not cb or cb != "swap_sent":
        w.bot.send_message(w.chat.id, "Swap cancelled.")
        return

    # Record the swap as a transaction note
    import database as db
    note = (
        f"SWAP: {amount_in:.8f} {coin_in} → {amount_out:.8f} {coin_out} | "
        f"Spread={spread}% | {datetime.datetime.now().isoformat()}"
    )
    txn = db.Transaction(user=w.user, value=0, notes=note)
    w.session.add(txn)
    w.session.commit()

    # Notify owner
    owner = w.session.query(db.Admin).filter_by(is_owner=True).first()
    if owner:
        w.bot.send_message(
            owner.user_id,
            f"🔄 <b>Swap Request</b>\n"
            f"User: {w.user.mention()} (ID: {w.user.user_id})\n"
            f"Sends: {amount_in:.8f} {coin_in} → receives: {amount_out:.8f} {coin_out}\n"
            f"Their payout address will be collected next."
        )

    # Collect user's receive address
    w.bot.send_message(
        w.chat.id,
        f"✅ Payment noted!\n\nPlease send your <b>{coin_out}</b> receiving address:"
    )
    recv_addr = w._wait_for_regex(r"(.+)", cancellable=True)
    if isinstance(recv_addr, CancelSignal):
        w.bot.send_message(w.chat.id, "Swap payout address not provided. Contact support.")
        return

    if owner:
        w.bot.send_message(
            owner.user_id,
            f"📬 Payout address for above swap:\n<code>{recv_addr}</code>\n"
            f"Please send <code>{amount_out:.8f} {coin_out}</code> to this address."
        )

    w.bot.send_message(
        w.chat.id,
        f"🎉 <b>Swap submitted!</b>\n\n"
        f"You will receive <code>{amount_out:.8f} {coin_out}</code> at\n"
        f"<code>{recv_addr}</code>\n\n"
        f"The owner will process your swap shortly. Thank you!"
    )


def _show_swap_history(w) -> None:
    """Show recent swap transactions for this user."""
    import database as db

    txns = (
        w.session.query(db.Transaction)
        .filter(
            db.Transaction.user == w.user,
            db.Transaction.notes.like("SWAP:%"),
        )
        .order_by(db.Transaction.transaction_id.desc())
        .limit(10)
        .all()
    )
    if not txns:
        w.bot.send_message(w.chat.id, "📜 No swap history found.")
        return

    lines = ["📜 <b>Your Swap History</b>\n"]
    for txn in txns:
        lines.append(f"• {txn.notes}")
    w.bot.send_message(w.chat.id, "\n".join(lines))
