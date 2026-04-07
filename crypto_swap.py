import logging
import threading
import time
from decimal import Decimal, ROUND_DOWN
from typing import Dict, Optional

import requests

import nuconfig
import utils

log = logging.getLogger(__name__)


class CoinGeckoClient:
    """Thread-safe CoinGecko API client with response caching."""

    def __init__(self, base_url: str = "https://api.coingecko.com/api/v3", cache_ttl: int = 60):
        self._base_url = base_url.rstrip("/")
        self._cache_ttl = cache_ttl
        self._price_cache: Dict[str, dict] = {}
        self._cache_timestamp: float = 0.0
        self._lock = threading.Lock()

    def get_price(self, coingecko_ids: list, vs_currency: str = "usd") -> Dict[str, Decimal]:
        """Fetch current prices for a list of CoinGecko coin IDs.
        Returns a dict mapping coingecko_id -> Decimal price in vs_currency."""
        now = time.time()
        cache_key = f"{','.join(sorted(coingecko_ids))}:{vs_currency}"

        with self._lock:
            if now - self._cache_timestamp < self._cache_ttl and cache_key in self._price_cache:
                return self._price_cache[cache_key]

        try:
            ids_param = ",".join(coingecko_ids)
            resp = requests.get(
                f"{self._base_url}/simple/price",
                params={"ids": ids_param, "vs_currencies": vs_currency},
                timeout=15
            )
            resp.raise_for_status()
            data = resp.json()
        except (requests.RequestException, ValueError) as e:
            log.error(f"CoinGecko API error: {e}")
            with self._lock:
                if cache_key in self._price_cache:
                    return self._price_cache[cache_key]
            return {}

        result = {}
        for cg_id in coingecko_ids:
            if cg_id in data and vs_currency in data[cg_id]:
                result[cg_id] = Decimal(str(data[cg_id][vs_currency]))

        with self._lock:
            self._price_cache[cache_key] = result
            self._cache_timestamp = now

        return result


class SwapEngine:
    """Thread-safe crypto swap engine backed by CoinGecko prices.
    Reads coin configuration dynamically from the NuConfig object."""

    def __init__(self, cfg: nuconfig.NuConfig):
        self.cfg = cfg
        swap_cfg = cfg["CryptoSwap"]
        self._client = CoinGeckoClient(
            base_url=swap_cfg.get("price_api", "https://api.coingecko.com/api/v3"),
            cache_ttl=swap_cfg.get("cache_ttl", 60)
        )
        self._fee_pct = Decimal(str(swap_cfg.get("fee_percentage", 1.0)))
        self._quote_timeout = swap_cfg.get("quote_timeout", 60)
        self._min_usd = Decimal(str(swap_cfg.get("min_usd", 10.0)))
        self._max_usd = Decimal(str(swap_cfg.get("max_usd", 10000.0)))

        # Build symbol -> coingecko_id mapping from config
        self._symbol_to_coingecko: Dict[str, str] = {}
        coins_cfg = swap_cfg.get("Coins", {})
        for symbol, cg_id in coins_cfg.items():
            self._symbol_to_coingecko[symbol] = cg_id

        log.info(f"SwapEngine initialized with coins: {list(self._symbol_to_coingecko.keys())}")

    @property
    def supported_coins(self) -> list:
        """Return list of supported coin symbols."""
        return list(self._symbol_to_coingecko.keys())

    @property
    def quote_timeout(self) -> int:
        """Return the quote timeout in seconds."""
        return self._quote_timeout

    def get_all_prices_usd(self) -> Dict[str, Decimal]:
        """Fetch USD prices for all supported coins.
        Returns dict mapping symbol -> Decimal USD price."""
        if not self._symbol_to_coingecko:
            return {}

        cg_ids = list(self._symbol_to_coingecko.values())
        raw_prices = self._client.get_price(cg_ids, "usd")

        # Reverse map: coingecko_id -> symbol
        id_to_symbol = {v: k for k, v in self._symbol_to_coingecko.items()}
        result = {}
        for cg_id, price in raw_prices.items():
            symbol = id_to_symbol.get(cg_id)
            if symbol:
                result[symbol] = price

        return result

    def get_price_usd(self, symbol: str) -> Optional[Decimal]:
        """Get the USD price for a single coin symbol."""
        cg_id = self._symbol_to_coingecko.get(symbol)
        if not cg_id:
            log.warning(f"Unknown coin symbol: {symbol}")
            return None

        prices = self._client.get_price([cg_id], "usd")
        return prices.get(cg_id)

    def calculate_crypto_amount(self, usd_amount: Decimal, symbol: str) -> Optional[Decimal]:
        """Calculate the amount of crypto needed for a given USD amount.
        Includes the fee percentage. Returns None if price unavailable."""
        price = self.get_price_usd(symbol)
        if not price or price == 0:
            return None

        decimals = utils.CRYPTO_DECIMALS.get(symbol, 8)
        crypto_amount = usd_amount / price
        # Round down to the appropriate number of decimal places
        quantize_str = "0." + "0" * decimals
        return crypto_amount.quantize(Decimal(quantize_str), rounding=ROUND_DOWN)

    def get_deposit_address(self, symbol: str) -> Optional[str]:
        """Get the operator's deposit address for a given coin."""
        try:
            addresses = self.cfg["CryptoSwap"]["DepositAddresses"]
            return addresses.get(symbol)
        except (KeyError, TypeError):
            log.error(f"No deposit address configured for {symbol}")
            return None

    def get_fee_address(self, symbol: str) -> Optional[str]:
        """Get the operator's fee collection address for a given coin."""
        try:
            addresses = self.cfg["CryptoSwap"]["FeeAddresses"]
            return addresses.get(symbol)
        except (KeyError, TypeError):
            log.error(f"No fee address configured for {symbol}")
            return None

    def validate_address(self, symbol: str, address: str) -> bool:
        """Validate a cryptocurrency address format."""
        pattern = utils.ADDR_PATTERNS.get(symbol)
        if not pattern:
            log.warning(f"No address pattern for {symbol}")
            return False
        return bool(pattern.match(address))
