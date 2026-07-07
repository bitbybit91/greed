#!/usr/bin/env python3
"""
greed_cryptorefactor.py
=======================
A comprehensive refactoring, patching, and supervision script for the greed
Telegram shop bot (https://github.com/bitbybit91/greed/).

SETUP & RUN INSTRUCTIONS:
──────────────────────────────────────────────────────────────────────────────
1.  Navigate to or clone the greed repository:
        git clone https://github.com/bitbybit91/greed/ ./greed && cd greed

2.  Run this script (requires Python 3.8+ on Ubuntu 20.04+):
        python3 greed_cryptorefactor.py

    On the first run it will:
      • Create ./venv and install all dependencies
      • Run a syntax-diagnostic pass over every .py file
      • Write ./crypto_manager.py, ./woo_importer.py, ./modes/*.py
      • Patch worker.py (strip Stripe/CC, add crypto payment flow)
      • Patch database.py (add crypto/shipping/investment/swap tables)
      • Write config templates: ./config/crypto_addresses.toml,
                                ./config/mode_config.toml
      • Generate greed-crypto.service (systemd unit)
      • Start the 24/7 supervisor loop

3.  Configure your bot before starting:
        Edit ./config/config.toml          (bot token, owner ID, currency)
        Edit ./config/crypto_addresses.toml (your deposit wallet addresses)
        Edit ./config/mode_config.toml      (active mode: SHOP/INVESTMENT/SWAP)

4.  Optional — install as a systemd service (run as root or with sudo):
        python3 greed_cryptorefactor.py --install-systemd

OPTIONS:
  --setup-only        Run all setup steps but do not start the supervisor loop.
  --install-systemd   Write and install greed-crypto.service, then exit.
  --no-patch          Skip patching worker.py / database.py (idempotent re-run).
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import argparse
import compileall
import datetime
import json
import logging
import os
import py_compile
import re
import shutil
import signal
import subprocess
import sys
import textwrap
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ──────────────────────────── Logging Setup ────────────────────────────────
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

_log_fmt = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=_log_fmt,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(LOG_DIR / "refactor.log")),
    ],
)
log = logging.getLogger("greed_cryptorefactor")

# ──────────────────────────── Constants ────────────────────────────────────
REPO_URL = "https://github.com/bitbybit91/greed/"
VENV_DIR = Path("venv")
EXTRA_DEPS = [
    "python-telegram-bot==13.5",
    "requests>=2.28",
    "aiohttp>=3.8",
    "SQLAlchemy>=1.4,<2.0",
    "toml>=0.10",
    "lxml>=4.9",
    "APScheduler>=3.6,<4.0",   # 3.6.x is compatible with python-telegram-bot 13.5
    "qrcode>=7.3",
    "Pillow>=9.0",
]

# ════════════════════════════════════════════════════════════════════════════
#  PART 1 — ENVIRONMENT & REPO PREPARATION
# ════════════════════════════════════════════════════════════════════════════

def detect_repo_root() -> Path:
    """Detect or clone the greed repository. Returns the repo root path."""
    if (Path.cwd() / "worker.py").exists() and (Path.cwd() / "database.py").exists():
        log.info(f"Detected greed repo at: {Path.cwd()}")
        return Path.cwd()

    greed_path = Path.cwd() / "greed"
    if (greed_path / "worker.py").exists():
        log.info(f"Found greed repo at: {greed_path}")
        os.chdir(greed_path)
        return greed_path

    log.info(f"Cloning greed repository from {REPO_URL} …")
    result = subprocess.run(
        ["git", "clone", REPO_URL, str(greed_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        log.error(f"Failed to clone repository:\n{result.stderr}")
        sys.exit(1)
    os.chdir(greed_path)
    log.info(f"Repository cloned to: {greed_path}")
    return greed_path


def setup_venv() -> Path:
    """Create / verify Python virtualenv at ./venv. Returns path to venv python."""
    python_exe = VENV_DIR / "bin" / "python"
    if not VENV_DIR.exists():
        log.info("Creating Python virtualenv at ./venv …")
        result = subprocess.run(
            [sys.executable, "-m", "venv", str(VENV_DIR)],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            log.error(f"Failed to create venv:\n{result.stderr}")
            sys.exit(1)
        log.info("Virtualenv created.")
    else:
        log.info("Virtualenv already exists at ./venv")
    return python_exe


def install_dependencies(python_exe: Path) -> None:
    """Install all required dependencies inside the venv."""
    pip = VENV_DIR / "bin" / "pip"
    log.info("Upgrading pip …")
    subprocess.run([str(python_exe), "-m", "pip", "install", "--quiet",
                    "--upgrade", "pip"], check=False)

    if Path("requirements.txt").exists():
        log.info("Installing from requirements.txt …")
        r = subprocess.run([str(pip), "install", "--quiet", "-r", "requirements.txt"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            log.warning(f"requirements.txt partial failure:\n{r.stderr[:400]}")

    log.info("Installing extra dependencies …")
    r = subprocess.run([str(pip), "install", "--quiet"] + EXTRA_DEPS,
                       capture_output=True, text=True)
    if r.returncode != 0:
        log.warning(f"Extra deps partial failure:\n{r.stderr[:400]}")
    log.info("Dependency installation complete.")


def run_diagnostics() -> None:
    """Syntax-check every .py file; log errors to ./logs/diagnostics.log."""
    diag_log = LOG_DIR / "diagnostics.log"
    errors: List[str] = []
    with open(diag_log, "w") as f:
        f.write(f"Diagnostics — {datetime.datetime.now().isoformat()}\n{'='*60}\n\n")
        for py in sorted(Path(".").rglob("*.py")):
            if "venv" in py.parts or ".git" in py.parts:
                continue
            try:
                py_compile.compile(str(py), doraise=True)
                f.write(f"OK  {py}\n")
            except py_compile.PyCompileError as exc:
                msg = f"ERR {py}: {exc}"
                f.write(msg + "\n")
                errors.append(msg)
                log.warning(msg)
    if errors:
        log.warning(f"Diagnostics: {len(errors)} error(s) — see {diag_log}")
    else:
        log.info(f"Diagnostics: all files OK — see {diag_log}")


# ════════════════════════════════════════════════════════════════════════════
#  PART 2 / 3 / 4 — FILE CONTENTS (written to disk by write_all_files())
# ════════════════════════════════════════════════════════════════════════════

# ─── crypto_manager.py ──────────────────────────────────────────────────────
CRYPTO_MANAGER_PY = '''\
"""
crypto_manager.py
CryptoCurrency Payment Manager for greed bot.
Loads owner deposit addresses from config/crypto_addresses.toml,
fetches live rates from CoinGecko (60 s cache), and converts fiat totals
to exact crypto amounts.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
import toml

log = logging.getLogger(__name__)

# CoinGecko symbol → coin-id mapping (extend as needed)
COINGECKO_IDS: Dict[str, str] = {
    "BTC":  "bitcoin",
    "ETH":  "ethereum",
    "XMR":  "monero",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BNB":  "binancecoin",
    "LTC":  "litecoin",
    "DOGE": "dogecoin",
    "SOL":  "solana",
    "TRX":  "tron",
    "MATIC":"matic-network",
    "ADA":  "cardano",
}

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
CACHE_TTL = 60  # seconds


