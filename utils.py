import re
from decimal import Decimal, InvalidOperation


def telegram_html_escape(string: str):
    return string.replace("<", "&lt;") \
        .replace(">", "&gt;") \
        .replace("&", "&amp;") \
        .replace('"', "&quot;")


# Decimal places per currency for display purposes
CRYPTO_DECIMALS = {
    "BTC": 8,
    "ETH": 6,
    "USDT": 2,
    "SOL": 4,
    "DOGE": 2,
    "LTC": 6,
    "XRP": 4,
    "BNB": 4,
    "ADA": 4,
    "DOT": 4,
}


def format_crypto(amount: Decimal, decimals: int = 8) -> str:
    """Format a Decimal crypto amount, stripping trailing zeros."""
    formatted = f"{amount:.{decimals}f}"
    # Strip trailing zeros after decimal point, but keep at least 2 decimal places
    if "." in formatted:
        formatted = formatted.rstrip("0")
        if formatted.endswith("."):
            formatted += "00"
        elif len(formatted.split(".")[1]) < 2:
            formatted += "0"
    return formatted


def format_crypto_amount(amount: Decimal, currency: str) -> str:
    """Format a crypto amount with currency-appropriate decimal places."""
    decimals = CRYPTO_DECIMALS.get(currency.upper(), 8)
    return f"{format_crypto(amount, decimals)} {currency.upper()}"


def format_usd(amount: Decimal) -> str:
    """Format a Decimal value as a USD string with commas."""
    return f"${amount:,.2f}"


def parse_decimal(text: str) -> Decimal:
    """Parse user-supplied text to a Decimal. Raises ValueError on invalid input."""
    try:
        # Replace commas used as decimal separators
        cleaned = text.strip().replace(",", ".")
        value = Decimal(cleaned)
        if not value.is_finite():
            raise ValueError(f"Non-finite value: {text}")
        return value
    except InvalidOperation:
        raise ValueError(f"Cannot parse '{text}' as a number")


# Regex patterns for basic crypto address validation
ADDR_PATTERNS = {
    "BTC": re.compile(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$"),
    "ETH": re.compile(r"^0x[0-9a-fA-F]{40}$"),
    "USDT": re.compile(r"^(0x[0-9a-fA-F]{40}|T[A-Za-z1-9]{33})$"),
    "SOL": re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$"),
    "DOGE": re.compile(r"^D[5-9A-HJ-NP-U][1-9A-HJ-NP-Za-km-z]{32}$"),
    "LTC": re.compile(r"^(ltc1|[LM3])[a-zA-HJ-NP-Z0-9]{26,62}$"),
    "XRP": re.compile(r"^r[0-9a-zA-Z]{24,34}$"),
    "BNB": re.compile(r"^(0x[0-9a-fA-F]{40}|bnb[0-9a-z]{39})$"),
    "ADA": re.compile(r"^(addr1[a-z0-9]+|[Aa][a-zA-Z0-9]{58})$"),
    "DOT": re.compile(r"^1[a-zA-Z0-9]{46,47}$"),
}


def validate_crypto_address(address: str, currency: str) -> bool:
    """Validate a crypto address using regex patterns. Returns True if valid."""
    pattern = ADDR_PATTERNS.get(currency.upper())
    if pattern is None:
        # Unknown currency — accept any non-empty string
        return bool(address and address.strip())
    return bool(pattern.match(address.strip()))

