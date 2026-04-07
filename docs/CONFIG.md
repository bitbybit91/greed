# Configuration Reference

Every field in `config/config.toml` is documented below with its type, default value, valid range, and example.

The configuration file is generated from `config/template_config.toml` on first run. Edit `config/config.toml` — never edit the template directly.

---

## [Language] Section

Controls the bot's multilingual support.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled_languages` | Array of strings | `["it", "en", "uk", "ru", "zh_cn", "he", "es_mx", "pt_br", "hi"]` | Languages available for users to select |
| `default_language` | String | `"it"` | Default language for users whose language can't be detected |
| `fallback_language` | String | `"en"` | Language to use when a string is missing in the user's language |

**Example:**
```toml
[Language]
enabled_languages = ["en", "es_mx"]
default_language = "en"
fallback_language = "en"
```

---

## [Database] Section

Database connection configuration.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `engine` | String | `"sqlite:///database.sqlite"` | SQLAlchemy connection URI |

Supports SQLite and PostgreSQL. Ignored if the `DB_ENGINE` environment variable is set.

**Example:**
```toml
[Database]
engine = "sqlite:///database.sqlite"
# Or for PostgreSQL:
# engine = "postgresql://user:pass@localhost/greed"
```

---

## [Telegram] Section

Telegram bot API connection settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `token` | String | — | Bot token from @BotFather (**required**) |
| `conversation_timeout` | Integer | `7200` | Seconds before an idle conversation expires |
| `long_polling_timeout` | Integer | `30` | Seconds to wait for new updates via long polling |
| `timed_out_pause` | Integer | `1` | Seconds to wait before retrying after a timeout |
| `error_pause` | Integer | `5` | Seconds to wait before retrying after an error |
| `con_pool_size` | Integer | `10` | Number of HTTP connections to keep in the pool |

**Example:**
```toml
[Telegram]
token = "123456789:ABCDefGHIjklMNOpqrsTUVwxyz"
conversation_timeout = 7200
```

---

## [Payments] Section

General payment configuration.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `currency` | String | `"EUR"` | ISO 4217 currency code |
| `currency_exp` | Integer | `2` | Number of decimal places (2 for EUR, USD, GBP) |
| `currency_symbol` | String | `"€"` | Currency symbol displayed to users |