class CryptoPaymentManager:
    """Owner-configurable crypto deposit + rate-conversion engine."""

    def __init__(self, config_path: str = "config/crypto_addresses.toml"):
        self.config_path = Path(config_path)
        self.addresses: Dict[str, str] = {}
        # cache: key = "BTC_eur", value = (rate_float, unix_ts)
        self._cache: Dict[str, Tuple[float, float]] = {}
        self._fallback: Dict[str, float] = {}
        self.load_addresses()

    # ── Address Management ───────────────────────────────────────────────
    def load_addresses(self) -> None:
        """Reload addresses from the TOML config file."""
        if not self.config_path.exists():
            log.warning(f"Crypto addresses config not found: {self.config_path}")
            return
        try:
            cfg = toml.load(str(self.config_path))
            self.addresses = {k.upper(): v for k, v in cfg.get("addresses", {}).items()}
            log.info(f"Loaded {len(self.addresses)} crypto addresses: "
                     f"{list(self.addresses.keys())}")
        except Exception as exc:
            log.error(f"Failed to load crypto addresses: {exc}")

    def get_available_coins(self) -> List[str]:
        return [c for c in self.addresses if self.addresses[c]]

    # ── Rate Fetching ────────────────────────────────────────────────────
    def get_live_rate(self, coin: str, fiat: str = "eur") -> Optional[float]:
        """Return 1 <coin> in <fiat>. Uses 60 s cache; falls back to last known."""
        key = f"{coin.upper()}_{fiat.lower()}"
        # Cache hit
        cached = self._cache.get(key)
        if cached and (time.time() - cached[1]) < CACHE_TTL:
            return cached[0]
        # Fetch
        coin_id = COINGECKO_IDS.get(coin.upper())
        if not coin_id:
            log.warning(f"No CoinGecko ID for {coin}")
            return self._fallback.get(key)
        for attempt in range(3):
            try:
                resp = requests.get(
                    COINGECKO_URL,
                    params={"ids": coin_id, "vs_currencies": fiat.lower()},
                    timeout=10,
                )
                resp.raise_for_status()
                rate = float(resp.json()[coin_id][fiat.lower()])
                self._cache[key] = (rate, time.time())
                self._fallback[key] = rate
                return rate
            except Exception as exc:
                wait = 2 ** attempt
                log.warning(f"CoinGecko attempt {attempt+1} for {coin}: {exc} "
                             f"— retrying in {wait}s")
                time.sleep(wait)
        # Fallback
        fb = self._fallback.get(key)
        if fb:
            log.warning(f"Using cached fallback rate for {coin}: {fb}")
        return fb

    # ── Conversion ───────────────────────────────────────────────────────
    def fiat_to_crypto(
        self,
        fiat_cents: int,
        coin: str,
        currency_exp: int = 2,
        fiat: str = "eur",
    ) -> Optional[float]:
        """Convert fiat_cents (int, minimum units) to crypto float amount."""
        fiat_val = fiat_cents / (10 ** currency_exp)
        rate = self.get_live_rate(coin, fiat)
        if not rate:
            return None
        return round(fiat_val / rate, 8)

    # ── Payment Info ─────────────────────────────────────────────────────
    def get_payment_info(
        self,
        fiat_cents: int,
        coin: str,
        currency_exp: int = 2,
        fiat: str = "eur",
        currency_symbol: str = "€",
    ) -> Optional[dict]:
        """
        Returns a dict with all info needed to display a payment request:
          coin, address, amount, rate, fiat_amount, fiat_symbol,
          qr_string, display (HTML-formatted string)
        Returns None if the coin has no configured address or rate unavailable.
        """
        coin = coin.upper()
        address = self.addresses.get(coin)
        if not address:
            log.warning(f"No address configured for {coin}")
            return None
        amount = self.fiat_to_crypto(fiat_cents, coin, currency_exp, fiat)
        if amount is None:
            log.warning(f"Could not convert fiat to {coin}")
            return None
        rate = self.get_live_rate(coin, fiat)
        fiat_val = fiat_cents / (10 ** currency_exp)
        qr = f"{coin.lower()}:{address}?amount={amount}"
        display = (
            f"\\U0001f4b0 Send exactly: <code>{amount} {coin}</code>\\n"
            f"\\U0001f4eb To address: <code>{address}</code>\\n"
            f"\\U0001f4b6 Fiat equivalent: {currency_symbol}{fiat_val:.2f}\\n"
            f"\\U0001f4ca Rate: 1 {coin} = {currency_symbol}{rate:,.4f}\\n\\n"
            f"QR data: <code>{qr}</code>\\n\\n"
            f"\\u23f3 After sending, notify the owner to confirm your payment."
        )
        return {
            "coin": coin,
            "address": address,
            "amount": amount,
            "rate": rate,
            "fiat_amount": fiat_val,
            "fiat_symbol": currency_symbol,
            "qr_string": qr,
            "display": display,
        }

    # ── Confirmation Polling Stub ────────────────────────────────────────
    def poll_address_for_payment(
        self,
        coin: str,
        address: str,
        expected_amount: float,
        timeout_seconds: int = 1800,
    ) -> bool:
        """
        Stub for address-balance polling.
        Override or extend to call a block-explorer API for BTC/XMR/ETH.
        Returns True when payment is detected, False on timeout.
        """
        log.info(f"[poll_stub] Watching {coin} address {address[:12]}… "
                 f"for {expected_amount} {coin} (timeout={timeout_seconds}s)")
        # Real implementation would call e.g. blockchain.info / xmrchain.net APIs.
        # Disabled by default — owner uses manual confirmation button.
        return False
'''

# ─── modes/__init__.py ───────────────────────────────────────────────────────
MODES_INIT_PY = '''\
"""
modes/__init__.py — Mode management helpers for greed-crypto.
"""
from __future__ import annotations
import logging
import toml
from pathlib import Path

log = logging.getLogger(__name__)

MODE_CONFIG_PATH = Path("config/mode_config.toml")

VALID_MODES = ("SHOP_BOT", "INVESTMENT_BOT", "SWAP_BOT")


def get_active_mode() -> str:
    """Return the currently active bot mode (default: SHOP_BOT)."""
    if not MODE_CONFIG_PATH.exists():
        return "SHOP_BOT"
    try:
        cfg = toml.load(str(MODE_CONFIG_PATH))
        mode = cfg.get("active_mode", "SHOP_BOT").upper()
        return mode if mode in VALID_MODES else "SHOP_BOT"
    except Exception as exc:
        log.warning(f"Could not read mode config: {exc}")
        return "SHOP_BOT"


def set_active_mode(mode: str) -> None:
    """Persist the active mode to config/mode_config.toml."""
    mode = mode.upper()
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode: {mode}")
    cfg: dict = {}
    if MODE_CONFIG_PATH.exists():
        try:
            cfg = toml.load(str(MODE_CONFIG_PATH))
        except Exception:
            pass
    cfg["active_mode"] = mode
    MODE_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODE_CONFIG_PATH, "w") as fh:
        toml.dump(cfg, fh)
    log.info(f"Active mode set to {mode}")
