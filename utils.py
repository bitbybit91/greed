import re


def telegram_html_escape(string: str):
    return string.replace("<", "&lt;") \
        .replace(">", "&gt;") \
        .replace("&", "&amp;") \
        .replace('"', "&quot;")


# Decimal precision for each supported cryptocurrency
CRYPTO_DECIMALS = {
    "BTC": 8,
    "LTC": 6,
    "XMR": 12,
    "USDT-TRC20": 2,
    "ZCASH": 8,
}

# Address validation regex patterns for each supported cryptocurrency
ADDR_PATTERNS = {
    "BTC": re.compile(r"^(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}$"),
    "LTC": re.compile(r"^(ltc1|[LM3])[a-zA-HJ-NP-Z0-9]{26,62}$"),
    "XMR": re.compile(r"^[48][0-9AB][1-9A-HJ-NP-Za-km-z]{93}$"),
    "USDT-TRC20": re.compile(r"^T[A-Za-z1-9]{33}$"),
    "ZCASH": re.compile(r"^(t1[a-zA-Z0-9]{33}|t3[a-zA-Z0-9]{33})$"),
}
