"""
crypto_manager.py
CryptoCurrency Payment Manager for greed bot.
Loads owner deposit addresses from config/crypto_addresses.toml,
fetches live rates from CoinGecko (60 s cache), and converts fiat totals
to exact crypto amounts.
"""
from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

log = logging.getLogger(__name__)

# Try to import toml; fall back to a minimal manual parser
try:
    import toml as _toml
    def _load_toml(path: str) -> dict:
        return _toml.load(path)
except ImportError:
    _toml = None  # type: ignore
    def _load_toml(path: str) -> dict:  # type: ignore[misc]
        """Minimal TOML parser: handles [section], key = "value", key = number."""
        result: dict = {}
        current: dict = result
        with open(path, encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    section = line[1:-1].strip()
                    parts = section.split(".")
                    node = result
                    for part in parts:
                        node = node.setdefault(part, {})
                    current = node
                    continue
                if "=" in line:
                    key, _, val = line.partition("=")
                    key = key.strip()
                    val = val.strip()
                    if val.startswith('"') or val.startswith("'"):
                        val = val[1:-1]
                    elif val.lower() in ("true", "false"):
                        val = val.lower() == "true"
                    else:
                        try:
                            val = int(val)
                        except ValueError:
                            try:
                                val = float(val)
                            except ValueError:
                                pass
                    current[key] = val
        return result

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
            cfg = _load_toml(str(self.config_path))
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
            f"\U0001f4b0 Send exactly: <code>{amount} {coin}</code>\n"
            f"\U0001f4eb To address: <code>{address}</code>\n"
            f"\U0001f4b6 Fiat equivalent: {currency_symbol}{fiat_val:.2f}\n"
            f"\U0001f4ca Rate: 1 {coin} = {currency_symbol}{rate:,.4f}\n\n"
            f"QR data: <code>{qr}</code>\n\n"
            f"\u23f3 After sending, notify the owner to confirm your payment."
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

    # ── Swap Quote ───────────────────────────────────────────────────────
    def get_swap_quote(
        self,
        coin_in: str,
        coin_out: str,
        amount_in: float,
        fiat: str = "eur",
        spread_pct: float = 1.5,
    ) -> Optional[dict]:
        """
        Calculate a swap quote: coin_in → coin_out.
        Returns dict with amount_in, coin_in, amount_out, coin_out, spread_pct,
        fiat_value, rate_in, rate_out; or None if rates unavailable.
        """
        rate_in = self.get_live_rate(coin_in.upper(), fiat)
        rate_out = self.get_live_rate(coin_out.upper(), fiat)
        if not rate_in or not rate_out:
            return None
        fiat_val = amount_in * rate_in
        amount_out = round(fiat_val / rate_out * (1 - spread_pct / 100), 8)
        return {
            "coin_in": coin_in.upper(),
            "coin_out": coin_out.upper(),
            "amount_in": amount_in,
            "amount_out": amount_out,
            "rate_in": rate_in,
            "rate_out": rate_out,
            "fiat_value": fiat_val,
            "spread_pct": spread_pct,
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
