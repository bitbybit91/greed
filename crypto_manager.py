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
            return "\u274c Payment information unavailable. Please try again."
        coin    = info["coin"]
        amt     = info["crypto_amount"]
        addr    = info["address"]
        fiat    = info["fiat_amount"]
        sym     = info["fiat_symbol"]
        rate    = info["rate"]
        return (
            f"\U0001f4b0 <b>Crypto Payment Request</b>\n\n"
            f"\U0001fa99 <b>Coin:</b> {coin}\n"
            f"\U0001f4b5 <b>Fiat Amount:</b> {sym}{fiat:.2f}\n"
            f"\U0001f4ca <b>Live Rate:</b> {sym}{rate:,.4f} / {coin}\n"
            f"\U0001f4b1 <b>Send Exactly:</b> <code>{amt:.8f} {coin}</code>\n\n"
            f"\U0001f4ec <b>Deposit Address:</b>\n<code>{addr}</code>\n\n"
            f"\u26a0\ufe0f After sending, press <b>I have paid</b> below.\n"
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
            description = _text(item, "{http://purl.org/rss/1.0/modules/content/}encoded")                        or _text(item, "description")
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
