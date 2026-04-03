"""crypto_swap.py — Core swap engine for the greed crypto swap platform.

Responsibilities:
- Fetch real-time exchange rates from a configurable price API (with TTL cache).
- Validate swap requests against supported trading pairs.
- Lock quoted prices for a configurable confirmation window.
- Execute swaps atomically: debit source wallet, credit destination wallet,
  record a SwapOrder, and persist a PriceHistory snapshot.
- Apply configurable fee percentages per pair.
- Thread-safe: uses a lock to prevent race conditions on balance updates.
"""

import datetime
import logging
import threading
import time
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple

import requests
import sqlalchemy.orm

import database as db
import utils

log = logging.getLogger(__name__)


class PriceFetchError(Exception):
    """Raised when the price API cannot be reached and no cached price is available."""


class PairNotSupportedError(Exception):
    """Raised when a requested trading pair is not configured or is inactive."""


class InsufficientBalanceError(Exception):
    """Raised when the user does not have enough of the source currency."""


class SwapExpiredError(Exception):
    """Raised when the quoted price has passed its confirmation timeout."""


class CryptoSwapEngine:
    """Thread-safe swap engine shared across all bot workers."""

    def __init__(self, cfg):
        """
        :param cfg: A :class:`nuconfig.NuConfig` instance with a ``[CryptoSwap]`` section.
        """
        self._cfg = cfg
        self._lock = threading.Lock()
        # price cache: maps pair string (e.g. "BTC/USDT") -> (price: Decimal, fetched_at: float)
        self._price_cache: Dict[str, Tuple[Decimal, float]] = {}
        # pending quotes: maps quote_id -> dict with quote metadata
        self._pending_quotes: Dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Price fetching
    # ------------------------------------------------------------------

    def _cache_ttl(self) -> int:
        try:
            return int(self._cfg["CryptoSwap"]["price_cache_ttl"])
        except (KeyError, TypeError, ValueError):
            return 60

    def _api_url(self) -> str:
        try:
            return self._cfg["CryptoSwap"]["price_api_url"]
        except KeyError:
            return "https://api.binance.com/api/v3/ticker/price"

    def _api_key(self) -> Optional[str]:
        try:
            return self._cfg["CryptoSwap"]["price_api_key"] or None
        except KeyError:
            return None

    def _confirmation_timeout(self) -> int:
        try:
            return int(self._cfg["CryptoSwap"]["swap_confirmation_timeout"])
        except (KeyError, TypeError, ValueError):
            return 60

    def fetch_price(self, base: str, quote: str) -> Decimal:
        """Return the current price of *base* in units of *quote*.

        Results are cached for :meth:`_cache_ttl` seconds.  If the API is
        unreachable, the cached price (however stale) is returned as a
        fallback.  If no cache exists, :class:`PriceFetchError` is raised.

        :raises PriceFetchError: when the API call fails and no cache exists.
        """
        pair = f"{base.upper()}/{quote.upper()}"
        now = time.monotonic()

        # Return cached value if still fresh
        if pair in self._price_cache:
            cached_price, cached_at = self._price_cache[pair]
            if now - cached_at < self._cache_ttl():
                log.debug(f"Cache hit for {pair}: {cached_price}")
                return cached_price

        # Attempt live fetch
        symbol = f"{base.upper()}{quote.upper()}"
        try:
            headers = {}
            if self._api_key():
                headers["X-MBX-APIKEY"] = self._api_key()
            resp = requests.get(
                self._api_url(),
                params={"symbol": symbol},
                headers=headers,
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            price = Decimal(str(data["price"]))
            with self._lock:
                self._price_cache[pair] = (price, now)
            log.debug(f"Fetched live price for {pair}: {price}")
            return price
        except Exception as exc:
            log.warning(f"Failed to fetch price for {pair}: {exc}")
            # Fall back to stale cache
            if pair in self._price_cache:
                stale_price, _ = self._price_cache[pair]
                log.warning(f"Using stale price for {pair}: {stale_price}")
                return stale_price
            raise PriceFetchError(f"Cannot fetch price for {pair} and no cache exists.") from exc

    # ------------------------------------------------------------------
    # Quote management
    # ------------------------------------------------------------------

    def create_quote(
        self,
        session: sqlalchemy.orm.Session,
        user_id: int,
        source_currency: str,
        destination_currency: str,
        source_amount: Decimal,
    ) -> dict:
        """Create a price-locked swap quote.

        :returns: A dict with keys ``quote_id``, ``source_currency``,
            ``destination_currency``, ``source_amount``,
            ``destination_amount``, ``exchange_rate``, ``fee_amount``,
            ``expires_at``.
        :raises PairNotSupportedError: if the pair is not active in the DB.
        :raises PriceFetchError: if the live price cannot be obtained.
        """
        src = source_currency.upper()
        dst = destination_currency.upper()

        # Check the pair is supported
        pair_record: Optional[db.SupportedPair] = (
            session.query(db.SupportedPair)
            .filter_by(base_currency=src, quote_currency=dst, is_active=True)
            .one_or_none()
        )
        if pair_record is None:
            raise PairNotSupportedError(f"{src}/{dst} is not a supported or active trading pair.")

        # Validate amount bounds
        if pair_record.min_amount is not None and source_amount < Decimal(str(pair_record.min_amount)):
            raise ValueError(
                f"Amount {source_amount} is below the minimum {pair_record.min_amount} for {src}/{dst}."
            )
        if pair_record.max_amount is not None and source_amount > Decimal(str(pair_record.max_amount)):
            raise ValueError(
                f"Amount {source_amount} exceeds the maximum {pair_record.max_amount} for {src}/{dst}."
            )

        rate = self.fetch_price(src, dst)
        fee_pct = Decimal(str(pair_record.fee_percentage))
        fee_amount = utils.calculate_swap_fee(source_amount, float(fee_pct))
        net_source = source_amount - fee_amount
        destination_amount = net_source * rate

        import uuid
        quote_id = str(uuid.uuid4())
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=self._confirmation_timeout())

        quote = {
            "quote_id": quote_id,
            "user_id": user_id,
            "source_currency": src,
            "destination_currency": dst,
            "source_amount": source_amount,
            "destination_amount": destination_amount,
            "exchange_rate": rate,
            "fee_amount": fee_amount,
            "expires_at": expires_at,
        }
        with self._lock:
            self._pending_quotes[quote_id] = quote
        log.info(f"Created quote {quote_id} for user {user_id}: {source_amount} {src} -> {destination_amount} {dst}")
        return quote

    def execute_swap(self, session: sqlalchemy.orm.Session, quote_id: str) -> db.SwapOrder:
        """Execute a previously created quote.

        Atomically debits the source wallet, credits the destination wallet,
        records a :class:`~database.SwapOrder`, and persists a
        :class:`~database.PriceHistory` entry.

        :raises SwapExpiredError: if the quote has timed out.
        :raises InsufficientBalanceError: if the user lacks sufficient funds.
        :raises KeyError: if *quote_id* is unknown.
        """
        with self._lock:
            quote = self._pending_quotes.get(quote_id)
            if quote is None:
                raise KeyError(f"Unknown quote_id: {quote_id}")

            if datetime.datetime.utcnow() > quote["expires_at"]:
                del self._pending_quotes[quote_id]
                raise SwapExpiredError(f"Quote {quote_id} has expired.")

            user_id = quote["user_id"]
            src = quote["source_currency"]
            dst = quote["destination_currency"]
            source_amount = quote["source_amount"]
            destination_amount = quote["destination_amount"]
            rate = quote["exchange_rate"]
            fee_amount = quote["fee_amount"]

            # Retrieve or create wallets
            src_wallet = self._get_or_create_wallet(session, user_id, src)
            dst_wallet = self._get_or_create_wallet(session, user_id, dst)

            # Check balance
            current_balance = Decimal(str(src_wallet.balance))
            if current_balance < source_amount:
                raise InsufficientBalanceError(
                    f"User {user_id} has {current_balance} {src} but needs {source_amount} {src}."
                )

            # Debit source, credit destination
            src_wallet.balance = current_balance - source_amount
            src_wallet.updated_at = datetime.datetime.utcnow()
            dst_wallet.balance = Decimal(str(dst_wallet.balance)) + destination_amount
            dst_wallet.updated_at = datetime.datetime.utcnow()

            # Create SwapOrder record
            swap_order = db.SwapOrder(
                user_id=user_id,
                source_currency=src,
                destination_currency=dst,
                source_amount=source_amount,
                destination_amount=destination_amount,
                exchange_rate=rate,
                fee_amount=fee_amount,
                status="completed",
                created_at=datetime.datetime.utcnow(),
                completed_at=datetime.datetime.utcnow(),
            )
            session.add(swap_order)

            # Record price history snapshot
            price_hist = db.PriceHistory(
                pair=f"{src}/{dst}",
                price=rate,
                timestamp=datetime.datetime.utcnow(),
            )
            session.add(price_hist)

            session.commit()

            # Remove the consumed quote
            del self._pending_quotes[quote_id]

        log.info(f"Swap executed: {swap_order}")
        return swap_order

    def cancel_quote(self, quote_id: str) -> None:
        """Remove a pending quote without executing it."""
        with self._lock:
            self._pending_quotes.pop(quote_id, None)

    # ------------------------------------------------------------------
    # Wallet helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_or_create_wallet(
        session: sqlalchemy.orm.Session, user_id: int, currency: str
    ) -> db.CryptoWallet:
        """Return the wallet for *user_id*/*currency*, creating it if missing."""
        wallet = (
            session.query(db.CryptoWallet)
            .filter_by(user_id=user_id, currency=currency)
            .one_or_none()
        )
        if wallet is None:
            wallet = db.CryptoWallet(
                user_id=user_id,
                currency=currency,
                balance=Decimal("0"),
            )
            session.add(wallet)
            session.flush()  # assign wallet_id without committing
        return wallet

    def get_wallet_balances(
        self, session: sqlalchemy.orm.Session, user_id: int
    ) -> List[db.CryptoWallet]:
        """Return all wallets for *user_id*."""
        return (
            session.query(db.CryptoWallet)
            .filter_by(user_id=user_id)
            .all()
        )

    def get_swap_history(
        self, session: sqlalchemy.orm.Session, user_id: int, limit: int = 10
    ) -> List[db.SwapOrder]:
        """Return the most recent swap orders for *user_id*."""
        return (
            session.query(db.SwapOrder)
            .filter_by(user_id=user_id)
            .order_by(db.SwapOrder.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_all_pending_swaps(self, session: sqlalchemy.orm.Session) -> List[db.SwapOrder]:
        """Return all swap orders with status 'pending' (for admin review)."""
        return (
            session.query(db.SwapOrder)
            .filter_by(status="pending")
            .order_by(db.SwapOrder.created_at.asc())
            .all()
        )

    def admin_set_swap_status(
        self,
        session: sqlalchemy.orm.Session,
        swap_id: int,
        new_status: str,
    ) -> db.SwapOrder:
        """Manually set the status of a SwapOrder (admin action).

        :param new_status: One of ``"completed"``, ``"failed"``, ``"cancelled"``.
        """
        if new_status not in ("completed", "failed", "cancelled"):
            raise ValueError(f"Invalid status: {new_status}")
        swap = session.query(db.SwapOrder).filter_by(swap_id=swap_id).one()
        swap.status = new_status
        if new_status == "completed":
            swap.completed_at = datetime.datetime.utcnow()
        session.commit()
        return swap

    def get_enabled_currencies(self) -> List[str]:
        """Return the list of enabled currency symbols from the config."""
        try:
            return list(self._cfg["CryptoSwap"]["enabled_currencies"])
        except KeyError:
            return ["BTC", "ETH", "USDT", "LTC", "XMR", "DASH", "DAI", "USDC", "BTCLN"]

    def get_default_fee_percentage(self) -> float:
        """Return the default fee percentage from the config."""
        try:
            return float(self._cfg["CryptoSwap"]["default_fee_percentage"])
        except (KeyError, TypeError, ValueError):
            return 0.5