'''

# ─── modes/shop_mode.py ──────────────────────────────────────────────────────
SHOP_MODE_PY = '''\
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
            "\\u26a0\\ufe0f No cryptocurrency addresses are configured. "
            "Please contact the shop owner.",
        )
        return None

    # Build coin-selection keyboard
    keyboard = [[telegram.KeyboardButton(c)] for c in coins]
    keyboard.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(
        w.chat.id,
        "\\U0001f4b0 <b>Select cryptocurrency to pay with:</b>",
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
            f"\\u274c Could not get rate for {coin}. Try another coin or contact support.",
        )
        return None

    # Show payment details
    w.bot.send_message(
        w.chat.id,
        "\\U0001f4cb <b>Payment Instructions</b>\\n\\n" + info["display"],
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )
    w.bot.send_message(
        w.chat.id,
        "\\u23f3 Waiting for the owner to confirm your payment. "
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
        "\\U0001f69a <b>Shipping Details</b>\\n\\nPlease provide the following information.",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )

    # Full name
    w.bot.send_message(w.chat.id, "\\U0001f464 Full name:", reply_markup=cancel_kb)
    name = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if hasattr(name, "__class__") and name.__class__.__name__ == "CancelSignal":
        return None

    # Delivery address
    w.bot.send_message(w.chat.id, "\\U0001f3e0 Delivery address (street, city, country):",
                       reply_markup=cancel_kb)
    address = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if hasattr(address, "__class__") and address.__class__.__name__ == "CancelSignal":
        return None

    # Phone
    w.bot.send_message(w.chat.id, "\\U0001f4f1 Phone number:", reply_markup=cancel_kb)
    phone = w._Worker__wait_for_regex(r"(\\+?[0-9\\s\\-]{7,})", cancellable=True)
    if hasattr(phone, "__class__") and phone.__class__.__name__ == "CancelSignal":
        return None

    # Notes
    skip_kb = telegram.InlineKeyboardMarkup(
        [[telegram.InlineKeyboardButton("Skip", callback_data="cmd_cancel")]]
    )
    w.bot.send_message(w.chat.id, "\\U0001f4dd Additional notes (or press Skip):",
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
        "\\U0001f6d2 <b>NEW ORDER — Crypto Payment</b>",
        f"\\U0001f464 Customer: {w.user.mention()} (ID {w.user.user_id})",
        f"\\U0001f4e6 Order #: {order.order_id}",
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

    msg = "\\n".join(lines)
    for admin in admins:
        try:
            w.bot.send_message(admin.user_id, msg, parse_mode="HTML")
        except Exception as exc:
            log.warning(f"Could not notify admin {admin.user_id}: {exc}")
'''

# ─── modes/investment_mode.py ────────────────────────────────────────────────
INVESTMENT_MODE_PY = '''\
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

    while True:
        keyboard = [
            [telegram.KeyboardButton("\\U0001f4c8 View Plans")],
            [telegram.KeyboardButton("\\U0001f4b0 My Balance")],
            [telegram.KeyboardButton("\\U0001f4e4 Deposit")],
            [telegram.KeyboardButton("\\U0001f4e5 Withdraw")],
            [telegram.KeyboardButton(w.loc.get("menu_cancel"))],
        ]
        w.bot.send_message(
            w.chat.id,
            "\\U0001f4bc <b>Investment Portal</b>\\nSelect an option:",
            parse_mode="HTML",
            reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
        )
        sel = w._Worker__wait_for_specific_message(
            ["\\U0001f4c8 View Plans", "\\U0001f4b0 My Balance",
             "\\U0001f4e4 Deposit", "\\U0001f4e5 Withdraw"],
            cancellable=True,
        )
        if hasattr(sel, "__class__") and sel.__class__.__name__ == "CancelSignal":
            return
        if sel == "\\U0001f4c8 View Plans":
            _show_plans(w)
        elif sel == "\\U0001f4b0 My Balance":
            _show_balance(w)
        elif sel == "\\U0001f4e4 Deposit":
            _deposit_flow(w)
        elif sel == "\\U0001f4e5 Withdraw":
            _withdraw_flow(w)


def _show_plans(w: "_w.Worker") -> None:
    import telegram
    lines = ["\\U0001f4ca <b>Investment Plans</b>\\n"]
    for p in DEFAULT_PLANS:
        roi = p["roi_pct"]
        days = p["days"]
        lines.append(
            f"<b>{p['name']}</b>\\n"
            f"  Min: ${p['min_usd']}  |  ROI: {roi}%  |  Duration: {days} days\\n"
            f"  Return: ${p['min_usd'] * (1 + roi/100):.2f} after {days} days\\n"
        )
    w.bot.send_message(w.chat.id, "\\n".join(lines), parse_mode="HTML",
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
    lines = ["\\U0001f4b0 <b>My Investments</b>\\n"]
    for d in deposits:
        status = "Active" if not d.paid_out else "\\u2705 Completed"
        lines.append(
            f"#{d.id} | {d.coin} {d.amount:.6f} | "
            f"Plan: {d.plan_name} | {status}\\n"
            f"  Deposited: {d.created_at.strftime('%Y-%m-%d')}"
        )
    w.bot.send_message(w.chat.id, "\\n".join(lines), parse_mode="HTML",
                       reply_markup=telegram.ReplyKeyboardRemove())


def _deposit_flow(w: "_w.Worker") -> None:
    import telegram
    import database as db
    from crypto_manager import CryptoPaymentManager

    mgr: CryptoPaymentManager = w._crypto_manager()
    coins = mgr.get_available_coins()
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
    if hasattr(plan_sel, "__class__") and plan_sel.__class__.__name__ == "CancelSignal":
        return
    plan = next(p for p in DEFAULT_PLANS if p["name"] == plan_sel)

    # Select coin
    kb2 = [[telegram.KeyboardButton(c)] for c in coins]
    kb2.append([telegram.KeyboardButton(w.loc.get("menu_cancel"))])
    w.bot.send_message(w.chat.id, "Select coin to deposit:",
                       reply_markup=telegram.ReplyKeyboardMarkup(kb2, one_time_keyboard=True))
    coin_sel = w._Worker__wait_for_specific_message(coins, cancellable=True)
    if hasattr(coin_sel, "__class__") and coin_sel.__class__.__name__ == "CancelSignal":
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
        f"\\U0001f4b0 <b>Investment Deposit</b>\\n\\n"
        f"Plan: <b>{plan['name']}</b> | ROI: {plan['roi_pct']}% in {plan['days']} days\\n\\n"
        f"Send at least <code>{min_crypto} {coin_sel}</code>\\n"
        f"To: <code>{address}</code>\\n\\n"
        f"After sending, enter your transaction ID below.",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )
    tx = w._Worker__wait_for_regex(r"(.+)", cancellable=True)
    if hasattr(tx, "__class__") and tx.__class__.__name__ == "CancelSignal":
        return

    # Store pending deposit
    dep = db.InvestmentDeposit(
        user_id=w.user.user_id,
        coin=coin_sel.upper(),
        amount=min_crypto,
        plan_name=plan["name"],
        roi_pct=plan["roi_pct"],
        duration_days=plan["days"],
        tx_ref=str(tx).strip(),
        paid_out=False,
        created_at=datetime.datetime.now(),
    )
    w.session.add(dep)
    w.session.commit()
    w.bot.send_message(
        w.chat.id,
        "\\u2705 Deposit request recorded! The owner will verify and activate your plan.",
    )


def _withdraw_flow(w: "_w.Worker") -> None:
    import telegram
    w.bot.send_message(
        w.chat.id,
        "\\U0001f4e5 <b>Withdrawal Request</b>\\n\\n"
        "Please provide your withdrawal address and amount:\\n"
        "Format: <code>COIN ADDRESS AMOUNT</code>\\n"
        "Example: <code>BTC bc1qxxx 0.01</code>",
        parse_mode="HTML",
        reply_markup=telegram.ReplyKeyboardRemove(),
    )
    reply = w._Worker__wait_for_regex(r"(\\S+ \\S+ [0-9.]+)", cancellable=True)
    if hasattr(reply, "__class__") and reply.__class__.__name__ == "CancelSignal":
        return
    parts = str(reply).strip().split()
    if len(parts) != 3:
        w.bot.send_message(w.chat.id, "\\u274c Invalid format. Please try again.")
        return
    coin, addr, amount = parts
    w.bot.send_message(
        w.chat.id,
        f"\\u23f3 Withdrawal request for {amount} {coin.upper()} to\\n"
        f"<code>{addr}</code>\\nsubmitted. Owner will process it shortly.",
        parse_mode="HTML",
    )
    # Notify admins
    import database as db
    admins = w.session.query(db.Admin).filter_by(receive_orders=True).all()
    for admin in admins:
        try:
            w.bot.send_message(
                admin.user_id,
                f"\\U0001f4e5 <b>Withdrawal Request</b>\\n"
                f"User: {w.user.mention()} ({w.user.user_id})\\n"
                f"Coin: {coin.upper()}\\nAmount: {amount}\\nAddress: {addr}",
                parse_mode="HTML",
            )
        except Exception as exc:
            log.warning(f"Could not notify admin {admin.user_id}: {exc}")
'''

# ─── modes/swap_mode.py ──────────────────────────────────────────────────────
SWAP_MODE_PY = '''\
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
        "\\U0001f504 <b>Crypto Swap</b>\\n\\nSelect coin to <b>send</b> (coin-in):",
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
        f"How much <b>{coin_in}</b> do you want to swap?\\n"
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
        w.bot.send_message(w.chat.id, "\\u274c Could not fetch live rates. Try again later.")
        return

    fiat_val = amount_in * rate_in
    amount_out_gross = fiat_val / rate_out
    amount_out_net = round(amount_out_gross * (1 - spread_pct / 100), 8)
    cs = w.cfg["Payments"].get("currency_symbol", "€")

    quote_msg = (
        f"\\U0001f4cb <b>Swap Quote</b>\\n\\n"
        f"Send:    <code>{amount_in} {coin_in}</code> (≈ {cs}{fiat_val:.2f})\\n"
        f"Receive: <code>{amount_out_net} {coin_out}</code>\\n"
        f"Spread:  {spread_pct}%\\n\\n"
        f"Deposit address for <b>{coin_in}</b>:\\n"
        f"<code>{mgr.addresses.get(coin_in.upper(), 'N/A')}</code>\\n\\n"
        f"After depositing, send your transaction ID below."
    )
    w.bot.send_message(w.chat.id, quote_msg, parse_mode="HTML")

    # Confirm or cancel
    confirm_kb = telegram.ReplyKeyboardMarkup(
        [["\\u2705 Confirm Swap"], [w.loc.get("menu_cancel")]],
        one_time_keyboard=True,
    )
    w.bot.send_message(w.chat.id, "Proceed with this swap?", reply_markup=confirm_kb)
    confirm = w._Worker__wait_for_specific_message(
        ["\\u2705 Confirm Swap"], cancellable=True)
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
        f"\\u23f3 Swap request submitted!\\n"
        f"You will receive <b>{amount_out_net} {coin_out}</b> "
        f"to your wallet after the owner processes your deposit.",
        parse_mode="HTML",
    )

    # Notify admins
    import database as db
    admins = w.session.query(db.Admin).filter_by(receive_orders=True).all()
    swap_msg = (
        f"\\U0001f504 <b>Swap Request</b>\\n"
        f"User: {w.user.mention()} ({w.user.user_id})\\n"
        f"Coin-in: {amount_in} {coin_in}\\n"
        f"Coin-out: {amount_out_net} {coin_out}\\n"
        f"TX ref: {str(tx).strip()}\\n"
        f"Deposit address: {mgr.addresses.get(coin_in.upper(), 'N/A')}"
    )
    for admin in admins:
        try:
            w.bot.send_message(admin.user_id, swap_msg, parse_mode="HTML")
        except Exception as exc:
            log.warning(f"Could not notify admin {admin.user_id}: {exc}")
