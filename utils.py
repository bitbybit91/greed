import re
from decimal import Decimal
from typing import Optional


def telegram_html_escape(string: str):
    return string.replace("<", "&lt;") \
        .replace(">", "&gt;") \
        .replace("&", "&amp;") \
        .replace('"', "&quot;")


# ---------------------------------------------------------------------------
# Crypto utility functions
# ---------------------------------------------------------------------------

# Number of decimal places displayed per currency
_CRYPTO_DECIMALS: dict = {
    "BTC": 8,
    "BTCLN": 8,
    "ETH": 6,
    "LTC": 8,
    "XMR": 12,
    "DASH": 8,
    "DAI": 6,
    "USDT": 6,
    "USDC": 6,
}

_DEFAULT_CRYPTO_DECIMALS = 8

# Basic regex patterns for address validation
_ADDRESS_PATTERNS: dict = {
    "BTC": re.compile(r"^(1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,62}$"),
    "BTCLN": re.compile(r"^(lnbc|lntb|lnbcrt)[0-9]+[munp]?[a-z0-9]+$", re.IGNORECASE),
    "LTC": re.compile(r"^[LMN3][a-km-zA-HJ-NP-Z1-9]{26,33}$"),
    "ETH": re.compile(r"^0x[0-9a-fA-F]{40}$"),
    "DAI": re.compile(r"^0x[0-9a-fA-F]{40}$"),
    "USDT": re.compile(r"^0x[0-9a-fA-F]{40}$"),
    "USDC": re.compile(r"^0x[0-9a-fA-F]{40}$"),
    "XMR": re.compile(r"^[48][0-9AB][1-9A-HJ-NP-Za-km-z]{93}$"),
    "DASH": re.compile(r"^X[1-9A-HJ-NP-Za-km-z]{33}$"),
}


def format_crypto_amount(amount, currency: str) -> str:
    """Format *amount* with the appropriate number of decimal places for *currency*.

    :param amount: Numeric amount (int, float, Decimal, or str).
    :param currency: Currency symbol, e.g. ``"BTC"``.
    :return: Formatted string, e.g. ``"0.00100000 BTC"``.
    """
    decimals = _CRYPTO_DECIMALS.get(currency.upper(), _DEFAULT_CRYPTO_DECIMALS)
    value = Decimal(str(amount))
    formatted = f"{value:.{decimals}f}"
    return f"{formatted} {currency.upper()}"


def validate_crypto_address(address: str, currency: str) -> bool:
    """Perform a basic format check on a cryptocurrency address.

    Returns ``True`` if the address looks valid for the given *currency*,
    ``False`` otherwise.  For currencies that have no configured validation
    pattern, returns ``False`` to err on the side of caution (operators should
    add patterns for any new currencies they enable).
    """
    pattern = _ADDRESS_PATTERNS.get(currency.upper())
    if pattern is None:
        return False
    return bool(pattern.match(address.strip()))


def calculate_swap_fee(amount, fee_percentage: float):
    """Compute the fee for a swap.

    :param amount: Source amount (numeric).
    :param fee_percentage: Fee as a percentage, e.g. ``0.5`` for 0.5 %.
    :return: Fee as a :class:`Decimal`.
    """
    return Decimal(str(amount)) * Decimal(str(fee_percentage)) / Decimal("100")


def format_exchange_rate(rate, base: str, quote: str) -> str:
    """Return a human-readable exchange rate string.

    :param rate: Numeric rate (how many *quote* units per 1 *base* unit).
    :param base: Base currency symbol.
    :param quote: Quote currency symbol.
    :return: Formatted string, e.g. ``"1 BTC = 42000.00 USDT"``.
    """
    decimals = _CRYPTO_DECIMALS.get(quote.upper(), 2)
    value = Decimal(str(rate))
    formatted = f"{value:.{decimals}f}"
    return f"1 {base.upper()} = {formatted} {quote.upper()}"
