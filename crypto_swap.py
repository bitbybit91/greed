"""crypto_swap.py — Core cryptocurrency swap engine for greed.

Provides:
  - CoinGeckoClient: fetches and caches prices from the CoinGecko free API.
  - SwapEngine: validates, quotes, and executes swaps atomically.
  - Custom exceptions for all error conditions.
"""

import logging
import threading
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from typing import Dict, List, Optional

import requests
import sqlalchemy
import sqlalchemy.orm

import database as db

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class PriceFetchError(Exception):
    """Raised when current prices cannot be fetched and no cache is available."""


class InsufficientBalanceError(Exception):
    """Raised when the user does not have enough balance to complete a swap."""


class SwapError(Exception):
    """Generic swap execution error."""


class PairNotSupportedError(Exception):
    """Raised when the requested trading pair is not supported."""


# ---------------------------------------------------------------------------
# CoinGecko price client
# ---------------------------------------------------------------------------

class CoinGeckoClient:
    """Fetches cryptocurrency prices from the CoinGecko free API with in-memory caching."""

    def __init__(self, api_url: str, cache_ttl: int):
        self._api_url = api_url
        self._cache_ttl = cache_ttl
        self._lock = threading.Lock()
        # {(coin_id, vs_currency): (Decimal price, datetime fetched_at)}
        self._price_cache: Dict[tuple, tuple] = {}

    def _is_cache_valid(self, key: tuple) -> bool:
        """Return True if the cached entry for key is still within TTL."""
        entry = self._price_cache.get(key)
        if entry is None:
            return False
        _, fetched_at = entry
        return datetime.utcnow() - fetched_at < timedelta(seconds=self._cache_ttl)

    def fetch_prices(self, coin_ids: List[str], vs_currency: str = "usd") -> Dict[str, Decimal]:
        """Fetch prices for multiple coins at once. Falls back to cache on network errors.

        Returns a dict mapping coin_id -> Decimal price.
        Raises PriceFetchError if the API fails AND no cached data exists.
        """
        ids_param = ",".join(coin_ids)
        try:
            response = requests.get(
                self._api_url,
                params={"ids": ids_param, "vs_currencies": vs_currency},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            log.warning(f"CoinGecko API error: {exc}. Falling back to cache.")
            data = None

        result: Dict[str, Decimal] = {}
        now = datetime.utcnow()

        for coin_id in coin_ids:
            key = (coin_id, vs_currency)
            if data is not None and coin_id in data and vs_currency in data[coin_id]:
                price = Decimal(str(data[coin_id][vs_currency]))
                with self._lock:
                    self._price_cache[key] = (price, now)
                result[coin_id] = price
            else:
                # Try to use stale cache
                with self._lock:
                    cached = self._price_cache.get(key)
                if cached is not None:
                    result[coin_id] = cached[0]
                    log.debug(f"Using stale cache for {coin_id}/{vs_currency}")
                else:
                    log.error(f"No price data available for {coin_id}/{vs_currency}")

        if not result and not data:
            raise PriceFetchError(
                f"Unable to fetch prices for {coin_ids} and no cached data available."
            )
        return result

    def get_price(self, coin_id: str, vs_currency: str = "usd") -> Decimal:
        """Return the price for a single coin, using cache if still valid."""
        key = (coin_id, vs_currency)
        with self._lock:
            if self._is_cache_valid(key):
                return self._price_cache[key][0]
        # Cache miss or expired — fetch fresh
        prices = self.fetch_prices([coin_id], vs_currency)
        if coin_id not in prices:
            raise PriceFetchError(f"Price for {coin_id} not available.")
        return prices[coin_id]

    def get_exchange_rate(self, source_coin_id: str, dest_coin_id: str) -> Decimal:
        """Return how many dest_coin_id units equal one source_coin_id unit.

        rate = source_price_usd / dest_price_usd
        """
        prices = self.fetch_prices([source_coin_id, dest_coin_id])
        src_price = prices.get(source_coin_id)
        dst_price = prices.get(dest_coin_id)
        if src_price is None:
            raise PriceFetchError(f"Price for source {source_coin_id} not available.")
        if dst_price is None:
            raise PriceFetchError(f"Price for destination {dest_coin_id} not available.")
        if dst_price == 0:
            raise SwapError(f"Destination price for {dest_coin_id} is zero.")
        return src_price / dst_price


# ---------------------------------------------------------------------------
# Swap engine
# ---------------------------------------------------------------------------

class SwapEngine:
    """Thread-safe cryptocurrency swap engine.

    Reads configuration from cfg, uses CoinGeckoClient for pricing,
    and executes swaps atomically via SQLAlchemy sessions.
    """

    def __init__(self, cfg, db_engine):
        self._cfg = cfg
        self._db_engine = db_engine
        self._lock = threading.Lock()

        swap_cfg = cfg["CryptoSwap"]
        self._coingecko = CoinGeckoClient(
            api_url=swap_cfg["price_api_url"],
            cache_ttl=swap_cfg["price_cache_ttl"],
        )
        # Build symbol -> coingecko_id mapping from config
        self._symbol_to_coingecko: Dict[str, str] = {
            symbol.upper(): cg_id
            for symbol, cg_id in swap_cfg["Coins"].items()
        }
        self._fee_pct = Decimal(str(swap_cfg["fee_percentage"]))
        self._quote_timeout = int(swap_cfg["quote_timeout"])
        self._min_usd = Decimal(str(swap_cfg["min_swap_usd"]))
        self._max_usd = Decimal(str(swap_cfg["max_swap_usd"]))

        # Fee addresses: {SYMBOL: address}
        self._fee_addresses: Dict[str, str] = {
            symbol.upper(): addr
            for symbol, addr in swap_cfg.get("FeeAddresses", {}).items()
        }
        # Deposit addresses shown to users: {SYMBOL: address}
        self._deposit_addresses: Dict[str, str] = {
            symbol.upper(): addr
            for symbol, addr in swap_cfg.get("DepositAddresses", {}).items()
        }

    def _new_session(self):
        return sqlalchemy.orm.sessionmaker(bind=self._db_engine, expire_on_commit=False)()

    # ------------------------------------------------------------------
    # Currency helpers
    # ------------------------------------------------------------------

    def get_supported_currencies(self) -> List[str]:
        """Return a sorted list of supported currency symbols."""
        return sorted(self._symbol_to_coingecko.keys())

    def get_deposit_address(self, currency: str) -> Optional[str]:
        """Return the deposit address for a currency, or None if not configured."""
        return self._deposit_addresses.get(currency.upper())

    def get_fee_address(self, currency: str) -> Optional[str]:
        """Return the operator fee address for a currency."""
        return self._fee_addresses.get(currency.upper())

    @property
    def quote_timeout(self) -> int:
        """How long a swap quote remains valid, in seconds."""
        return self._quote_timeout

    def _symbol_to_cg(self, symbol: str) -> str:
        cg_id = self._symbol_to_coingecko.get(symbol.upper())
        if cg_id is None:
            raise PairNotSupportedError(f"Currency {symbol} is not supported.")
        return cg_id

    # ------------------------------------------------------------------
    # Pricing
    # ------------------------------------------------------------------

    def get_all_prices_usd(self) -> Dict[str, Decimal]:
        """Return current USD prices for all supported currencies, mapped by symbol."""
        coin_ids = list(self._symbol_to_coingecko.values())
        prices_by_id = self._coingecko.fetch_prices(coin_ids, "usd")
        return {
            symbol: prices_by_id[cg_id]
            for symbol, cg_id in self._symbol_to_coingecko.items()
            if cg_id in prices_by_id
        }

    def get_exchange_rate(self, src_symbol: str, dst_symbol: str) -> Decimal:
        """Return how many dst_symbol units equal one src_symbol unit."""
        src_cg = self._symbol_to_cg(src_symbol)
        dst_cg = self._symbol_to_cg(dst_symbol)
        return self._coingecko.get_exchange_rate(src_cg, dst_cg)

    # ------------------------------------------------------------------
    # Quote generation
    # ------------------------------------------------------------------

    def generate_quote(
        self,
        src: str,
        dst: str,
        amount: Decimal,
    ) -> dict:
        """Calculate a swap quote.

        Returns a dict with:
          - source_currency, destination_currency
          - source_amount, destination_amount
          - exchange_rate
          - fee_amount, fee_currency (taken from destination)
          - usd_value (approximate)
          - expires_at (datetime)
          - operator_fee_address
        Raises PairNotSupportedError, PriceFetchError, SwapError on errors.
        """
        src = src.upper()
        dst = dst.upper()
        if src == dst:
            raise SwapError("Source and destination currencies must be different.")
        if src not in self._symbol_to_coingecko:
            raise PairNotSupportedError(f"{src} is not supported.")
        if dst not in self._symbol_to_coingecko:
            raise PairNotSupportedError(f"{dst} is not supported.")

        # Get prices
        src_usd = self._coingecko.get_price(self._symbol_to_cg(src), "usd")
        dst_usd = self._coingecko.get_price(self._symbol_to_cg(dst), "usd")
        rate = src_usd / dst_usd

        # Validate amount bounds (USD equivalent)
        usd_value = amount * src_usd
        if usd_value < self._min_usd:
            raise SwapError(
                f"Swap value ${usd_value:.2f} is below the minimum ${self._min_usd:.2f}."
            )
        if usd_value > self._max_usd:
            raise SwapError(
                f"Swap value ${usd_value:.2f} exceeds the maximum ${self._max_usd:.2f}."
            )

        # Calculate gross destination amount
        gross_dst = (amount * rate).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)
        # Fee taken from destination amount
        fee_amount = (gross_dst * self._fee_pct / Decimal("100")).quantize(
            Decimal("0.00000001"), rounding=ROUND_DOWN
        )
        net_dst = gross_dst - fee_amount

        expires_at = datetime.utcnow() + timedelta(seconds=self._quote_timeout)

        return {
            "source_currency": src,
            "destination_currency": dst,
            "source_amount": amount,
            "destination_amount": net_dst,
            "exchange_rate": rate,
            "fee_amount": fee_amount,
            "fee_currency": dst,
            "usd_value": usd_value,
            "expires_at": expires_at,
            "operator_fee_address": self.get_fee_address(dst),
        }

    # ------------------------------------------------------------------
    # Swap execution
    # ------------------------------------------------------------------

    def execute_swap(
        self,
        user_id: int,
        src: str,
        dst: str,
        amount: Decimal,
        quoted_rate: Decimal,
    ) -> db.SwapOrder:
        """Execute a swap atomically.

        Debits src wallet, credits dst wallet (minus fee), records SwapOrder and FeeCollection.
        Raises InsufficientBalanceError if the user lacks sufficient src balance.
        """
        src = src.upper()
        dst = dst.upper()
        quote = self.generate_quote(src, dst, amount)

        with self._lock:
            session = self._new_session()
            try:
                now = datetime.utcnow()

                # Get or create source wallet
                src_wallet = session.query(db.CryptoWallet).filter_by(
                    user_id=user_id, currency=src
                ).with_for_update().first()
                if src_wallet is None or src_wallet.get_balance() < amount:
                    available = src_wallet.get_balance() if src_wallet else Decimal("0")
                    raise InsufficientBalanceError(
                        f"Insufficient {src} balance. Available: {available}, required: {amount}."
                    )

                # Debit source wallet
                src_wallet.set_balance(src_wallet.get_balance() - amount)
                src_wallet.updated_at = now

                # Get or create destination wallet
                dst_wallet = session.query(db.CryptoWallet).filter_by(
                    user_id=user_id, currency=dst
                ).with_for_update().first()
                if dst_wallet is None:
                    dst_wallet = db.CryptoWallet(
                        user_id=user_id,
                        currency=dst,
                        balance="0",
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(dst_wallet)
                    session.flush()

                # Credit destination wallet (net of fee)
                dst_wallet.set_balance(dst_wallet.get_balance() + quote["destination_amount"])
                dst_wallet.updated_at = now

                # Create swap order record
                swap_order = db.SwapOrder(
                    user_id=user_id,
                    source_currency=src,
                    destination_currency=dst,
                    source_amount=str(amount),
                    destination_amount=str(quote["destination_amount"]),
                    exchange_rate=str(quote["exchange_rate"]),
                    fee_amount=str(quote["fee_amount"]),
                    fee_currency=dst,
                    status="completed",
                    created_at=now,
                    completed_at=now,
                    operator_fee_address=quote["operator_fee_address"],
                )
                session.add(swap_order)
                session.flush()

                # Create fee collection record
                fee_record = db.FeeCollection(
                    swap_id=swap_order.swap_id,
                    currency=dst,
                    amount=str(quote["fee_amount"]),
                    operator_address=quote["operator_fee_address"],
                    created_at=now,
                )
                session.add(fee_record)

                session.commit()
                log.info(
                    f"Swap {swap_order.swap_id} completed: user={user_id} "
                    f"{amount} {src} -> {quote['destination_amount']} {dst} "
                    f"(fee={quote['fee_amount']} {dst})"
                )
                return swap_order
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

    # ------------------------------------------------------------------
    # Wallet management
    # ------------------------------------------------------------------

    def deposit_to_wallet(self, user_id: int, currency: str, amount: Decimal) -> db.CryptoWallet:
        """Credit a user's wallet (admin deposit or test). Creates wallet if needed."""
        currency = currency.upper()
        session = self._new_session()
        try:
            now = datetime.utcnow()
            wallet = session.query(db.CryptoWallet).filter_by(
                user_id=user_id, currency=currency
            ).first()
            if wallet is None:
                wallet = db.CryptoWallet(
                    user_id=user_id,
                    currency=currency,
                    balance="0",
                    created_at=now,
                    updated_at=now,
                )
                session.add(wallet)
                session.flush()
            wallet.set_balance(wallet.get_balance() + amount)
            wallet.updated_at = now
            session.commit()
            log.info(f"Deposited {amount} {currency} to user {user_id}")
            return wallet
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_user_wallets(self, user_id: int) -> List[db.CryptoWallet]:
        """Return all CryptoWallet records for a user."""
        session = self._new_session()
        try:
            return session.query(db.CryptoWallet).filter_by(user_id=user_id).all()
        finally:
            session.close()

    # ------------------------------------------------------------------
    # History / reporting
    # ------------------------------------------------------------------

    def get_user_swaps(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> List[db.SwapOrder]:
        """Return a user's swap orders in descending chronological order."""
        session = self._new_session()
        try:
            return (
                session.query(db.SwapOrder)
                .filter_by(user_id=user_id)
                .order_by(db.SwapOrder.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )
        finally:
            session.close()

    def get_pending_swaps(self) -> List[db.SwapOrder]:
        """Return all swap orders with status 'pending' (admin view)."""
        session = self._new_session()
        try:
            return (
                session.query(db.SwapOrder)
                .filter_by(status="pending")
                .order_by(db.SwapOrder.created_at.desc())
                .all()
            )
        finally:
            session.close()

    def admin_get_fee_summary(self) -> Dict[str, Decimal]:
        """Return a dict mapping currency -> total fees collected."""
        session = self._new_session()
        try:
            records = session.query(db.FeeCollection).all()
            summary: Dict[str, Decimal] = {}
            for rec in records:
                currency = rec.currency
                summary[currency] = summary.get(currency, Decimal("0")) + Decimal(rec.amount)
            return summary
        finally:
            session.close()