'''

# ─── woo_importer.py ─────────────────────────────────────────────────────────
WOO_IMPORTER_PY = '''\
"""
woo_importer.py
WooCommerceXMLImporter — parse a WordPress/WooCommerce product-export XML
and upsert products into the greed database.
"""
from __future__ import annotations

import logging
import requests
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from lxml import etree

if TYPE_CHECKING:
    import database as db

log = logging.getLogger(__name__)

# WooCommerce RSS/XML namespaces
NS = {
    "wp":      "http://wordpress.org/export/1.2/",
    "wc":      "http://www.woothemes.com/woo-commerce/",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "excerpt": "http://wordpress.org/export/1.2/excerpt/",
}


class WooCommerceXMLImporter:
    """
    Parse a WooCommerce product-export XML file and import/update products
    in the greed database.

    Usage:
        importer = WooCommerceXMLImporter(session, xml_path="products.xml")
        count = importer.import_products()
    """

    def __init__(self, session, xml_path: str = "products.xml"):
        self.session = session
        self.xml_path = Path(xml_path)

    # ── Public API ────────────────────────────────────────────────────────
    def import_products(self) -> int:
        """Parse XML and upsert products. Returns number of products processed."""
        if not self.xml_path.exists():
            log.error(f"XML file not found: {self.xml_path}")
            return 0
        try:
            tree = etree.parse(str(self.xml_path))
        except etree.XMLSyntaxError as exc:
            log.error(f"XML parse error: {exc}")
            return 0

        root = tree.getroot()
        items = root.findall(".//item")
        count = 0
        for item in items:
            post_type = self._get_text(item, "wp:post_type")
            if post_type != "product":
                continue
            try:
                self._process_item(item)
                count += 1
            except Exception as exc:
                log.warning(f"Skipped item: {exc}")
        self.session.commit()
        log.info(f"WooCommerce import complete: {count} products processed")
        return count

    # ── Private Helpers ───────────────────────────────────────────────────
    def _process_item(self, item) -> None:
        import database as db

        title = self._get_text(item, "title") or "Unnamed Product"
        description = (
            self._get_text(item, "content:encoded")
            or self._get_text(item, "excerpt:encoded")
            or ""
        )
        # Strip HTML tags from description safely (no string-concatenation injection)
        if description:
            try:
                from html.parser import HTMLParser as _HTMLParser
                class _Stripper(_HTMLParser):
                    def __init__(self):
                        super().__init__()
                        self._parts: list = []
                    def handle_data(self, data: str) -> None:
                        self._parts.append(data)
                    def get_text(self) -> str:
                        return "".join(self._parts).strip()
                stripper = _Stripper()
                stripper.feed(description)
                description = stripper.get_text()
            except Exception:
                description = ""

        # Price from _regular_price or _price meta
        price_str = (
            self._get_meta(item, "_regular_price")
            or self._get_meta(item, "_price")
            or "0"
        )
        try:
            price_float = float(price_str.replace(",", "."))
            # Convert to minimum units (cents), default exp=2
            price_cents = int(price_float * 100)
        except ValueError:
            price_cents = 0

        # SKU
        sku = self._get_meta(item, "_sku") or ""

        # Image URL
        image_url = self._get_text(item, "wp:attachment_url") or ""

        # Check if product already exists by name
        existing: Optional[db.Product] = (
            self.session.query(db.Product)
            .filter_by(name=title, deleted=False)
            .one_or_none()
        )
        if existing:
            existing.description = description[:500] if description else existing.description
            existing.price = price_cents if price_cents > 0 else existing.price
            log.debug(f"Updated product: {title}")
        else:
            product = db.Product(
                name=title[:255],
                description=(description[:500] if description else ""),
                price=price_cents if price_cents > 0 else None,
                deleted=False,
            )
            self.session.add(product)
            log.debug(f"Added product: {title}")
            existing = product

        # Optionally download product image
        if image_url and existing.image is None:
            try:
                r = requests.get(image_url, timeout=10)
                r.raise_for_status()
                existing.image = r.content
                log.debug(f"Downloaded image for: {title}")
            except Exception as exc:
                log.warning(f"Could not download image for {title}: {exc}")

    def _get_text(self, element, tag: str) -> Optional[str]:
        """Find element text, resolving namespace prefixes from NS dict."""
        if ":" in tag:
            prefix, local = tag.split(":", 1)
            ns = NS.get(prefix, "")
            el = element.find(f"{{{ns}}}{local}" if ns else local)
        else:
            el = element.find(tag)
        return el.text.strip() if el is not None and el.text else None

    def _get_meta(self, item, meta_key: str) -> Optional[str]:
        """Extract a WooCommerce _meta value by key."""
        ns = NS.get("wp", "")
        for meta in item.findall(f"{{{ns}}}postmeta"):
            key_el = meta.find(f"{{{ns}}}meta_key")
            val_el = meta.find(f"{{{ns}}}meta_value")
            if key_el is not None and key_el.text == meta_key:
                return val_el.text.strip() if val_el is not None and val_el.text else ""
        return None