### [Payments.Cash]

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enable_pay_with_cash` | Boolean | `true` | Show "Pay with cash" option |
| `enable_create_transaction` | Boolean | `true` | Allow managers to create manual transactions |

### [Payments.CreditCard]

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `credit_card_token` | String | `""` | Telegram Payments provider token (empty = disabled) |
| `min_amount` | Integer | `1000` | Minimum payment in smallest currency units |
| `max_amount` | Integer | `10000` | Maximum payment in smallest currency units |
| `payment_presets` | Array of floats | `[10.00, 25.00, 50.00, 100.00]` | Quick-select payment amounts |
| `tip_presets` | Array of integers | `[]` | Suggested tip amounts (empty = disabled) |
| `max_tip_amount` | Integer | `0` | Maximum tip in smallest currency units |
| `fee_percentage` | Float | `2.9` | Percentage fee on credit card payments |
| `fee_fixed` | Integer | `30` | Fixed fee in smallest currency units |
| `name_required` | Boolean | `true` | Require customer name for card payments |
| `email_required` | Boolean | `true` | Require customer email for card payments |
| `phone_required` | Boolean | `true` | Require customer phone for card payments |

---

## [CryptoSwap] Section

Cryptocurrency swap and payment settings.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | Boolean | `true` | Enable/disable crypto payment features |
| `price_api` | String | `"https://api.coingecko.com/api/v3"` | CoinGecko API base URL |
| `cache_ttl` | Integer | `60` | Price cache duration in seconds |
| `fee_percentage` | Float | `1.0` | Fee percentage on crypto swaps |
| `quote_timeout` | Integer | `60` | Seconds before a price quote expires |
| `min_usd` | Float | `10.0` | Minimum swap amount in USD |
| `max_usd` | Float | `10000.0` | Maximum swap amount in USD |

### [CryptoSwap.Coins]

Maps coin symbols to CoinGecko API IDs. Only these 5 coins are supported:

| Symbol | CoinGecko ID | Network | Description |
|--------|-------------|---------|-------------|
| `BTC` | `bitcoin` | Bitcoin mainnet | Bitcoin |
| `LTC` | `litecoin` | Litecoin mainnet | Litecoin |
| `XMR` | `monero` | Monero mainnet | Monero |
| `USDT-TRC20` | `tether` | TRON TRC-20 | Tether (USDT) on TRON |
| `ZCASH` | `zcash` | Zcash mainnet | Zcash |

**Example:**
```toml
[CryptoSwap.Coins]
BTC = "bitcoin"
LTC = "litecoin"
XMR = "monero"
"USDT-TRC20" = "tether"
ZCASH = "zcash"
```

### [CryptoSwap.FeeAddresses]

Operator fee collection addresses — one per supported coin.

```toml
[CryptoSwap.FeeAddresses]
BTC = "bc1qyourbtcfeeaddress"
LTC = "ltc1qyourltcfeeaddress"
XMR = "4YourMoneroFeeAddress..."
"USDT-TRC20" = "TYourTronFeeAddress"
ZCASH = "t1YourZcashFeeAddress"
```

### [CryptoSwap.DepositAddresses]

Deposit addresses shown to customers during checkout. These **must** be addresses you control.

```toml
[CryptoSwap.DepositAddresses]
BTC = "bc1qyourbtcdepositaddress"
LTC = "ltc1qyourltcdepositaddress"
XMR = "4YourMoneroDepositAddress..."
"USDT-TRC20" = "TYourTronDepositAddress"
ZCASH = "t1YourZcashDepositAddress"
```

> **Important:** The `USDT-TRC20` key must be quoted in TOML because it contains a hyphen.

---

## [Bots.*] Section — Multi-Bot Configuration

Greed supports up to 7 simultaneous bot instances. Each bot is configured in its own sub-section.

### Memory Management (top-level [Bots])

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `max_workers_per_bot` | Integer | `50` | Maximum concurrent worker threads per bot |
| `worker_idle_timeout` | Integer | `1800` | Seconds before an idle worker is cleaned up |

### Per-Bot Configuration ([Bots.botN])

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `token` | String | — | Bot token from @BotFather |
| `enabled` | Boolean | `false` | Whether this bot should be started |
| `name` | String | — | Human-readable name for logging |
| `directory` | String | — | Working directory (created automatically) |

**Example:**
```toml
[Bots]
max_workers_per_bot = 50
worker_idle_timeout = 1800

[Bots.bot1]
token = "123456789:ABCDefGHIjklMNOpqrsTUVwxyz"
enabled = true
name = "ShopBot-1"
directory = "ShopBot-1-TG-Bot"

[Bots.bot2]
token = "987654321:ZYXwvuTSRqpoNMLkjiHGFedCBA"
enabled = false
name = "ShopBot-2"
directory = "ShopBot-2-TG-Bot"
```

---

## [Appearance] Section

Controls the visual appearance and behavior of the bot UI.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `full_order_info` | Boolean | `false` | Show full order details to customers (includes order number and timestamp) |
| `refill_on_checkout` | Boolean | `true` | Allow balance refill during checkout if balance is insufficient |
| `display_welcome_message` | Boolean | `true` | Show welcome message when user sends /start |

---

## [Logging] Section

Controls console logging output.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `format` | String | `"{asctime} \| {threadName} \| {name} \| {message}"` | Python logging format string |
| `level` | String | `"INFO"` | Minimum log level: FATAL, ERROR, WARNING, INFO, DEBUG |

---

## Environment Variables

| Variable | Description | Overrides |
|----------|-------------|-----------|
| `CONFIG_PATH` | Path to config file | Default: `config/config.toml` |
| `DB_ENGINE` | SQLAlchemy database URI | `[Database] engine` |
