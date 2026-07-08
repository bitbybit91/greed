from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

try:
    import tomllib as _toml_loader  # type: ignore[attr-defined]
except ImportError:
    try:
        import toml as _toml_loader  # type: ignore[no-redef]
    except ImportError:
        _toml_loader = None

log = logging.getLogger(__name__)

COINGECKO_IDS: Dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "XMR": "monero",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BNB": "binancecoin",
    "LTC": "litecoin",
    "DOGE": "dogecoin",
    "SOL": "solana",
    "TRX": "tron",
    "MATIC": "matic-network",
    "ADA": "cardano",
}
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
CACHE_TTL = 60


def _strip_wrapping_quotes(value: str) -> str:
    """Remove matching outer quotes only; unmatched quotes are kept as-is."""
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


class CryptoPaymentManager:
    def __init__(self, config_path: str = "config/crypto_addresses.toml"):
        self.config_path = Path(config_path)
        self.addresses: Dict[str, str] = {}
        self._cache: Dict[str, Tuple[float, float]] = {}
        self._fallback: Dict[str, float] = {}
        self._session = requests.Session()
        self.load_addresses()

    def _load_config(self) -> dict:
        if not self.config_path.exists():
            return {}
        if _toml_loader is not None:
            try:
                if hasattr(_toml_loader, "load"):
                    return _toml_loader.load(str(self.config_path))
                return _toml_loader.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception as exc:
                log.warning("Failed to parse %s via TOML loader: %s", self.config_path, exc)
        try:
            return self._load_config_fallback()
        except Exception as exc:
            log.warning("Failed to parse %s via fallback parser: %s", self.config_path, exc)
            return {}

    def _load_config_fallback(self) -> dict:
        content = self.config_path.read_text(encoding="utf-8")
        in_addresses = False
        addresses: Dict[str, str] = {}
        for raw_line in content.splitlines():
            line = raw_line.split("#", 1)[0].strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                in_addresses = line.strip() == "[addresses]"
                continue
            if not in_addresses or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip().upper()
            value = _strip_wrapping_quotes(value)
            addresses[key] = value
        return {"addresses": addresses}

    def load_addresses(self) -> None:
        if not self.config_path.exists():
            self.addresses = {}
            log.warning("Crypto addresses config not found: %s", self.config_path)
            return
        cfg = self._load_config()
        raw_addresses = cfg.get("addresses", {}) if isinstance(cfg, dict) else {}
        cleaned: Dict[str, str] = {}
        if isinstance(raw_addresses, dict):
            for coin, address in raw_addresses.items():
                cleaned[str(coin).upper()] = str(address).strip()
        self.addresses = cleaned
        log.info("Loaded %s configured crypto addresses", len(self.get_available_coins()))

    def get_available_coins(self) -> List[str]:
        return sorted([coin for coin, address in self.addresses.items() if str(address).strip()])

    def get_live_rate(self, coin: str, fiat: str = "eur") -> Optional[float]:
        coin = str(coin).upper()
        fiat = str(fiat).lower()
        key = f"{coin}_{fiat}"
        cached = self._cache.get(key)
        if cached and (time.time() - cached[1]) < CACHE_TTL:
            return cached[0]

        coin_id = COINGECKO_IDS.get(coin)
        if not coin_id:
            log.warning("No CoinGecko ID configured for %s", coin)
            return self._fallback.get(key)

        try:
            response = self._session.get(
                COINGECKO_URL,
                params={"ids": coin_id, "vs_currencies": fiat},
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json() or {}
            rate = float(payload[coin_id][fiat])
            if rate <= 0:
                raise ValueError(f"invalid exchange rate received for {coin}/{fiat}: {rate}")
            now = time.time()
            self._cache[key] = (rate, now)
            self._fallback[key] = rate
            return rate
        except Exception as exc:
            fallback = self._fallback.get(key)
            if fallback is not None:
                log.warning("CoinGecko unavailable for %s/%s, using cached fallback: %s", coin, fiat, exc)
                return fallback
            log.warning("CoinGecko unavailable for %s/%s and no fallback rate exists: %s", coin, fiat, exc)
            return None

    def fiat_to_crypto(
        self,
        fiat_cents: int,
        coin: str,
        currency_exp: int = 2,
        fiat: str = "eur",
    ) -> Optional[float]:
        rate = self.get_live_rate(coin, fiat)
        if rate is None or rate <= 0:
            return None
        fiat_value = float(fiat_cents) / float(10 ** currency_exp)
        return round(fiat_value / rate, 8)

    def get_payment_info(
        self,
        fiat_cents: int,
        coin: str,
        currency_exp: int = 2,
        fiat: str = "eur",
        currency_symbol: str = "€",
    ) -> Optional[dict]:
        coin = str(coin).upper()
        address = str(self.addresses.get(coin, "")).strip()
        if not address:
            log.warning("No address configured for %s", coin)
            return None
        amount = self.fiat_to_crypto(fiat_cents, coin, currency_exp, fiat)
        if amount is None:
            return None
        rate = self.get_live_rate(coin, fiat)
        if rate is None:
            return None
        fiat_value = float(fiat_cents) / float(10 ** currency_exp)
        qr_string = f"{coin.lower()}:{address}?amount={amount}"
        display = (
            f"💰 Send exactly: <code>{amount} {coin}</code>\n"
            f"📫 To address: <code>{address}</code>\n"
            f"💶 Fiat equivalent: {currency_symbol}{fiat_value:.2f}\n"
            f"📊 Rate: 1 {coin} = {currency_symbol}{rate:,.4f}\n\n"
            f"QR data: <code>{qr_string}</code>"
        )
        return {
            "coin": coin,
            "address": address,
            "amount": amount,
            "rate": rate,
            "fiat_amount": fiat_value,
            "fiat_symbol": currency_symbol,
            "qr_string": qr_string,
            "display": display,
        }

    def poll_address_for_payment(
        self,
        coin: str,
        address: str,
        expected_amount: float,
        timeout_seconds: int = 1800,
    ) -> bool:
        log.info(
            "[poll_stub] Watching %s address %s for %s %s (timeout=%ss)",
            coin,
            address[:12],
            expected_amount,
            coin,
            timeout_seconds,
        )
        return False