'''

# ─── config/crypto_addresses.toml (template) ─────────────────────────────────
CRYPTO_ADDRESSES_TOML = """\
# config/crypto_addresses.toml
# Owner deposit addresses for cryptocurrency payments.
# Key = coin symbol (uppercase), Value = your wallet address.
# Leave value empty ("") to disable that coin.

[addresses]
BTC  = ""   # Bitcoin
ETH  = ""   # Ethereum
XMR  = ""   # Monero
USDT = ""   # Tether (ERC-20 or TRC-20 — specify chain in notes)
USDC = ""   # USD Coin
LTC  = ""   # Litecoin
DOGE = ""   # Dogecoin
"""

# ─── config/mode_config.toml (template) ──────────────────────────────────────
MODE_CONFIG_TOML = """\
# config/mode_config.toml
# Active bot mode. Owner can switch via the Telegram admin panel.
# Valid values: SHOP_BOT | INVESTMENT_BOT | SWAP_BOT

active_mode = "SHOP_BOT"

# Spread percentage charged on swaps (SWAP_BOT mode only)
swap_spread_pct = 1.5

# Enable auto address-polling for BTC/XMR confirmation (experimental)
enable_address_polling = false
"""

# ─── systemd unit template ───────────────────────────────────────────────────
SYSTEMD_UNIT_TEMPLATE = """\
[Unit]
Description=greed-crypto Telegram Bot (supervised by greed_cryptorefactor)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User={user}
WorkingDirectory={workdir}
ExecStart={python} {script}
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=greed-crypto
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
"""


# ════════════════════════════════════════════════════════════════════════════
#  PART 2 — PATCH worker.py  (strip CC, add crypto)
# ════════════════════════════════════════════════════════════════════════════

# Replacement for __add_credit_menu (no CC option)
_NEW_ADD_CREDIT_MENU = '''\
    def __add_credit_menu(self):
        """Add more credit to the account (crypto only)."""
        log.debug("Displaying __add_credit_menu")
        keyboard = []
        if self.cfg["Payments"]["Cash"]["enable_pay_with_cash"]:
            keyboard.append([telegram.KeyboardButton(self.loc.get("menu_cash"))])
        keyboard.append([telegram.KeyboardButton("\\U0001f4b0 Pay with Crypto")])
        keyboard.append([telegram.KeyboardButton(self.loc.get("menu_cancel"))])
        self.bot.send_message(
            self.chat.id,
            self.loc.get("conversation_payment_method"),
            reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
        )
        selection = self.__wait_for_specific_message(
            [self.loc.get("menu_cash"), "\\U0001f4b0 Pay with Crypto",
             self.loc.get("menu_cancel")],
            cancellable=True,
        )
        if selection == self.loc.get("menu_cash") and \\
                self.cfg["Payments"]["Cash"]["enable_pay_with_cash"]:
            self.bot.send_message(
                self.chat.id,
                self.loc.get("payment_cash", user_cash_id=self.user.identifiable_str()),
            )
        elif selection == "\\U0001f4b0 Pay with Crypto":
            self.__add_credit_crypto()
        # CancelSignal or menu_cancel → return silently

