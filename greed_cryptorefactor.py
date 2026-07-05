#!/usr/bin/env python3
"""
greed_cryptorefactor.py
=======================
A complete refactoring, patching, and supervisor script for the 'greed'
Telegram shop bot (https://github.com/bitbybit91/greed/).

SETUP & RUN INSTRUCTIONS
-------------------------
1. Clone (or place) the greed repo in the current working directory, OR run this
   script from the repo root — it auto-detects the repo directory.

2. (Optional) Set environment variables:
       GREED_DIR=/path/to/greed          # override repo directory
       GREED_TOKEN=<your bot token>      # used only for health-checks
       GREED_OWNER_ID=<owner chat id>    # owner's Telegram user ID

3. Run:
       python3 greed_cryptorefactor.py [--setup-only] [--install-systemd]

   Flags:
       --setup-only      Patch files and exit without starting the supervisor.
       --install-systemd After patching, install and enable the systemd unit.
       --no-patch        Skip patching (assume already done); go straight to supervisor.

4. After first run, edit config/crypto_addresses.toml and fill in your deposit
   addresses, then restart.

WHAT THIS SCRIPT DOES
----------------------
  Part 1  — Detect/verify the greed repo directory.
  Part 2  — Create a Python 3.8+ virtualenv and install all required dependencies.
  Part 3  — Static diagnostics: py_compile every .py file; log errors.
  Part 4  — Write crypto_manager.py, woo_importer.py, and modes/*.py into the repo.
  Part 5  — Patch worker.py: remove CC/Telegram Payments; add crypto-only flow,
             mode routing (SHOP/INVESTMENT/SWAP), admin mode panel, shipping follow-up.
  Part 6  — Write config templates (crypto_addresses.toml, mode_config.toml).
  Part 7  — Write greed-crypto.service systemd unit; optionally install it.
  Part 8  — Supervise the bot subprocess with exponential-backoff restart and
             30-second heartbeat (getMe) health-checks.
"""

# ════════════════════════════════════════════════════════════
# SECTION 0 — Imports
# ════════════════════════════════════════════════════════════
import argparse
import compileall
import datetime
import hashlib
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
import threading
import time
import traceback
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ════════════════════════════════════════════════════════════
# SECTION 1 — Constants
# ════════════════════════════════════════════════════════════

REPO_URL = "https://github.com/bitbybit91/greed/"
VENV_DIR = "venv"
LOGS_DIR = "logs"
MODES_DIR = "modes"
CONFIG_DIR = "config"

REQUIRED_PY_FILES = [
    "worker.py", "database.py", "core.py", "duckbot.py",
    "nuconfig.py", "localization.py", "utils.py",
]

EXTRA_DEPS = [
    "python-telegram-bot==13.5",
    "requests>=2.28.0",
    "aiohttp>=3.8.0",
    "sqlalchemy==1.4.14",
    "toml>=0.10.2",
    "lxml>=4.9.0",
    "apscheduler>=3.9.0",
    "qrcode[pil]>=7.3",
]

HEARTBEAT_INTERVAL = 30          # seconds between health-checks
MAX_RESTART_DELAY = 300          # cap for exponential backoff (seconds)
RESTART_BACKOFF_BASE = 5         # initial backoff (seconds)

# ════════════════════════════════════════════════════════════
# SECTION 2 — Logging Setup
# ════════════════════════════════════════════════════════════