'''

# New methods to inject into worker.py (before __bot_info)
_NEW_WORKER_METHODS = '''\
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
        # Ask how much to top up
        cancel = telegram.InlineKeyboardMarkup(
            [[telegram.InlineKeyboardButton(self.loc.get("menu_cancel"),
                                            callback_data="cmd_cancel")]]
        )
        self.bot.send_message(
            self.chat.id,
            "\\U0001f4b0 How much would you like to add to your wallet?\\n"
            f"Enter amount in {self.cfg['Payments']['currency']} "
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

        # Coin selection
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
            currency_symbol=self.cfg["Payments"].get("currency_symbol", "€"),
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
        # Record a pending transaction (value = 0 until owner confirms)
        transaction = db.Transaction(
            user=self.user,
            value=0,
            provider=f"Crypto:{info['coin']}",
            notes=(
                f"PENDING | {info['coin']} {info['amount']} | "
                f"addr:{info['address']} | tx:{str(tx_id).strip()}"
            ),
        )
        self.session.add(transaction)
        self.session.commit()
        self.bot.send_message(
            self.chat.id,
            "\\u2705 Payment submitted for review. The owner will confirm "
            "and credit your wallet shortly.",
        )
        # Notify admins
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
                    f"Coin: {info['coin']} {info['amount']}\\n"
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

'''


def _replace_method(content: str, method_name: str, new_body: str) -> str:
    """Replace a single 4-space-indented method in a class with new_body."""
    pattern = rf"(    def {re.escape(method_name)}\b.*?)(?=\n    def |\Z)"
    m = re.search(pattern, content, re.DOTALL)
    if m:
        return content[: m.start()] + new_body + content[m.end():]
    log.warning(f"  Method not found for replacement: {method_name}")
    return content


def _remove_method(content: str, method_name: str) -> str:
    """Remove a 4-space-indented method entirely."""
    return _replace_method(content, method_name, "")


def patch_worker_py(no_patch: bool = False) -> None:
    """Apply all crypto-related patches to worker.py."""
    if no_patch:
        log.info("Skipping worker.py patch (--no-patch)")
        return

    target = Path("worker.py")
    backup = Path("worker.py.bak")
    if not target.exists():
        log.error("worker.py not found — cannot patch.")
        return

    # Idempotency guard: check if already patched
    original = target.read_text(encoding="utf-8")
    if "# GREED_CRYPTO_PATCHED" in original:
        log.info("worker.py already patched — skipping.")
        return

    # Backup
    if not backup.exists():
        shutil.copy2(target, backup)
        log.info(f"Backup: {backup}")

    content = original

    # 1 — Add imports after "import nuconfig"
    crypto_imports = (
        "\n# ── greed-crypto additions ──────────────────────────────────────────\n"
        "try:\n"
        "    import toml as _toml\n"
        "    from crypto_manager import CryptoPaymentManager as _CryptoPaymentManager\n"
        "except ImportError:\n"
        "    _CryptoPaymentManager = None\n"
        "try:\n"
        "    import modes as _modes_pkg\n"
        "except ImportError:\n"
        "    _modes_pkg = None\n"
        "# GREED_CRYPTO_PATCHED\n"
        "# ─────────────────────────────────────────────────────────────────────\n"
    )
    if "import nuconfig" in content:
        content = content.replace("import nuconfig\n",
                                  "import nuconfig\n" + crypto_imports, 1)

    # 2 — Init self._crypto_mgr in Worker.__init__ (after invoice_payload line)
    init_addition = "        # greed-crypto: crypto payment manager\n        self._crypto_mgr = None\n"
    old_inv_line = "        self.invoice_payload = None\n"
    if old_inv_line in content and "self._crypto_mgr" not in content:
        content = content.replace(
            old_inv_line,
            old_inv_line + init_addition,
            1,
        )

    # 3 — Remove credit-card-only methods
    for m in ("__wait_for_precheckoutquery", "__wait_for_successfulpayment",
              "__add_credit_cc", "__make_payment", "__get_total_fee"):
        content = _remove_method(content, m)

    # 4 — Replace __add_credit_menu
    content = _replace_method(content, "__add_credit_menu", _NEW_ADD_CREDIT_MENU)

    # 5 — Inject new methods before __bot_info
    bot_info_sig = "    def __bot_info(self):\n"
    if bot_info_sig in content and "__add_credit_crypto" not in content:
        content = content.replace(bot_info_sig,
                                  _NEW_WORKER_METHODS + bot_info_sig, 1)

    # 6 — Extend admin menu: add Mode Panel + Crypto buttons for owner
    old_admin_mode_line = (
        "            if self.admin.is_owner:\n"
        "                keyboard.append([self.loc.get(\"menu_edit_admins\")])\n"
    )
    new_admin_mode_lines = (
        "            if self.admin.is_owner:\n"
        "                keyboard.append([self.loc.get(\"menu_edit_admins\")])\n"
        "                keyboard.append([\"\\U0001f916 Bot Mode\"])\n"
        "                keyboard.append([\"\\U0001f4b0 Crypto Addresses\"])\n"
        "                keyboard.append([\"\\U0001f4e6 Import Products (WooCommerce)\"])\n"
    )
    if old_admin_mode_line in content and "Bot Mode" not in content:
        content = content.replace(old_admin_mode_line, new_admin_mode_lines, 1)

    # 6b — Add handling for the new admin buttons in the admin menu loop
    old_admin_elif = (
        "            # If the user has selected the Transactions option"
        " and has the privileges to perform the action...\n"
        "            elif selection == self.loc.get(\"menu_csv\")"
        " and self.admin.create_transactions:\n"
        "                # Generate the .csv file\n"
        "                self.__transactions_file()\n"
    )
    new_admin_elif = (
        "            # If the user has selected the Transactions option"
        " and has the privileges to perform the action...\n"
        "            elif selection == self.loc.get(\"menu_csv\")"
        " and self.admin.create_transactions:\n"
        "                # Generate the .csv file\n"
        "                self.__transactions_file()\n"
        "            elif selection == \"\\U0001f916 Bot Mode\" and self.admin.is_owner:\n"
        "                self.__admin_mode_panel()\n"
        "            elif selection == \"\\U0001f4b0 Crypto Addresses\" and self.admin.is_owner:\n"
        "                self.__admin_reload_crypto()\n"
        "            elif selection == \"\\U0001f4e6 Import Products (WooCommerce)\" and self.admin.is_owner:\n"
        "                self.__admin_woo_import()\n"
    )
    if old_admin_elif in content and "__admin_mode_panel" not in content:
        content = content.replace(old_admin_elif, new_admin_elif, 1)

    # 7 — Extend user menu with mode-aware buttons
    old_user_menu_keys = (
        "            keyboard = [[telegram.KeyboardButton(self.loc.get(\"menu_order\"))],\n"
        "                        [telegram.KeyboardButton(self.loc.get(\"menu_order_status\"))],\n"
        "                        [telegram.KeyboardButton(self.loc.get(\"menu_add_credit\"))],\n"
        "                        [telegram.KeyboardButton(self.loc.get(\"menu_language\"))],\n"
        "                        [telegram.KeyboardButton(self.loc.get(\"menu_help\")),\n"
        "                         telegram.KeyboardButton(self.loc.get(\"menu_bot_info\"))]]\n"
    )
    new_user_menu_keys = (
        "            # greed-crypto: mode-aware user menu\n"
        "            _active_mode = \"SHOP_BOT\"\n"
        "            try:\n"
        "                import modes as _m; _active_mode = _m.get_active_mode()\n"
        "            except ImportError:\n"
        "                pass\n"
        "            keyboard = []\n"
        "            if _active_mode == \"SHOP_BOT\":\n"
        "                keyboard = [[telegram.KeyboardButton(self.loc.get(\"menu_order\"))],\n"
        "                             [telegram.KeyboardButton(self.loc.get(\"menu_order_status\"))]]\n"
        "            elif _active_mode == \"INVESTMENT_BOT\":\n"
        "                keyboard = [[telegram.KeyboardButton(\"\\U0001f4bc Investment Portal\")]]\n"
        "            elif _active_mode == \"SWAP_BOT\":\n"
        "                keyboard = [[telegram.KeyboardButton(\"\\U0001f504 Swap Crypto\")]]\n"
        "            keyboard += [\n"
        "                [telegram.KeyboardButton(self.loc.get(\"menu_add_credit\"))],\n"
        "                [telegram.KeyboardButton(self.loc.get(\"menu_language\"))],\n"
        "                [telegram.KeyboardButton(self.loc.get(\"menu_help\")),\n"
        "                 telegram.KeyboardButton(self.loc.get(\"menu_bot_info\"))],\n"
        "            ]\n"
    )
    if old_user_menu_keys in content and "_active_mode" not in content:
        content = content.replace(old_user_menu_keys, new_user_menu_keys, 1)

    # 7b — Add handling for mode buttons in user menu loop
    old_user_elif_help = (
        "            # If the user has selected the Help option...\n"
        "            elif selection == self.loc.get(\"menu_help\"):\n"
        "                # Go to the Help menu\n"
        "                self.__help_menu()\n"
    )
    new_user_elif_help = (
        "            # If the user has selected the Help option...\n"
        "            elif selection == self.loc.get(\"menu_help\"):\n"
        "                # Go to the Help menu\n"
        "                self.__help_menu()\n"
        "            elif selection == \"\\U0001f4bc Investment Portal\":\n"
        "                try:\n"
        "                    from modes.investment_mode import run_investment_menu\n"
        "                    run_investment_menu(self)\n"
        "                except ImportError:\n"
        "                    self.bot.send_message(self.chat.id, \"Investment mode unavailable.\")\n"
        "            elif selection == \"\\U0001f504 Swap Crypto\":\n"
        "                try:\n"
        "                    from modes.swap_mode import run_swap_menu\n"
        "                    run_swap_menu(self)\n"
        "                except ImportError:\n"
        "                    self.bot.send_message(self.chat.id, \"Swap mode unavailable.\")\n"
    )
    if old_user_elif_help in content and "run_investment_menu" not in content:
        content = content.replace(old_user_elif_help, new_user_elif_help, 1)

    target.write_text(content, encoding="utf-8")
    log.info("worker.py patched successfully.")


# ════════════════════════════════════════════════════════════════════════════
#  PART 2 (cont.) — PATCH database.py  (add new tables)
# ════════════════════════════════════════════════════════════════════════════

_NEW_DB_TABLES = '''\

# ── greed-crypto additional tables ──────────────────────────────────────────

class CryptoDeposit(TableDeclarativeBase):
    """A pending or confirmed cryptocurrency deposit."""
    __tablename__ = "crypto_deposits"

    id          = Column(Integer, primary_key=True)
    user_id     = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    user        = relationship("User")
    coin        = Column(String, nullable=False)
    address     = Column(String, nullable=False)
    amount      = Column(String, nullable=False)   # crypto units (string for precision)
    fiat_amount = Column(String)                   # fiat snapshot at time of request
    tx_ref      = Column(Text)                     # user-supplied tx hash
    confirmed   = Column(Boolean, default=False)
    created_at  = Column(DateTime, nullable=False)
    confirmed_at = Column(DateTime)

    def __repr__(self):
        return f"<CryptoDeposit {self.id} {self.coin} confirmed={self.confirmed}>"


class ShippingDetails(TableDeclarativeBase):
    """Shipping information collected after a crypto shop order."""
    __tablename__ = "shipping_details"

    id         = Column(Integer, primary_key=True)
    order_id   = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    order      = relationship("Order")
    name       = Column(String)
    address    = Column(Text)
    phone      = Column(String)
    notes      = Column(Text)
    created_at = Column(DateTime)

    def __repr__(self):
        return f"<ShippingDetails order={self.order_id}>"


class InvestmentDeposit(TableDeclarativeBase):
    """A user investment deposit under a specific plan."""
    __tablename__ = "investment_deposits"

    id            = Column(Integer, primary_key=True)
    user_id       = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    user          = relationship("User")
    coin          = Column(String, nullable=False)
    amount        = Column(String, nullable=False)   # crypto units string
    plan_name     = Column(String)
    roi_pct       = Column(Integer)
    duration_days = Column(Integer)
    tx_ref        = Column(Text)
    paid_out      = Column(Boolean, default=False)
    created_at    = Column(DateTime, nullable=False)
    payout_date   = Column(DateTime)

    def __repr__(self):
        return f"<InvestmentDeposit {self.id} {self.coin} plan={self.plan_name}>"


class SwapRequest(TableDeclarativeBase):
    """A user swap request (coin-in → coin-out)."""
    __tablename__ = "swap_requests"

    id           = Column(Integer, primary_key=True)
    user_id      = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    user         = relationship("User")
    coin_in      = Column(String, nullable=False)
    amount_in    = Column(String, nullable=False)
    coin_out     = Column(String, nullable=False)
    amount_out   = Column(String, nullable=False)
    spread_pct   = Column(String)
    deposit_addr = Column(String)
    tx_ref       = Column(Text)
    status       = Column(String, default="pending")  # pending / completed / cancelled
    created_at   = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<SwapRequest {self.id} {self.coin_in}->{self.coin_out}>"

# ────────────────────────────────────────────────────────────────────────────
'''


def patch_database_py(no_patch: bool = False) -> None:
    """Append new table definitions to database.py."""
    if no_patch:
        log.info("Skipping database.py patch (--no-patch)")
        return

    target = Path("database.py")
    backup = Path("database.py.bak")
    if not target.exists():
        log.error("database.py not found — cannot patch.")
        return

    original = target.read_text(encoding="utf-8")
    if "# GREED_CRYPTO_DB_PATCHED" in original:
        log.info("database.py already patched — skipping.")
        return

    if not backup.exists():
        shutil.copy2(target, backup)
        log.info(f"Backup: {backup}")

    new_content = original.rstrip() + "\n\n# GREED_CRYPTO_DB_PATCHED\n" + _NEW_DB_TABLES
    target.write_text(new_content, encoding="utf-8")
    log.info("database.py patched (new tables added).")


# ════════════════════════════════════════════════════════════════════════════
#  PART 4 — WRITE ALL MODULE FILES
# ════════════════════════════════════════════════════════════════════════════

def write_all_files() -> None:
    """Write crypto_manager.py, mode modules, config templates, etc."""

    files: Dict[str, str] = {
        "crypto_manager.py":           CRYPTO_MANAGER_PY,
        "modes/__init__.py":           MODES_INIT_PY,
        "modes/shop_mode.py":          SHOP_MODE_PY,
        "modes/investment_mode.py":    INVESTMENT_MODE_PY,
        "modes/swap_mode.py":          SWAP_MODE_PY,
        "woo_importer.py":             WOO_IMPORTER_PY,
        "config/crypto_addresses.toml": CRYPTO_ADDRESSES_TOML,
        "config/mode_config.toml":     MODE_CONFIG_TOML,
    }

    for rel_path, content in files.items():
        path = Path(rel_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            log.info(f"  exists (skipping): {rel_path}")
        else:
            path.write_text(content, encoding="utf-8")
            log.info(f"  wrote: {rel_path}")

    log.info("All module files written.")


# ════════════════════════════════════════════════════════════════════════════
#  PART 7 — SYSTEMD UNIT + SUPERVISOR
# ════════════════════════════════════════════════════════════════════════════

def write_systemd_unit() -> Path:
    """Write the greed-crypto.service file to the current directory."""
    import getpass
    unit_path = Path("greed-crypto.service")
    unit_content = SYSTEMD_UNIT_TEMPLATE.format(
        user=getpass.getuser(),
        workdir=str(Path.cwd().resolve()),
        python=str((VENV_DIR / "bin" / "python").resolve()),
        script=str(Path(__file__).resolve()),
    )
    unit_path.write_text(unit_content, encoding="utf-8")
    log.info(f"Systemd unit written: {unit_path.resolve()}")
    return unit_path


def install_systemd_unit() -> None:
    """Install and enable the systemd service (requires root / sudo)."""
    unit_src = write_systemd_unit()
    unit_dst = Path("/etc/systemd/system/greed-crypto.service")
    print("\n" + "=" * 60)
    print("Installing greed-crypto.service …")
    for cmd in [
        ["sudo", "cp", str(unit_src), str(unit_dst)],
        ["sudo", "systemctl", "daemon-reload"],
        ["sudo", "systemctl", "enable", "greed-crypto"],
        ["sudo", "systemctl", "start",  "greed-crypto"],
    ]:
        print(f"  $ {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ERROR: {result.stderr.strip()}")
        else:
            print(f"  OK")
    print("\nTo check status: sudo systemctl status greed-crypto")
    print("=" * 60)


# ─── Supervisor ──────────────────────────────────────────────────────────────

class BotSupervisor:
    """
    24/7 supervisor that launches core.py as a subprocess, monitors it,
    performs a heartbeat /getMe check every 30 s, and restarts on crash
    with exponential back-off (max 60 s).
    """

    HEARTBEAT_INTERVAL = 30   # seconds
    MAX_BACKOFF        = 60   # seconds
    CRASH_LOG          = LOG_DIR / "crash.log"

    def __init__(self, python_exe: Path):
        self.python_exe  = python_exe
        self._process: Optional[subprocess.Popen] = None
        self._shutdown   = False
        self._backoff    = 1
        self._last_hb    = 0.0
        self._bot_token: Optional[str] = None
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT,  self._handle_signal)

    # ── Internals ────────────────────────────────────────────────────────
    def _handle_signal(self, signum, frame):
        log.info(f"Received signal {signum} — shutting down supervisor …")
        self._shutdown = True
        self._kill_bot()

    def _kill_bot(self):
        if self._process and self._process.poll() is None:
            log.info("Terminating bot process …")
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()

    def _read_bot_token(self) -> Optional[str]:
        """Read the bot token from config/config.toml."""
        cfg_path = Path("config/config.toml")
        if not cfg_path.exists():
            return None
        try:
            import toml
            cfg = toml.load(str(cfg_path))
            return cfg.get("Telegram", {}).get("token")
        except Exception:
            return None

    def _heartbeat(self) -> bool:
        """Send a getMe request to Telegram. Returns True on success."""
        if not self._bot_token:
            self._bot_token = self._read_bot_token()
        if not self._bot_token:
            return True   # can't check, assume OK
        try:
            import requests as _req
            resp = _req.get(
                f"https://api.telegram.org/bot{self._bot_token}/getMe",
                timeout=10,
            )
            return resp.status_code == 200
        except Exception as exc:
            log.warning(f"Heartbeat failed: {exc}")
            return False

    def _log_crash(self, returncode: int, output_tail: str):
        with open(self.CRASH_LOG, "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"CRASH at {datetime.datetime.now().isoformat()} "
                    f"| exit code: {returncode}\n")
            f.write(output_tail[-2000:] if output_tail else "(no output captured)\n")

    # ── Main Loop ────────────────────────────────────────────────────────
    def run(self):
        log.info("Supervisor started. Launching bot …")
        while not self._shutdown:
            self._start_bot()
            start_ts = time.time()
            # Monitor loop
            while not self._shutdown:
                time.sleep(1)
                rc = self._process.poll()
                # Heartbeat check
                if time.time() - self._last_hb >= self.HEARTBEAT_INTERVAL:
                    ok = self._heartbeat()
                    self._last_hb = time.time()
                    if not ok:
                        log.warning("Heartbeat failed — will restart if process exits.")
                # If process has ended, handle restart
                if rc is not None:
                    # Collect both stdout and stderr for the crash log
                    output_tail = ""
                    try:
                        if self._process.stdout:
                            output_tail += self._process.stdout.read()
                    except Exception:
                        pass
                    try:
                        if self._process.stderr:
                            output_tail += self._process.stderr.read()
                    except Exception:
                        pass
                    # If the bot ran for more than 60 s, treat it as a "clean" start
                    # and reset the backoff counter to avoid permanent max-delay.
                    uptime = time.time() - start_ts
                    if uptime >= 60:
                        self._backoff = 1
                    log.error(f"Bot process exited with code {rc} "
                               f"(uptime {uptime:.0f}s). "
                               f"Restarting in {self._backoff}s …")
                    self._log_crash(rc, output_tail)
                    time.sleep(self._backoff)
                    self._backoff = min(self._backoff * 2, self.MAX_BACKOFF)
                    break
            if self._shutdown:
                break
        log.info("Supervisor stopped.")

    def _start_bot(self):
        log.info(f"Starting bot: {self.python_exe} core.py")
        self._process = subprocess.Popen(
            [str(self.python_exe), "core.py"],
            stdout=subprocess.PIPE,   # capture stdout for crash logs
            stderr=subprocess.PIPE,   # capture stderr for crash logs
            text=True,
        )
        # Reduce backoff so repeated fast restarts gradually recover
        self._backoff = max(1, self._backoff // 2)


# ════════════════════════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="greed-crypto: setup, patch, and supervise the greed Telegram bot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--setup-only",      action="store_true",
                        help="Run setup steps and exit without starting the supervisor.")
    parser.add_argument("--install-systemd", action="store_true",
                        help="Generate + install greed-crypto.service and exit.")
    parser.add_argument("--no-patch",        action="store_true",
                        help="Skip patching worker.py / database.py.")
    args = parser.parse_args()

    # ── Step 1: Detect repo ──────────────────────────────────────────────
    log.info("=" * 60)
    log.info("greed_cryptorefactor.py — starting up")
    log.info("=" * 60)
    detect_repo_root()

    # ── Step 2: Virtualenv ───────────────────────────────────────────────
    python_exe = setup_venv()

    # ── Step 3: Dependencies ─────────────────────────────────────────────
    install_dependencies(python_exe)

    # ── Step 4: Diagnostics ──────────────────────────────────────────────
    run_diagnostics()

    # ── Step 5-6: Write module files ─────────────────────────────────────
    log.info("Writing module files …")
    write_all_files()

    # ── Steps 2-6: Patch worker.py + database.py ─────────────────────────
    log.info("Patching worker.py …")
    patch_worker_py(no_patch=args.no_patch)
    log.info("Patching database.py …")
    patch_database_py(no_patch=args.no_patch)

    # ── Post-patch diagnostics ───────────────────────────────────────────
    log.info("Re-running diagnostics after patching …")
    run_diagnostics()

    # ── Step 7a: Systemd unit ────────────────────────────────────────────
    svc_path = write_systemd_unit()
    log.info(
        f"\nSystemd service file: {svc_path.resolve()}\n"
        f"  To install:  sudo cp {svc_path} /etc/systemd/system/ && "
        f"sudo systemctl enable --now greed-crypto\n"
        f"  Or re-run:   python3 greed_cryptorefactor.py --install-systemd\n"
    )

    if args.install_systemd:
        install_systemd_unit()
        return

    if args.setup_only:
        log.info("Setup complete (--setup-only). Exiting.")
        return

    # ── Step 7b: Config check ────────────────────────────────────────────
    cfg_path = Path("config/config.toml")
    if not cfg_path.exists():
        log.warning(
            "\n" + "!" * 60 + "\n"
            "config/config.toml does not exist.\n"
            "The bot will create a template on first run.\n"
            "Please edit it (add your bot token + owner ID) then restart.\n"
            "!" * 60
        )
    else:
        try:
            import toml
            cfg = toml.load(str(cfg_path))
            token = cfg.get("Telegram", {}).get("token", "")
            if "YOUR_TOKEN" in token:
                log.warning(
                    "Bot token not configured in config/config.toml! "
                    "Edit the file before the bot can start."
                )
        except Exception:
            pass

    # ── Step 7b: Start supervisor ─────────────────────────────────────────
    log.info("\nStarting 24/7 supervisor …\n")
    supervisor = BotSupervisor(python_exe=python_exe)
    supervisor.run()


if __name__ == "__main__":
    main()