def setup_logging(log_dir: Path) -> logging.Logger:
    """Initialise root logger with console + rotating file handlers."""
    log_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s [%(levelname)-8s] %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    if not root.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(fmt)
        root.addHandler(ch)
    fh = logging.FileHandler(log_dir / "refactor.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)
    return logging.getLogger("greed_refactor")


# ════════════════════════════════════════════════════════════
# SECTION 3 — Environment Preparation
# ════════════════════════════════════════════════════════════

def find_repo_dir() -> Path:
    """Locate the greed repo directory."""
    env_override = os.environ.get("GREED_DIR")
    if env_override:
        p = Path(env_override).expanduser().resolve()
        if p.is_dir() and (p / "worker.py").exists():
            return p
        raise FileNotFoundError(f"GREED_DIR={env_override} does not look like the greed repo")

    cwd = Path.cwd()
    # Script running inside the repo
    if (cwd / "worker.py").exists():
        return cwd
    # Script sitting next to a greed/ subdir
    candidate = cwd / "greed"
    if candidate.is_dir() and (candidate / "worker.py").exists():
        return candidate
    raise FileNotFoundError(
        "Cannot locate the greed repo. Clone it first or set GREED_DIR."
    )


def clone_repo_if_missing(base_dir: Path, log: logging.Logger) -> Path:
    """Clone the greed repo if not already present."""
    target = base_dir / "greed"
    if target.is_dir() and (target / "worker.py").exists():
        log.info(f"Repo already present at {target}")
        return target
    log.info(f"Cloning {REPO_URL} → {target}")
    subprocess.run(["git", "clone", REPO_URL, str(target)], check=True)
    return target


def ensure_venv(repo_dir: Path, log: logging.Logger) -> Path:
    """Create or reuse a virtualenv at repo_dir/venv. Returns path to python binary."""
    venv_path = repo_dir / VENV_DIR
    python_bin = venv_path / "bin" / "python"
    if python_bin.exists():
        log.info(f"Virtualenv already exists at {venv_path}")
        return python_bin

    log.info(f"Creating virtualenv at {venv_path}")
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    log.info("Virtualenv created successfully.")
    return python_bin


def install_dependencies(python_bin: Path, repo_dir: Path, log: logging.Logger) -> None:
    """Install all dependencies inside the virtualenv."""
    pip = python_bin.parent / "pip"
    req_file = repo_dir / "requirements.txt"

    log.info("Upgrading pip…")
    subprocess.run([str(pip), "install", "--upgrade", "pip"], check=True,
                   capture_output=True)

    if req_file.exists():
        log.info(f"Installing from {req_file}…")
        subprocess.run([str(pip), "install", "-r", str(req_file)], check=True)

    log.info(f"Installing extra dependencies: {', '.join(EXTRA_DEPS)}")
    subprocess.run([str(pip), "install"] + EXTRA_DEPS, check=True)
    log.info("All dependencies installed.")


# ════════════════════════════════════════════════════════════
# SECTION 4 — Static Diagnostics
# ════════════════════════════════════════════════════════════

def run_diagnostics(repo_dir: Path, log: logging.Logger) -> bool:
    """
    Run py_compile on every .py file; log errors to logs/diagnostics.log.
    Returns True if all files pass.
    """
    diag_log_path = repo_dir / LOGS_DIR / "diagnostics.log"
    (repo_dir / LOGS_DIR).mkdir(parents=True, exist_ok=True)
    errors: List[str] = []

    with open(diag_log_path, "w", encoding="utf-8") as diag_file:
        diag_file.write(f"=== Diagnostics run at {datetime.datetime.now()} ===\n\n")
        for py_file in sorted(repo_dir.rglob("*.py")):
            if ".git" in py_file.parts or VENV_DIR in py_file.parts:
                continue
            try:
                py_compile.compile(str(py_file), doraise=True)
                diag_file.write(f"[OK]    {py_file.relative_to(repo_dir)}\n")
            except py_compile.PyCompileError as exc:
                msg = f"[ERROR] {py_file.relative_to(repo_dir)}: {exc}"
                diag_file.write(msg + "\n")
                errors.append(msg)
                log.error(msg)
                if _try_auto_fix(py_file, str(exc), log):
                    diag_file.write(f"         ↳ Auto-fixed.\n")

    if errors:
        log.warning(f"{len(errors)} syntax error(s) found. See {diag_log_path}")
        return False
    log.info(f"Diagnostics passed — all .py files compile cleanly.")
    return True


def _try_auto_fix(filepath: Path, error_msg: str, log: logging.Logger) -> bool:
    """Attempt trivially safe auto-fixes for known syntax patterns."""
    try:
        source = filepath.read_text(encoding="utf-8")
        original = source

        # Fix: trailing comma after last positional arg in function call
        source = re.sub(r",\s*\)", ")", source)
        # Fix: Windows-style line endings
        source = source.replace("\r\n", "\n").replace("\r", "\n")
        # Fix: BOM
        source = source.lstrip("\ufeff")

        if source != original:
            filepath.write_text(source, encoding="utf-8")
            try:
                py_compile.compile(str(filepath), doraise=True)
                log.info(f"Auto-fixed: {filepath.name}")
                return True
            except py_compile.PyCompileError:
                filepath.write_text(original, encoding="utf-8")
    except Exception as e:
        log.debug(f"Auto-fix failed for {filepath}: {e}")
    return False


# ════════════════════════════════════════════════════════════
# SECTION 5 — File Sources to Write into the Repo
# ════════════════════════════════════════════════════════════

# ── 5a: crypto_manager.py ──────────────────────────────────
CRYPTO_MANAGER_PY = '''\
"""
crypto_manager.py
=================
CryptoPaymentManager — live CoinGecko rates, address management, and deposit info.
WooCommerceXMLImporter — parse WooCommerce product export XML and import to greed DB.
"""
import logging
import os
import threading
import time
from typing import Dict, Optional, Tuple

import requests

log = logging.getLogger(__name__)


class CryptoPaymentManager:
    """Manages cryptocurrency payment processing with live CoinGecko rates."""

    COINGECKO_BASE = "https://api.coingecko.com/api/v3/simple/price"

    COIN_GECKO_IDS: Dict[str, str] = {
        "BTC":  "bitcoin",
        "XMR":  "monero",
        "ETH":  "ethereum",
        "USDT": "tether",
        "USDC": "usd-coin",
        "LTC":  "litecoin",
        "BNB":  "binancecoin",
        "SOL":  "solana",
        "DOGE": "dogecoin",
        "ADA":  "cardano",
        "TRX":  "tron",
        "MATIC": "matic-network",
    }

    CACHE_TTL = 60       # seconds before re-fetching price
    MAX_RETRIES = 3
    RETRY_DELAY = 2      # base seconds for exponential backoff

    def __init__(self, addresses_path: str, fiat_currency: str = "usd"):
        self.addresses_path = addresses_path
        self.fiat_currency = fiat_currency.lower()
        self._addresses: Dict[str, str] = {}
        self._price_cache: Dict[str, Tuple[float, float]] = {}   # coin -> (price, ts)
        self._cache_lock = threading.Lock()
        self._last_known: Dict[str, float] = {}                  # fallback prices
        self._load_addresses()

    # ── Address management ──────────────────────────────────

    def _load_addresses(self) -> None:
        """Load deposit addresses from the TOML config file."""
        try:
            import toml
            if os.path.exists(self.addresses_path):
                with open(self.addresses_path, "r", encoding="utf-8") as fh:
                    data = toml.load(fh)
                self._addresses = {
                    k.upper(): v.strip()
                    for k, v in data.get("addresses", {}).items()
                }
                log.info("Loaded %d crypto address(es) from %s",
                         len(self._addresses), self.addresses_path)
            else:
                log.warning("Crypto addresses config not found: %s", self.addresses_path)
        except Exception as exc:
            log.error("Failed to load crypto addresses: %s", exc)

    def reload_addresses(self) -> None:
        """Reload addresses from disk (call after editing the TOML file)."""
        self._load_addresses()

    def get_available_coins(self) -> Dict[str, str]:
        """Return {coin: address} for every coin with a non-empty address."""
        return {k: v for k, v in self._addresses.items() if v}

    # ── Price fetching ──────────────────────────────────────

    def get_price(self, coin: str) -> Optional[float]:
        """
        Return the live fiat price of *coin* (e.g. 'BTC').
        Uses a 60-second in-memory cache; falls back to last-known rate on failure.
        """
        coin = coin.upper()
        gecko_id = self.COIN_GECKO_IDS.get(coin)
        if not gecko_id:
            log.warning("No CoinGecko ID for coin: %s", coin)
            return self._last_known.get(coin)

        with self._cache_lock:
            cached = self._price_cache.get(coin)
            if cached and (time.time() - cached[1]) < self.CACHE_TTL:
                return cached[0]

        for attempt in range(self.MAX_RETRIES):
            try:
                resp = requests.get(
                    self.COINGECKO_BASE,
                    params={"ids": gecko_id, "vs_currencies": self.fiat_currency},
                    timeout=10,
                )
                resp.raise_for_status()
                price = resp.json().get(gecko_id, {}).get(self.fiat_currency)
                if price is not None:
                    price = float(price)
                    with self._cache_lock:
                        self._price_cache[coin] = (price, time.time())
                    self._last_known[coin] = price
                    log.debug("Fetched %s = %.6f %s", coin, price, self.fiat_currency.upper())
                    return price
            except requests.RequestException as exc:
                log.warning("CoinGecko attempt %d/%d failed: %s",
                            attempt + 1, self.MAX_RETRIES, exc)
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (2 ** attempt))

        fallback = self._last_known.get(coin)
        if fallback:
            log.warning("Using last-known rate for %s: %.6f", coin, fallback)
        return fallback

    # ── Conversion helpers ──────────────────────────────────

    def fiat_to_crypto(self, fiat_cents: int, coin: str,
                        currency_exp: int = 2) -> Optional[float]:
        """Convert *fiat_cents* (integer minimum units) to crypto amount."""
        fiat = fiat_cents / (10 ** currency_exp)
        rate = self.get_price(coin)
        if not rate:
            return None
        return round(fiat / rate, 8)

    def get_deposit_info(
        self, coin: str, fiat_cents: int,
        currency_exp: int = 2, fiat_symbol: str = "$"
    ) -> Optional[Dict]:
        """
        Return a dict with full deposit info:
          coin, address, crypto_amount, fiat_amount, fiat_symbol, rate, qr_string
        Returns None if no address is configured for the coin or rate is unavailable.
        """
        coin = coin.upper()
        address = self._addresses.get(coin, "").strip()
        if not address:
            log.warning("No deposit address configured for %s", coin)
            return None

        crypto_amount = self.fiat_to_crypto(fiat_cents, coin, currency_exp)
        if crypto_amount is None:
            return None

        fiat_amount = fiat_cents / (10 ** currency_exp)
        rate = self.get_price(coin)

        return {
            "coin":         coin,
            "address":      address,
            "crypto_amount": crypto_amount,
            "fiat_amount":  fiat_amount,
            "fiat_symbol":  fiat_symbol,
            "rate":         rate or 0.0,
            "qr_string":    f"{coin.lower()}:{address}?amount={crypto_amount}",
        }

    def format_deposit_message(self, info: Dict) -> str:
        """Return a Telegram HTML string describing the deposit request."""
        if not info:
            return "\\u274c Payment information unavailable. Please try again."
        coin    = info["coin"]
        amt     = info["crypto_amount"]
        addr    = info["address"]
        fiat    = info["fiat_amount"]
        sym     = info["fiat_symbol"]
        rate    = info["rate"]
        return (
            f"\\U0001f4b0 <b>Crypto Payment Request</b>\\n\\n"
            f"\\U0001fa99 <b>Coin:</b> {coin}\\n"
            f"\\U0001f4b5 <b>Fiat Amount:</b> {sym}{fiat:.2f}\\n"
            f"\\U0001f4ca <b>Live Rate:</b> {sym}{rate:,.4f} / {coin}\\n"
            f"\\U0001f4b1 <b>Send Exactly:</b> <code>{amt:.8f} {coin}</code>\\n\\n"
            f"\\U0001f4ec <b>Deposit Address:</b>\\n<code>{addr}</code>\\n\\n"
            f"\\u26a0\\ufe0f After sending, press <b>I have paid</b> below.\\n"
            f"The owner will verify and credit your account."
        )


# ════════════════════════════════════════════════════════════
# WooCommerce XML Importer
# ════════════════════════════════════════════════════════════

class WooCommerceXMLImporter:
    """
    Parse a WooCommerce product-export XML file and import/update products
    in the greed database.

    Usage::

        from crypto_manager import WooCommerceXMLImporter
        importer = WooCommerceXMLImporter(session, xml_path, crypto_mgr, currency_exp=2)
        count = importer.import_products()
    """

    def __init__(self, session, xml_path: str, crypto_mgr: Optional[CryptoPaymentManager],
                 currency_exp: int = 2):
        self.session = session
        self.xml_path = xml_path
        self.crypto_mgr = crypto_mgr
        self.currency_exp = currency_exp

    def import_products(self) -> int:
        """Parse XML and upsert products into the DB. Returns count of inserted/updated rows."""
        try:
            from lxml import etree
        except ImportError:
            log.error("lxml not installed. Run: pip install lxml")
            return 0

        if not os.path.exists(self.xml_path):
            log.error("WooCommerce XML not found: %s", self.xml_path)
            return 0

        try:
            tree = etree.parse(self.xml_path)
        except etree.XMLSyntaxError as exc:
            log.error("XML parse error: %s", exc)
            return 0

        root = tree.getroot()
        ns_map = {k: v for k, v in root.nsmap.items() if k}

        def _text(el, tag: str, default: str = "") -> str:
            """Extract text from a child element, handling namespaces gracefully."""
            child = el.find(tag)
            if child is None:
                for ns_uri in root.nsmap.values():
                    child = el.find(f"{{{ns_uri}}}{tag}")
                    if child is not None:
                        break
            return (child.text or "").strip() if child is not None else default

        import database as db
        import requests as req

        count = 0
        items = root.findall(".//item")
        if not items:
            items = root.findall(".//{http://wordpress.org/export/1.2/}item")

        for item in items:
            post_type_el = item.find("{http://wordpress.org/export/1.2/}post_type")
            if post_type_el is None or post_type_el.text != "product":
                continue

            title       = _text(item, "title")
            description = _text(item, "{http://purl.org/rss/1.0/modules/content/}encoded") \
                       or _text(item, "description")
            price_str   = ""
            sku         = ""
            stock       = 0
            image_url   = ""

            for meta in item.findall("{http://wordpress.org/export/1.2/}postmeta"):
                key_el   = meta.find("{http://wordpress.org/export/1.2/}meta_key")
                value_el = meta.find("{http://wordpress.org/export/1.2/}meta_value")
                if key_el is None or value_el is None:
                    continue
                key   = (key_el.text or "").strip()
                value = (value_el.text or "").strip()
                if key == "_price":
                    price_str = value
                elif key == "_sku":
                    sku = value
                elif key == "_stock":
                    try:
                        stock = int(float(value))
                    except ValueError:
                        stock = 0
                elif key == "_thumbnail_id":
                    pass  # handled by attachment lookup

            for enc in item.findall("enclosure"):
                url = enc.get("url", "")
                if url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    image_url = url
                    break

            if not title:
                continue

            try:
                price_float = float(price_str.replace(",", ".")) if price_str else None
                price_int   = (
                    int(price_float * (10 ** self.currency_exp))
                    if price_float is not None else None
                )
            except ValueError:
                price_int = None

            # Strip HTML from description
            description_clean = re.sub(r"<[^>]+>", "", description or "").strip()
            description_clean = description_clean[:500] if description_clean else title

            # Fetch image
            image_data: Optional[bytes] = None
            if image_url:
                try:
                    r = req.get(image_url, timeout=10)
                    if r.ok:
                        image_data = r.content
                except Exception:
                    pass

            existing = self.session.query(db.Product).filter_by(name=title).one_or_none()
            if existing:
                existing.description = description_clean
                existing.price       = price_int
                existing.deleted     = False
                if image_data:
                    existing.image = image_data
                log.info("Updated product: %s", title)
            else:
                product = db.Product(
                    name        = title,
                    description = description_clean,
                    price       = price_int,
                    image       = image_data,
                    deleted     = False,
                )
                self.session.add(product)
                log.info("Imported product: %s (price=%s)", title, price_int)

            count += 1

        try:
            self.session.commit()
            log.info("WooCommerce import: %d product(s) processed.", count)
        except Exception as exc:
            self.session.rollback()
            log.error("DB commit failed during WooCommerce import: %s", exc)

        return count
'''


# ── 5b: modes/__init__.py ─────────────────────────────────
MODES_INIT_PY = '''\
"""Greed crypto bot mode modules."""
from .shop_mode       import run_shop_mode
from .investment_mode import run_investment_mode
from .swap_mode       import run_swap_mode

__all__ = ["run_shop_mode", "run_investment_mode", "run_swap_mode"]
'''


# ── 5c: modes/shop_mode.py ────────────────────────────────
SHOP_MODE_PY = '''\
"""
shop_mode.py
============
Standard shop flow: product catalogue → cart → crypto checkout → shipping follow-up.
Entry point: run_shop_mode(worker_instance)
"""
import logging
import datetime
import re
from typing import Optional

import telegram

log = logging.getLogger(__name__)


def run_shop_mode(w) -> None:
    """Main user-menu loop for SHOP_BOT mode."""
    import database as db
    from worker import CancelSignal

    while True:
        coins = list(w._get_crypto_manager().get_available_coins().keys())
        crypto_label = "💳 Top-up with Crypto" if coins else "💳 Crypto Top-up (N/A)"

        keyboard = [
            [telegram.KeyboardButton(w.loc.get("menu_order"))],
            [telegram.KeyboardButton(w.loc.get("menu_order_status"))],
            [telegram.KeyboardButton(crypto_label)],
            [telegram.KeyboardButton(w.loc.get("menu_language"))],
            [
                telegram.KeyboardButton(w.loc.get("menu_help")),
                telegram.KeyboardButton(w.loc.get("menu_bot_info")),
            ],
        ]
        w.bot.send_message(
            w.chat.id,
            w.loc.get("conversation_open_user_menu", credit=w.Price(w.user.credit)),
            reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True),
        )

        valid = [
            w.loc.get("menu_order"),
            w.loc.get("menu_order_status"),
            crypto_label,
            w.loc.get("menu_language"),
            w.loc.get("menu_help"),
            w.loc.get("menu_bot_info"),
        ]
        selection = w._wait_for_message(valid)
        w.update_user()

        if selection == w.loc.get("menu_order"):
            w._order_menu()
        elif selection == w.loc.get("menu_order_status"):
            w._order_status()
        elif selection == crypto_label:
            if coins:
                w._add_credit_crypto()
            else:
                w.bot.send_message(
                    w.chat.id,
                    "⚠️ No crypto addresses configured yet. Please contact the owner."
                )
        elif selection == w.loc.get("menu_language"):
            w._language_menu()
        elif selection == w.loc.get("menu_bot_info"):
            w._bot_info()
        elif selection == w.loc.get("menu_help"):
            w._help_menu()
'''


# ── 5d: modes/investment_mode.py ──────────────────────────
INVESTMENT_MODE_PY = '''\
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
            f"🏦 <b>Investment Dashboard</b>\\n\\nWallet Balance: <b>{w.Price(w.user.credit)}</b>\\n\\nChoose an option:",
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
    text = "📊 <b>Available Investment Plans</b>\\n\\n"
    buttons = []
    for plan in plans:
        text += (
            f"🔹 <b>{plan['name']}</b>\\n"
            f"   Duration: {plan['duration_days']} days\\n"
            f"   ROI: +{plan['roi_percent']}%\\n"
            f"   Minimum: ${plan['min_usd']}\\n\\n"
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
            f"❌ Insufficient balance. You need at least ${plan['min_usd']:.2f}.\\n"
            f"Your balance: {w.Price(w.user.credit)}\\n\\n"
            f"Use <b>💰 Deposit Crypto</b> to top up first."
        )
        return

    w.bot.send_message(
        w.chat.id,
        f"✅ <b>Confirm Investment</b>\\n\\n"
        f"Plan: <b>{plan['name']}</b>\\n"
        f"Amount to invest: <b>{w.Price(min_cents)}</b>\\n"
        f"Duration: <b>{plan['duration_days']} days</b>\\n"
        f"Expected return: <b>+{plan['roi_percent']}%</b> = "
        f"<b>{w.Price(int(min_cents * (1 + plan['roi_percent']/100)))}</b>\\n\\n"
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
        f"🎉 Investment confirmed!\\n\\n"
        f"Plan: <b>{plan['name']}</b>\\n"
        f"Amount: <b>{w.Price(min_cents)}</b>\\n"
        f"Expected return date: <b>{(datetime.datetime.now() + datetime.timedelta(days=plan['duration_days'])).date()}</b>\\n\\n"
        f"The owner will credit your profits when the plan matures.\\n"
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

    lines = ["📈 <b>Your Transaction History</b>\\n"]
    for txn in txns:
        sign = "+" if txn.value > 0 else ""
        status = " [REFUNDED]" if txn.refunded else ""
        lines.append(
            f"• T{txn.transaction_id}: {sign}{w.Price(txn.value)}{status}"
            + (f"\\n  <i>{txn.notes}</i>" if txn.notes else "")
        )
    lines.append(f"\\n💰 Current Balance: <b>{w.Price(w.user.credit)}</b>")
    w.bot.send_message(w.chat.id, "\\n".join(lines))


def _request_withdrawal(w) -> None:
    """Collect withdrawal request details and notify owner."""
    import database as db
    from worker import CancelSignal

    if w.user.credit <= 0:
        w.bot.send_message(w.chat.id, "❌ Your balance is zero. Nothing to withdraw.")
        return

    w.bot.send_message(
        w.chat.id,
        f"💸 <b>Withdrawal Request</b>\\n\\n"
        f"Available balance: <b>{w.Price(w.user.credit)}</b>\\n\\n"
        f"Please enter your crypto wallet address to receive the withdrawal,\\n"
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
        f"💸 WITHDRAWAL REQUEST\\n"
        f"User: {w.user.mention()} (ID: {w.user.user_id})\\n"
        f"Amount: {w.Price(w.user.credit)}\\n"
        f"Coin: {coin}\\n"
        f"Address: {address}"
    )
    if owner_admin:
        w.bot.send_message(owner_admin.user_id, note)

    w.bot.send_message(
        w.chat.id,
        f"✅ Withdrawal request submitted!\\n\\n"
        f"Amount: <b>{w.Price(w.user.credit)}</b> in <b>{coin}</b>\\n"
        f"Address: <code>{address}</code>\\n\\n"
        f"The owner will process your request shortly."
    )
'''


# ── 5e: modes/swap_mode.py ────────────────────────────────
SWAP_MODE_PY = '''\
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
            "🔄 <b>Crypto Swap Service</b>\\n\\nInstant peer-to-peer crypto swaps.\\n\\nChoose an option:",
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
        f"🔄 <b>Step 3:</b> Enter the amount of <b>{coin_in}</b> you want to send\\n"
        f"(e.g. <code>0.005</code>):"
    )
    amount_str = w._wait_for_regex(r"([0-9]+(?:\\.[0-9]+)?)", cancellable=True)
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
        f"🔄 <b>Swap Quote</b>\\n\\n"
        f"You send:    <code>{amount_in:.8f} {coin_in}</code>\\n"
        f"Rate {coin_in}: ${price_in:,.4f}\\n"
        f"Rate {coin_out}: ${price_out:,.4f}\\n"
        f"Service fee: {spread}%\\n"
        f"You receive: <code>{amount_out:.8f} {coin_out}</code>\\n\\n"
        f"📬 Send <b>exactly</b> <code>{amount_in:.8f} {coin_in}</code> to:\\n"
        f"<code>{deposit_address}</code>\\n\\n"
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
            f"🔄 <b>Swap Request</b>\\n"
            f"User: {w.user.mention()} (ID: {w.user.user_id})\\n"
            f"Sends: {amount_in:.8f} {coin_in} → receives: {amount_out:.8f} {coin_out}\\n"
            f"Their payout address will be collected next."
        )

    # Collect user's receive address
    w.bot.send_message(
        w.chat.id,
        f"✅ Payment noted!\\n\\nPlease send your <b>{coin_out}</b> receiving address:"
    )
    recv_addr = w._wait_for_regex(r"(.+)", cancellable=True)
    if isinstance(recv_addr, CancelSignal):
        w.bot.send_message(w.chat.id, "Swap payout address not provided. Contact support.")
        return

    if owner:
        w.bot.send_message(
            owner.user_id,
            f"📬 Payout address for above swap:\\n<code>{recv_addr}</code>\\n"
            f"Please send <code>{amount_out:.8f} {coin_out}</code> to this address."
        )

    w.bot.send_message(
        w.chat.id,
        f"🎉 <b>Swap submitted!</b>\\n\\n"
        f"You will receive <code>{amount_out:.8f} {coin_out}</code> at\\n"
        f"<code>{recv_addr}</code>\\n\\n"
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

    lines = ["📜 <b>Your Swap History</b>\\n"]
    for txn in txns:
        lines.append(f"• {txn.notes}")
    w.bot.send_message(w.chat.id, "\\n".join(lines))
'''


# ════════════════════════════════════════════════════════════
# SECTION 6 — Config File Templates
# ════════════════════════════════════════════════════════════

CRYPTO_ADDRESSES_TOML = """\
# crypto_addresses.toml
# =====================
# Configure your cryptocurrency deposit addresses here.
# Leave value blank ("") to disable that coin.

[addresses]
BTC   = ""   # Bitcoin  — e.g. "bc1qxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
ETH   = ""   # Ethereum — e.g. "0xYourEthAddress"
XMR   = ""   # Monero   — e.g. "4YourMoneroAddress..."
USDT  = ""   # Tether (TRC-20 or ERC-20 address)
USDC  = ""   # USD Coin
LTC   = ""   # Litecoin — e.g. "LYourLitecoinAddress"
BNB   = ""   # BNB Smart Chain
SOL   = ""   # Solana
DOGE  = ""   # Dogecoin
TRX   = ""   # Tron (TRC-20)
"""

MODE_CONFIG_TOML = """\
# mode_config.toml
# ================
# Controls the active bot mode and per-mode settings.

[bot]
# Active mode: SHOP_BOT | INVESTMENT_BOT | SWAP_BOT
active_mode = "SHOP_BOT"

# Enable / disable modes entirely
shop_enabled       = true
investment_enabled = true
swap_enabled       = true

[woocommerce]
# Path to WooCommerce product export XML (relative to bot root or absolute)
xml_path = "products.xml"

[investment]
# Define investment plans as array of tables
[[investment.plans]]
id            = "basic"
name          = "Basic Plan"
duration_days = 7
roi_percent   = 5.0
min_usd       = 50

[[investment.plans]]
id            = "standard"
name          = "Standard Plan"
duration_days = 14
roi_percent   = 12.0
min_usd       = 100

[[investment.plans]]
id            = "premium"
name          = "Premium Plan"
duration_days = 30
roi_percent   = 30.0
min_usd       = 250

[swap]
# Owner spread / profit margin percentage applied to every swap
spread_percent = 2.0
"""


# ════════════════════════════════════════════════════════════
# SECTION 7 — Worker.py Patcher
# ════════════════════════════════════════════════════════════

# New imports to inject at the top of worker.py
WORKER_NEW_IMPORTS = """\
import os as _os
import toml as _toml

try:
    from crypto_manager import CryptoPaymentManager as _CryptoPaymentManager
except ImportError:
    _CryptoPaymentManager = None  # will warn at runtime

try:
    from woo_importer import WooCommerceXMLImporter as _WooImporter
except ImportError:
    _WooImporter = None
"""

# New methods to append to the Worker class (added just before run(self))
WORKER_NEW_METHODS = r'''
    # ─── Crypto / Mode helpers ─────────────────────────────────────────────────

    def _get_crypto_manager(self):
        """Lazy-initialise and return the shared CryptoPaymentManager."""
        if not hasattr(self, "_crypto_mgr") or self._crypto_mgr is None:
            if _CryptoPaymentManager is None:
                return None
            currency = self.cfg["Payments"].get("currency", "usd").lower()
            self._crypto_mgr = _CryptoPaymentManager(
                addresses_path=_os.path.join("config", "crypto_addresses.toml"),
                fiat_currency=currency,
            )
        return self._crypto_mgr

    def _get_active_mode(self) -> str:
        """Read the active bot mode from mode_config.toml. Defaults to SHOP_BOT."""
        cfg_path = _os.path.join("config", "mode_config.toml")
        try:
            if _os.path.exists(cfg_path):
                with open(cfg_path, encoding="utf-8") as fh:
                    data = _toml.load(fh)
                return data.get("bot", {}).get("active_mode", "SHOP_BOT")
        except Exception:
            pass
        return "SHOP_BOT"

    def _set_active_mode(self, mode: str) -> None:
        """Persist the active mode to mode_config.toml."""
        cfg_path = _os.path.join("config", "mode_config.toml")
        try:
            data = {}
            if _os.path.exists(cfg_path):
                with open(cfg_path, encoding="utf-8") as fh:
                    data = _toml.load(fh)
            data.setdefault("bot", {})["active_mode"] = mode
            with open(cfg_path, "w", encoding="utf-8") as fh:
                _toml.dump(data, fh)
        except Exception as exc:
            log.error("Failed to save mode config: %s", exc)

    # Public wrappers used by mode modules (avoid name-mangling from external files)
    def _wait_for_message(self, items, cancellable=False):
        return self.__wait_for_specific_message(items, cancellable=cancellable)

    def _wait_for_regex(self, regex, cancellable=False):
        return self.__wait_for_regex(regex, cancellable=cancellable)

    def _wait_for_callback(self, cancellable=False):
        cb = self.__wait_for_inlinekeyboard_callback(cancellable=cancellable)
        if isinstance(cb, CancelSignal):
            return None
        return cb.data

    def _order_menu(self):
        return self.__order_menu()

    def _order_status(self):
        return self.__order_status()

    def _add_credit_crypto(self):
        return self.__add_credit_crypto()

    def _language_menu(self):
        return self.__language_menu()

    def _help_menu(self):
        return self.__help_menu()

    def _bot_info(self):
        return self.__bot_info()

    # ─── Crypto deposit flow ───────────────────────────────────────────────────

    def __add_credit_crypto(self):
        """Let the user top up their wallet via cryptocurrency deposit."""
        log.debug("Displaying __add_credit_crypto")
        mgr = self._get_crypto_manager()
        if mgr is None:
            self.bot.send_message(
                self.chat.id,
                "⚠️ Crypto payment system unavailable. Please contact the owner."
            )
            return

        coins = mgr.get_available_coins()
        if not coins:
            self.bot.send_message(
                self.chat.id,
                "⚠️ No cryptocurrency addresses have been configured yet.\n"
                "Please contact the owner."
            )
            return

        # Step 1: Choose coin
        buttons = [
            [telegram.InlineKeyboardButton(coin, callback_data=f"deposit_{coin}")]
            for coin in sorted(coins.keys())
        ]
        buttons.append([telegram.InlineKeyboardButton("❌ Cancel", callback_data="cmd_cancel")])
        self.bot.send_message(
            self.chat.id,
            "💳 <b>Crypto Deposit</b>\n\nSelect the cryptocurrency you want to deposit:",
            reply_markup=telegram.InlineKeyboardMarkup(buttons)
        )
        cb = self.__wait_for_inlinekeyboard_callback(cancellable=True)
        if isinstance(cb, CancelSignal):
            return
        coin = cb.data.replace("deposit_", "")

        # Step 2: Enter amount (in fiat)
        self.bot.send_message(
            self.chat.id,
            f"Enter the fiat amount you want to add to your wallet\n"
            f"(e.g. <code>50</code> for $50.00):",
            reply_markup=telegram.ReplyKeyboardRemove()
        )
        raw = self.__wait_for_regex(r"([0-9]+(?:[.,][0-9]{1,2})?)", cancellable=True)
        if isinstance(raw, CancelSignal):
            return
        fiat_value = self.Price(raw)
        fiat_cents = int(fiat_value)

        # Step 3: Get deposit info
        currency_exp = self.cfg["Payments"]["currency_exp"]
        fiat_symbol  = self.cfg["Payments"]["currency_symbol"]
        info = mgr.get_deposit_info(
            coin=coin,
            fiat_cents=fiat_cents,
            currency_exp=currency_exp,
            fiat_symbol=fiat_symbol,
        )
        if info is None:
            self.bot.send_message(
                self.chat.id,
                "⚠️ Could not generate payment info. The price feed may be unavailable. Try again shortly."
            )
            return

        msg_text = mgr.format_deposit_message(info)
        confirm_keyboard = telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton("✅ I have paid", callback_data="crypto_paid")],
            [telegram.InlineKeyboardButton("❌ Cancel",      callback_data="cmd_cancel")],
        ])
        self.bot.send_message(self.chat.id, msg_text, reply_markup=confirm_keyboard)

        cb2 = self.__wait_for_inlinekeyboard_callback(cancellable=True)
        if isinstance(cb2, CancelSignal):
            return

        if cb2.data == "crypto_paid":
            # Ask for tx reference
            self.bot.send_message(
                self.chat.id,
                "📝 Please paste your <b>transaction ID / hash</b> so the owner can verify:\n"
                "(Or type <code>skip</code> if you don't have one yet)"
            )
            tx_ref = self.__wait_for_regex(r"(.+)", cancellable=True)
            if isinstance(tx_ref, CancelSignal):
                tx_ref = "not provided"

            # Notify admins
            admins = self.session.query(db.Admin).filter(
                db.Admin.receive_orders == True
            ).all()
            owner_keyboard = telegram.InlineKeyboardMarkup([
                [telegram.InlineKeyboardButton(
                    f"✅ Confirm {str(fiat_value)} deposit",
                    callback_data=f"confirm_deposit_{self.user.user_id}_{fiat_cents}"
                )],
                [telegram.InlineKeyboardButton(
                    "❌ Reject",
                    callback_data=f"reject_deposit_{self.user.user_id}"
                )],
            ])
            notif = (
                f"💳 <b>Crypto Deposit Request</b>\n\n"
                f"User: {self.user.mention()} (ID: {self.user.user_id})\n"
                f"Amount: <b>{str(fiat_value)}</b>\n"
                f"Coin: <b>{coin}</b>\n"
                f"Crypto amount: <code>{info['crypto_amount']:.8f} {coin}</code>\n"
                f"Tx Ref: <code>{tx_ref}</code>\n"
            )
            for admin in admins:
                self.bot.send_message(admin.user_id, notif, reply_markup=owner_keyboard)

            self.bot.send_message(
                self.chat.id,
                f"⏳ <b>Payment submitted for review!</b>\n\n"
                f"Amount: <b>{str(fiat_value)}</b>\n"
                f"Coin: <b>{coin}</b>\n"
                f"Tx Ref: <code>{tx_ref}</code>\n\n"
                f"The owner will credit your account once the payment is verified."
            )

    # ─── Shipping follow-up after shop purchase ────────────────────────────────

    def __crypto_shipping_followup(self, order) -> None:
        """
        Collect shipping details from the user after a successful purchase.
        FSM: name → address → phone → notes → confirm → notify owner.
        """
        log.debug("Starting shipping follow-up for order %s", order.order_id)
        cancel_kb = telegram.InlineKeyboardMarkup([[
            telegram.InlineKeyboardButton("⏭ Skip", callback_data="cmd_cancel")
        ]])

        self.bot.send_message(
            self.chat.id,
            "📦 <b>Shipping Details</b>\n\n"
            "Your payment is confirmed! Please provide shipping information.\n\n"
            "What is your <b>full name</b>? (or press Skip)"
        )

        def _ask(prompt: str, cancellable: bool = True) -> str:
            self.bot.send_message(self.chat.id, prompt, reply_markup=cancel_kb)
            result = self.__wait_for_regex(r"(.*)", cancellable=cancellable)
            if isinstance(result, CancelSignal):
                return ""
            return result.strip()

        full_name = _ask("✏️ Your full name:")
        if not full_name:
            full_name = str(self.user)

        address = _ask("🏠 Your shipping address (street, city, postcode, country):")
        phone   = _ask("📞 Your phone number (with country code):")
        notes   = _ask("📝 Any special delivery notes? (or press Skip)")

        # Compile order summary
        from html import escape as _esc
        summary = (
            f"📦 <b>Order Confirmed!</b>\n\n"
            f"🆔 Order ID: <b>#{order.order_id}</b>\n"
            f"👤 Name: {_esc(full_name)}\n"
            f"🏠 Address: {_esc(address)}\n"
            f"📞 Phone: {_esc(phone)}\n"
            f"📝 Notes: {_esc(notes) if notes else 'None'}\n\n"
            f"Thank you for your order! You'll be notified when it ships. 🚚"
        )
        self.bot.send_message(self.chat.id, summary)

        # Notify all order-receiving admins
        admins = self.session.query(db.Admin).filter(
            db.Admin.receive_orders == True
        ).all()
        order_text = order.text(w=self)
        owner_notif = (
            f"🆕 <b>New Order + Shipping Details</b>\n\n"
            f"{order_text}\n\n"
            f"👤 Customer: {self.user.mention()} (ID: {self.user.user_id})\n"
            f"📛 Name: {_esc(full_name)}\n"
            f"🏠 Address: {_esc(address)}\n"
            f"📞 Phone: {_esc(phone)}\n"
            f"📝 Notes: {_esc(notes) if notes else 'None'}"
        )
        order_keyboard = telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton("✅ Mark Shipped", callback_data="order_complete")],
            [telegram.InlineKeyboardButton("💰 Refund",       callback_data="order_refund")],
        ])
        for admin in admins:
            self.bot.send_message(admin.user_id, owner_notif, reply_markup=order_keyboard)

        # Persist shipping info in order notes
        if hasattr(order, "notes"):
            existing_notes = order.notes or ""
            order.notes = (
                existing_notes
                + f"\n[Shipping] Name={full_name} | "
                  f"Addr={address} | Phone={phone} | Notes={notes}"
            )
            self.session.commit()

    # ─── Admin mode config panel ───────────────────────────────────────────────

    def __mode_config_menu(self) -> None:
        """Owner-only inline panel to switch the active bot mode."""
        log.debug("Displaying __mode_config_menu")
        current = self._get_active_mode()

        def _label(mode: str) -> str:
            return f"{'✅ ' if current == mode else ''}{mode}"

        keyboard = telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton(_label("SHOP_BOT"),       callback_data="mode_SHOP_BOT")],
            [telegram.InlineKeyboardButton(_label("INVESTMENT_BOT"), callback_data="mode_INVESTMENT_BOT")],
            [telegram.InlineKeyboardButton(_label("SWAP_BOT"),       callback_data="mode_SWAP_BOT")],
            [telegram.InlineKeyboardButton("🔄 Reload Addresses",    callback_data="mode_reload_addrs")],
            [telegram.InlineKeyboardButton("📦 Import WooCommerce",  callback_data="mode_woo_import")],
            [telegram.InlineKeyboardButton("← Back",                 callback_data="cmd_cancel")],
        ])
        self.bot.send_message(
            self.chat.id,
            f"🔧 <b>Bot Mode Configuration</b>\n\nCurrent mode: <b>{current}</b>\n\n"
            "Select a mode to activate:",
            reply_markup=keyboard
        )

        cb = self.__wait_for_inlinekeyboard_callback(cancellable=True)
        if isinstance(cb, CancelSignal):
            return

        if cb.data.startswith("mode_") and not cb.data.startswith("mode_reload") \
                and not cb.data.startswith("mode_woo"):
            new_mode = cb.data.replace("mode_", "")
            self._set_active_mode(new_mode)
            self.bot.send_message(
                self.chat.id,
                f"✅ Active mode changed to <b>{new_mode}</b>."
            )

        elif cb.data == "mode_reload_addrs":
            mgr = self._get_crypto_manager()
            if mgr:
                mgr.reload_addresses()
                n = len(mgr.get_available_coins())
                self.bot.send_message(
                    self.chat.id,
                    f"✅ Addresses reloaded. {n} coin(s) active."
                )
            else:
                self.bot.send_message(self.chat.id, "⚠️ Crypto manager unavailable.")

        elif cb.data == "mode_woo_import":
            if _WooImporter is None:
                self.bot.send_message(self.chat.id, "⚠️ WooCommerce importer unavailable.")
                return
            cfg_path = _os.path.join("config", "mode_config.toml")
            xml_path = "products.xml"
            try:
                import toml as _t2
                if _os.path.exists(cfg_path):
                    data = _t2.load(open(cfg_path))
                    xml_path = data.get("woocommerce", {}).get("xml_path", xml_path)
            except Exception:
                pass

            self.bot.send_message(self.chat.id, f"⏳ Importing from <code>{xml_path}</code>…")
            mgr = self._get_crypto_manager()
            importer = _WooImporter(
                session=self.session,
                xml_path=xml_path,
                crypto_mgr=mgr,
                currency_exp=self.cfg["Payments"]["currency_exp"],
            )
            count = importer.import_products()
            self.bot.send_message(
                self.chat.id,
                f"✅ WooCommerce import complete. {count} product(s) processed."
            )
'''


# New __user_menu implementation that routes by mode
USER_MENU_REPLACEMENT = '''    def __user_menu(self):
        """Route the user to the appropriate mode-based menu."""
        log.debug("Displaying __user_menu (mode-aware)")
        mode = self._get_active_mode()
        if mode == "INVESTMENT_BOT":
            try:
                from modes.investment_mode import run_investment_mode
                run_investment_mode(self)
            except Exception as exc:
                log.error("investment_mode error: %s", exc)
                self.__user_menu_shop()
        elif mode == "SWAP_BOT":
            try:
                from modes.swap_mode import run_swap_mode
                run_swap_mode(self)
            except Exception as exc:
                log.error("swap_mode error: %s", exc)
                self.__user_menu_shop()
        else:
            try:
                from modes.shop_mode import run_shop_mode
                run_shop_mode(self)
            except Exception as exc:
                log.error("shop_mode error: %s", exc)
                self.__user_menu_shop()

    def __user_menu_shop(self):
        """Fallback shop menu (no external mode file required)."""
        log.debug("Displaying __user_menu_shop (fallback)")
        while True:
            keyboard = [[telegram.KeyboardButton(self.loc.get("menu_order"))],
                        [telegram.KeyboardButton(self.loc.get("menu_order_status"))],
                        [telegram.KeyboardButton("💳 Add Crypto Credit")],
                        [telegram.KeyboardButton(self.loc.get("menu_language"))],
                        [telegram.KeyboardButton(self.loc.get("menu_help")),
                         telegram.KeyboardButton(self.loc.get("menu_bot_info"))]]
            self.bot.send_message(self.chat.id,
                                  self.loc.get("conversation_open_user_menu",
                                               credit=self.Price(self.user.credit)),
                                  reply_markup=telegram.ReplyKeyboardMarkup(keyboard, one_time_keyboard=True))
            selection = self.__wait_for_specific_message([
                self.loc.get("menu_order"),
                self.loc.get("menu_order_status"),
                "💳 Add Crypto Credit",
                self.loc.get("menu_language"),
                self.loc.get("menu_help"),
                self.loc.get("menu_bot_info"),
            ])
            self.update_user()
            if selection == self.loc.get("menu_order"):
                self.__order_menu()
            elif selection == self.loc.get("menu_order_status"):
                self.__order_status()
            elif selection == "💳 Add Crypto Credit":
                self.__add_credit_crypto()
            elif selection == self.loc.get("menu_language"):
                self.__language_menu()
            elif selection == self.loc.get("menu_bot_info"):
                self.__bot_info()
            elif selection == self.loc.get("menu_help"):
                self.__help_menu()
'''

# Replacement for __add_credit_menu (delegates to crypto)
ADD_CREDIT_MENU_REPLACEMENT = '''    def __add_credit_menu(self):
        """Add credit via cryptocurrency deposit (Telegram Payments removed)."""
        log.debug("Displaying __add_credit_menu → crypto only")
        self.__add_credit_crypto()
'''

# Replacement for __add_credit_cc (no longer used)
ADD_CREDIT_CC_REPLACEMENT = (
    '    def __add_credit_cc(self):\n'
    '        """Removed: Telegram/Stripe CC payment is no longer supported."""\n'
    '        log.warning("__add_credit_cc called but CC payments are disabled.")\n'
    '        self.bot.send_message(\n'
    '            self.chat.id,\n'
    '            "\\U0001f4b3 Credit card payments are no longer supported. "\n'
    '            "Please use cryptocurrency to add credit instead."\n'
    '        )\n'
    '        self.__add_credit_crypto()\n'
)

# Replacement for __make_payment (no longer sends Telegram invoice)
MAKE_PAYMENT_REPLACEMENT = '''    def __make_payment(self, amount):
        """Removed: Telegram invoice payments replaced by crypto-only flow."""
        log.warning("__make_payment called; redirecting to crypto deposit.")
        self.__add_credit_crypto()
'''


def _extract_method_span(source: str, method_name: str) -> Optional[Tuple[int, int]]:
    """
    Find the start and end character positions of a method definition in *source*.
    Returns (start, end) or None if not found.
    The range covers from the 'def' line through all its body lines.
    """
    # Match 'def <method_name>(' at any indentation level
    pattern = re.compile(
        r'^( {4,})def ' + re.escape(method_name) + r'\b',
        re.MULTILINE
    )
    m = pattern.search(source)
    if not m:
        return None

    indent = m.group(1)          # e.g. "    " (4 spaces for class method)
    start = m.start()
    rest = source[m.end():]      # everything after the indent+def

    # Walk line by line from after the def line to find where the method ends.
    # The method body is everything that is indented more than `indent`,
    # or is a blank line.  The method ends when we hit a non-blank line
    # at the same (or lower) indent level.
    def_end_nl = source.find('\n', m.start())
    if def_end_nl == -1:
        return (start, len(source))

    scan_pos = def_end_nl + 1
    end = scan_pos

    for line in source[scan_pos:].splitlines(keepends=True):
        stripped = line.rstrip('\n\r')
        if stripped == '' or stripped.isspace():
            end += len(line)
            continue
        # Count leading spaces
        leading = len(stripped) - len(stripped.lstrip(' '))
        if leading > len(indent):
            end += len(line)
        else:
            break

    return (start, end)


def _replace_method(source: str, method_name: str, new_body: str) -> str:
    """Replace the implementation of *method_name* in *source* with *new_body*."""
    span = _extract_method_span(source, method_name)
    if span is None:
        log_global.warning("Method %s not found in source; skipping replacement.", method_name)
        return source
    return source[:span[0]] + new_body + source[span[1]:]


def patch_worker_py(repo_dir: Path, log: logging.Logger) -> None:
    """Apply all patches to worker.py in place."""
    worker_path = repo_dir / "worker.py"
    if not worker_path.exists():
        log.error("worker.py not found at %s", worker_path)
        return

    # Back up original
    backup = worker_path.with_suffix(".py.bak")
    if not backup.exists():
        shutil.copy2(worker_path, backup)
        log.info("Backed up worker.py → worker.py.bak")

    source = worker_path.read_text(encoding="utf-8")

    # 1. Inject new imports after existing imports block
    if "_CryptoPaymentManager" not in source:
        # Find end of imports (first non-import, non-comment line)
        import_end = 0
        for match in re.finditer(r'^import |^from ', source, re.MULTILINE):
            import_end = match.end() + source[match.end():].find('\n') + 1
        insert_at = import_end
        source = source[:insert_at] + "\n" + WORKER_NEW_IMPORTS + "\n" + source[insert_at:]
        log.info("Injected crypto imports into worker.py")

    # 2. Replace individual methods
    replacements = [
        ("__user_menu",      USER_MENU_REPLACEMENT),
        ("__add_credit_menu", ADD_CREDIT_MENU_REPLACEMENT),
        ("__add_credit_cc",  ADD_CREDIT_CC_REPLACEMENT),
        ("__make_payment",   MAKE_PAYMENT_REPLACEMENT),
    ]
    for method_name, new_body in replacements:
        before = source
        source = _replace_method(source, method_name, new_body)
        if source != before:
            log.info("Patched %s in worker.py", method_name)
        else:
            log.warning("Could not find %s to patch in worker.py", method_name)

    # 3b. Patch the checkout block inside __order_menu (remove CC check, add crypto top-up)
    old_checkout_block = (
        '        # Suggest payment for missing credit value if configuration allows refill\n'
        '            if self.cfg["Payments"]["CreditCard"]["credit_card_token"] != "" \\\n'
        '                    and self.cfg["Appearance"]["refill_on_checkout"] \\\n'
        '                    and self.Price(self.cfg["Payments"]["CreditCard"]["min_amount"]) <= \\\n'
        '                    credit_required <= \\\n'
        '                    self.Price(self.cfg["Payments"]["CreditCard"]["max_amount"]):\n'
        '                self.__make_payment(self.Price(credit_required))'
    )
    new_checkout_block = (
        '        # Offer crypto top-up when credit is insufficient\n'
        '            if self.cfg["Appearance"]["refill_on_checkout"]:\n'
        '                self.__add_credit_crypto()\n'
        '                self.update_user()'
    )
    if old_checkout_block in source:
        source = source.replace(old_checkout_block, new_checkout_block, 1)
        log.info("Patched CC checkout block in __order_menu")
    else:
        # Fallback: simpler pattern
        old_alt = (
            'if self.cfg["Payments"]["CreditCard"]["credit_card_token"] != "" \\\n'
            '                    and self.cfg["Appearance"]["refill_on_checkout"]'
        )
        if old_alt in source:
            # Find surrounding block and replace
            idx = source.find(old_alt)
            block_end = source.find("self.__make_payment(self.Price(credit_required))", idx)
            if block_end != -1:
                block_end = source.find('\n', block_end) + 1
                replacement = (
                    'if self.cfg["Appearance"]["refill_on_checkout"]:\n'
                    '                self.__add_credit_crypto()\n'
                    '                self.update_user()\n'
                )
                source = source[:idx] + replacement + source[block_end:]
                log.info("Patched CC checkout block (fallback) in __order_menu")
        else:
            log.warning("Could not find CC checkout block in __order_menu; manual review needed.")

    # 3c. Add shipping follow-up call after __order_transaction inside __order_menu
    old_order_txn = "self.__order_transaction(order=order, value=-int(self.__get_cart_value(cart)))"
    new_order_txn = (
        "self.__order_transaction(order=order, value=-int(self.__get_cart_value(cart)))\n"
        "            self.__crypto_shipping_followup(order)"
    )
    if old_order_txn in source and "crypto_shipping_followup" not in source:
        source = source.replace(old_order_txn, new_order_txn, 1)
        log.info("Added shipping follow-up call after __order_transaction")

    # 3. Append new methods to the Worker class
    # Find end of class Worker (last method before a new top-level def/class)
    if "def __add_credit_crypto(self)" not in source:
        # Insert before the closing of Worker class or before `def main`
        insert_marker = "\ndef main("
        pos = source.find(insert_marker)
        if pos == -1:
            # Append at end
            source += "\n" + WORKER_NEW_METHODS + "\n"
        else:
            source = source[:pos] + "\n" + WORKER_NEW_METHODS + "\n" + source[pos:]
        log.info("Appended new crypto/mode methods to worker.py")

    # 4. Patch __admin_menu to add mode config button
    if "🔧 Mode Config" not in source and "def __mode_config_menu" in source:
        # Add to admin keyboard list after is_owner block
        old_snippet = 'keyboard.append([self.loc.get("menu_edit_admins")])'
        new_snippet = (
            'keyboard.append([self.loc.get("menu_edit_admins")])\n'
            '            if self.admin.is_owner:\n'
            '                keyboard.append(["🔧 Mode Config"])'
        )
        if old_snippet in source:
            source = source.replace(old_snippet, new_snippet, 1)
            log.info("Injected Mode Config button into __admin_menu keyboard")

        # Add handler in the selection chain
        old_sel = 'self.loc.get("menu_edit_admins")'
        handler_insert = (
            '            elif selection == "🔧 Mode Config" and self.admin.is_owner:\n'
            '                self.__mode_config_menu()\n'
        )
        # Find the last elif in __admin_menu to insert after
        admin_menu_pos = source.find("def __admin_menu(")
        if admin_menu_pos != -1:
            # Find "elif selection == self.loc.get("menu_csv")" and insert after its block
            csv_handler = '                self.__transactions_file()'
            csv_pos = source.find(csv_handler, admin_menu_pos)
            if csv_pos != -1:
                insert_pos = csv_pos + len(csv_handler)
                source = source[:insert_pos] + "\n" + handler_insert + source[insert_pos:]
                log.info("Injected Mode Config handler into __admin_menu")

    # 5. Write patched file
    worker_path.write_text(source, encoding="utf-8")

    # 6. Verify syntax
    try:
        py_compile.compile(str(worker_path), doraise=True)
        log.info("worker.py patched and compiles cleanly.")
    except py_compile.PyCompileError as exc:
        log.error("Patched worker.py has syntax errors: %s", exc)
        log.error("Restoring from backup.")
        shutil.copy2(backup, worker_path)


# ════════════════════════════════════════════════════════════
# SECTION 8 — Write Files to Repo
# ════════════════════════════════════════════════════════════

def write_file(path: Path, content: str, log: logging.Logger, overwrite: bool = True) -> None:
    """Write *content* to *path*, optionally skipping if already present."""
    if path.exists() and not overwrite:
        log.info("File already exists, skipping: %s", path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    log.info("Wrote: %s", path)


def write_all_files(repo_dir: Path, log: logging.Logger) -> None:
    """Write crypto_manager.py, woo_importer.py, modes/, and config templates."""
    write_file(repo_dir / "crypto_manager.py",             CRYPTO_MANAGER_PY, log)

    # woo_importer.py is part of crypto_manager.py; keep a thin shim for import compatibility
    woo_shim = (
        '"""Thin shim — WooCommerceXMLImporter lives in crypto_manager."""\n'
        'from crypto_manager import WooCommerceXMLImporter  # noqa: F401\n'
    )
    write_file(repo_dir / "woo_importer.py", woo_shim, log)

    modes_dir = repo_dir / MODES_DIR
    modes_dir.mkdir(exist_ok=True)
    write_file(modes_dir / "__init__.py",      MODES_INIT_PY,      log)
    write_file(modes_dir / "shop_mode.py",     SHOP_MODE_PY,       log)
    write_file(modes_dir / "investment_mode.py", INVESTMENT_MODE_PY, log)
    write_file(modes_dir / "swap_mode.py",     SWAP_MODE_PY,       log)

    config_dir = repo_dir / CONFIG_DIR
    config_dir.mkdir(exist_ok=True)
    write_file(config_dir / "crypto_addresses.toml", CRYPTO_ADDRESSES_TOML, log,
               overwrite=False)   # don't overwrite if owner has filled it in
    write_file(config_dir / "mode_config.toml",      MODE_CONFIG_TOML,      log,
               overwrite=False)


# ════════════════════════════════════════════════════════════
# SECTION 9 — Systemd Unit
# ════════════════════════════════════════════════════════════

def generate_systemd_unit(repo_dir: Path, venv_python: Path) -> str:
    """Generate a systemd service unit file for the bot."""
    return textwrap.dedent(f"""\
        [Unit]
        Description=Greed Crypto Telegram Bot
        After=network-online.target
        Wants=network-online.target

        [Service]
        Type=simple
        WorkingDirectory={repo_dir}
        ExecStart={venv_python} {repo_dir / 'greed_cryptorefactor.py'} --no-patch
        Restart=always
        RestartSec=10
        StandardOutput=append:{repo_dir / LOGS_DIR}/systemd.log
        StandardError=append:{repo_dir / LOGS_DIR}/systemd.log
        Environment=PYTHONUNBUFFERED=1

        [Install]
        WantedBy=multi-user.target
    """)


def install_systemd_unit(repo_dir: Path, venv_python: Path, log: logging.Logger) -> None:
    """Write and enable the systemd unit."""
    unit_content = generate_systemd_unit(repo_dir, venv_python)
    unit_path = repo_dir / "greed-crypto.service"
    unit_path.write_text(unit_content, encoding="utf-8")
    log.info("Wrote systemd unit: %s", unit_path)

    system_unit = Path("/etc/systemd/system/greed-crypto.service")
    try:
        shutil.copy2(unit_path, system_unit)
        subprocess.run(["systemctl", "daemon-reload"],      check=True)
        subprocess.run(["systemctl", "enable", "greed-crypto"], check=True)
        subprocess.run(["systemctl", "start",  "greed-crypto"], check=True)
        log.info("systemd unit installed, enabled, and started.")
        log.info("Check status with: systemctl status greed-crypto")
    except (PermissionError, subprocess.CalledProcessError) as exc:
        log.warning(
            "Could not install systemd unit automatically: %s\n"
            "To install manually, run:\n"
            "  sudo cp %s %s\n"
            "  sudo systemctl daemon-reload\n"
            "  sudo systemctl enable greed-crypto\n"
            "  sudo systemctl start  greed-crypto",
            exc, unit_path, system_unit
        )


# ════════════════════════════════════════════════════════════
# SECTION 10 — Bot Supervisor
# ════════════════════════════════════════════════════════════

class BotSupervisor:
    """
    Supervise the greed bot subprocess.

    * Starts `python core.py` inside the repo virtualenv.
    * On crash, logs the error to logs/crash.log and restarts with
      exponential backoff (capped at MAX_RESTART_DELAY seconds).
    * Every HEARTBEAT_INTERVAL seconds, calls getMe on the bot API
      to verify the bot is responsive.
    """

    def __init__(self, repo_dir: Path, venv_python: Path, log: logging.Logger):
        self.repo_dir     = repo_dir
        self.venv_python  = venv_python
        self.log          = log
        self.crash_log    = repo_dir / LOGS_DIR / "crash.log"
        self._proc: Optional[subprocess.Popen] = None
        self._stop_evt    = threading.Event()
        self._hb_thread: Optional[threading.Thread] = None
        self._restart_delay = RESTART_BACKOFF_BASE

        # Read bot token for health-checks
        self._bot_token: Optional[str] = os.environ.get("GREED_TOKEN")
        if not self._bot_token:
            self._bot_token = self._read_token_from_config()

    def _read_token_from_config(self) -> Optional[str]:
        """Try to read the bot token from config/config.toml."""
        cfg_path = self.repo_dir / "config" / "config.toml"
        try:
            import toml
            if cfg_path.exists():
                data = toml.load(str(cfg_path))
                return data.get("Telegram", {}).get("token")
        except Exception:
            pass
        return None

    def _start_bot(self) -> subprocess.Popen:
        """Launch core.py as a subprocess inside the repo virtualenv."""
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        proc = subprocess.Popen(
            [str(self.venv_python), str(self.repo_dir / "core.py")],
            cwd=str(self.repo_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        self.log.info("Bot started — PID %d", proc.pid)
        return proc

    def _drain_output(self, proc: subprocess.Popen) -> str:
        """Read all remaining stdout/stderr from a finished process."""
        try:
            out, _ = proc.communicate(timeout=5)
            return out or ""
        except subprocess.TimeoutExpired:
            proc.kill()
            out, _ = proc.communicate()
            return out or ""
        except Exception:
            return ""

    def _log_crash(self, return_code: int, output: str) -> None:
        """Append crash info to logs/crash.log."""
        (self.repo_dir / LOGS_DIR).mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().isoformat()
        with open(self.crash_log, "a", encoding="utf-8") as fh:
            fh.write(f"\n{'='*60}\n")
            fh.write(f"CRASH at {ts} — return code {return_code}\n")
            fh.write(output[-4000:] if len(output) > 4000 else output)
            fh.write(f"\n{'='*60}\n")

    def _heartbeat_loop(self) -> None:
        """Periodically call getMe to verify bot responsiveness."""
        if not self._bot_token:
            self.log.warning("No bot token available; heartbeat disabled.")
            return

        try:
            import requests
        except ImportError:
            self.log.warning("requests not installed; heartbeat disabled.")
            return

        url = f"https://api.telegram.org/bot{self._bot_token}/getMe"
        while not self._stop_evt.is_set():
            self._stop_evt.wait(HEARTBEAT_INTERVAL)
            if self._stop_evt.is_set():
                break
            try:
                resp = requests.get(url, timeout=10)
                if resp.ok and resp.json().get("ok"):
                    self.log.debug("Heartbeat OK — bot is alive.")
                else:
                    self.log.warning("Heartbeat FAILED: %s", resp.text[:200])
            except Exception as exc:
                self.log.warning("Heartbeat exception: %s", exc)

    def run(self) -> None:
        """Main supervisor loop — blocks until a SIGTERM/SIGINT is received."""
        self.log.info("Supervisor starting. Press Ctrl+C to stop.")

        def _handle_signal(signum, frame):
            self.log.info("Received signal %d; shutting down.", signum)
            self._stop_evt.set()
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()

        signal.signal(signal.SIGTERM, _handle_signal)
        signal.signal(signal.SIGINT,  _handle_signal)

        # Start heartbeat thread
        self._hb_thread = threading.Thread(
            target=self._heartbeat_loop, name="heartbeat", daemon=True
        )
        self._hb_thread.start()

        while not self._stop_evt.is_set():
            self.log.info("Starting bot subprocess…")
            try:
                self._proc = self._start_bot()
            except Exception as exc:
                self.log.error("Failed to start bot: %s", exc)
                self._stop_evt.wait(self._restart_delay)
                self._restart_delay = min(self._restart_delay * 2, MAX_RESTART_DELAY)
                continue

            # Stream output while waiting for the process
            output_lines: List[str] = []
            try:
                assert self._proc.stdout is not None
                for line in self._proc.stdout:
                    print(line, end="", flush=True)
                    output_lines.append(line)
                    if self._stop_evt.is_set():
                        break
            except Exception:
                pass

            rc = self._proc.wait()
            if self._stop_evt.is_set():
                self.log.info("Supervisor stopped by request.")
                break

            output = "".join(output_lines)
            self.log.error("Bot exited with code %d. Logging crash.", rc)
            self._log_crash(rc, output)

            self.log.info(
                "Restarting in %d second(s) (backoff=%.0fs)…",
                self._restart_delay, self._restart_delay
            )
            self._stop_evt.wait(self._restart_delay)
            if self._stop_evt.is_set():
                break
            # Increase backoff, capped at MAX_RESTART_DELAY
            self._restart_delay = min(self._restart_delay * 2, MAX_RESTART_DELAY)

        self.log.info("Supervisor exited cleanly.")


# ════════════════════════════════════════════════════════════
# SECTION 11 — Main Orchestration
# ════════════════════════════════════════════════════════════

# Module-level logger (used by _replace_method helper before setup_logging)
log_global = logging.getLogger("greed_refactor")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="greed_cryptorefactor — patch and supervise the greed Telegram bot."
    )
    parser.add_argument(
        "--setup-only", action="store_true",
        help="Patch files and exit without starting the supervisor."
    )
    parser.add_argument(
        "--install-systemd", action="store_true",
        help="Install the systemd unit after patching."
    )
    parser.add_argument(
        "--no-patch", action="store_true",
        help="Skip patching; go straight to the supervisor."
    )
    args = parser.parse_args()

    # ── Locate repo ────────────────────────────────────────────────────────────
    try:
        repo_dir = find_repo_dir()
    except FileNotFoundError:
        # Try cloning
        repo_dir = clone_repo_if_missing(Path.cwd(), logging.getLogger("init"))

    # ── Setup logging ──────────────────────────────────────────────────────────
    log = setup_logging(repo_dir / LOGS_DIR)
    log.info("Repo directory: %s", repo_dir)

    # ── Virtualenv ─────────────────────────────────────────────────────────────
    venv_python = ensure_venv(repo_dir, log)

    # ── Install dependencies ───────────────────────────────────────────────────
    try:
        install_dependencies(venv_python, repo_dir, log)
    except subprocess.CalledProcessError as exc:
        log.error("Dependency installation failed: %s", exc)

    if not args.no_patch:
        # ── Diagnostics ────────────────────────────────────────────────────────
        run_diagnostics(repo_dir, log)

        # ── Write new module files ─────────────────────────────────────────────
        log.info("Writing crypto/mode module files…")
        write_all_files(repo_dir, log)

        # ── Patch worker.py ────────────────────────────────────────────────────
        log.info("Patching worker.py…")
        patch_worker_py(repo_dir, log)

        # ── Generate systemd unit ──────────────────────────────────────────────
        unit_path = repo_dir / "greed-crypto.service"
        unit_path.write_text(generate_systemd_unit(repo_dir, venv_python), encoding="utf-8")
        log.info("Systemd unit written to: %s", unit_path)

        if args.install_systemd:
            install_systemd_unit(repo_dir, venv_python, log)

        # ── Final diagnostics ──────────────────────────────────────────────────
        log.info("Running post-patch diagnostics…")
        run_diagnostics(repo_dir, log)

        log.info(
            "\n"
            "╔══════════════════════════════════════════════════════════╗\n"
            "║  greed_cryptorefactor — Setup Complete!                  ║\n"
            "╠══════════════════════════════════════════════════════════╣\n"
            "║  Next steps:                                             ║\n"
            "║  1. Edit config/config.toml  (set Telegram token etc.)   ║\n"
            "║  2. Edit config/crypto_addresses.toml  (your addresses)  ║\n"
            "║  3. Edit config/mode_config.toml       (active mode)     ║\n"
            "╚══════════════════════════════════════════════════════════╝"
        )

    if args.setup_only:
        log.info("--setup-only flag set. Exiting without starting the bot.")
        return

    # ── Start supervisor ───────────────────────────────────────────────────────
    supervisor = BotSupervisor(repo_dir, venv_python, log)
    supervisor.run()


if __name__ == "__main__":
    main()
