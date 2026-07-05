<div align="center">

![](.media/icon-128x128_round.png)

# Greed

Customizable, multilanguage Telegram shop bot with cryptocurrency payment integration and optional credit-card / wallet support.

</div>

---

## Overview

**Greed** is an open-source Telegram bot framework for running a fully-functional digital shop.  
It supports product listings, a shopping cart, multiple payment methods (crypto, Telegram Payments, cash), live order management for admins, and up to 7 simultaneous bot instances.

---

## Features

### Customer Mode
- Browse products and add them to a shopping cart
- **Crypto-first checkout**: BTC, LTC, XMR, USDT-TRC20, ZCASH (primary)
- Wallet balance checkout (secondary)
- Submit TX hash after sending crypto; admins verify and mark as delivered
- View past order status
- Enter and save shipping details (name, address, city, state, ZIP, country)
- Built-in "Buy Crypto" resource links: LocalCoinSwap, Binance, CoinATMRadar
- Multi-language support (9 languages: EN, IT, RU, UK, ZH-CN, HE, ES-MX, PT-BR, HI)

### Owner / Admin Mode
- Add, edit, and delete products (with optional images)
- Live Orders feed: mark orders complete or issue refunds
- Manually credit / debit customer wallets
- View paginated transaction list and export to CSV
- Manage admin accounts and permissions
- Run up to 7 independent bot instances via `[Bots.*]` config

### Crypto Payment Features
- Automatic price lookup via CoinGecko API
- Configurable deposit addresses per coin
- Countdown timer on payment invoice
- TX hash collection and admin notification
- Order blocked for users with a pending unverified crypto payment

---

## Requirements

- **Ubuntu 20.04** VPS (or compatible Debian/Ubuntu system)
- **Python 3.8+**
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- Internet access (for CoinGecko price API and Telegram API)

---

## Quick Install (Automated)

```bash
# Run as root on Ubuntu 20.04
curl -fsSL https://raw.githubusercontent.com/bitbybit91/greed/copilot/add-setup-bots-script/setup.sh | bash
```

Or clone the repo first:

```bash
git clone -b copilot/add-setup-bots-script https://github.com/bitbybit91/greed.git /opt/greed
bash /opt/greed/setup.sh
```

The script will:
1. Install system packages (`python3`, `pip`, `venv`, `git`, `screen`, `sqlite3`)
2. Clone / update the repo to `/opt/greed`
3. Create a Python virtual environment and install all dependencies
4. Copy `config/template_config.toml` → `config/config.toml` (first run only)
5. Prompt for your bot token and write it into the config
6. Install and start a `systemd` service named `greed`

---

## Manual Install

### 1. Install system packages

```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y python3 python3-pip python3-venv git screen sqlite3
```

### 2. Clone the repository

```bash
git clone -b copilot/add-setup-bots-script https://github.com/bitbybit91/greed.git /opt/greed
cd /opt/greed
```

### 3. Create virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt coloredlogs
```

### 4. Create and edit the config file

```bash
cp config/template_config.toml config/config.toml
nano config/config.toml
```

See the **Configuration Reference** section below for all settings.

### 5. First run

```bash
source venv/bin/activate
python core.py
```

### 6. Become the first admin

Send `/start` to your bot in Telegram.  
The **first user** to send `/start` is automatically made the owner/admin.

---

## Configuration Reference

All settings live in `config/config.toml` (created from `config/template_config.toml`).

### `[Language]`

| Key | Description | Example |
|-----|-------------|---------|
| `enabled_languages` | List of language codes to enable | `["en", "it"]` |
| `default_language` | Fallback language for new users | `"en"` |
| `fallback_language` | Language used when a string is missing | `"en"` |

### `[Database]`

| Key | Description | Example |
|-----|-------------|---------|
| `engine` | SQLAlchemy database URI | `"sqlite:///database.sqlite"` |

For PostgreSQL: `"******localhost/greed"`

### `[Telegram]`

| Key | Description | Example |
|-----|-------------|---------|
| `token` | Your bot token from @BotFather | `"123456789:ABC..."` |
| `conversation_timeout` | Seconds before idle session expires | `7200` |
| `long_polling_timeout` | Seconds to wait for Telegram updates | `30` |
| `con_pool_size` | Number of HTTP connections to Telegram | `10` |

### `[Payments]`

| Key | Description | Example |
|-----|-------------|---------|
| `currency` | ISO 4217 currency code | `"USD"` |
| `currency_exp` | Decimal places (2 for USD/EUR) | `2` |
| `currency_symbol` | Display symbol | `"$"` |

### `[Payments.Cash]`

| Key | Description |
|-----|-------------|
| `enable_pay_with_cash` | Show "Pay with cash" option to customers |
| `enable_create_transaction` | Show "Create transaction" button in admin menu |

### `[Payments.CreditCard]`

| Key | Description |
|-----|-------------|
| `credit_card_token` | Telegram Payments provider token (leave empty to disable) |
| `min_amount` | Minimum charge in minimum currency units (e.g. `1000` = $10.00) |
| `max_amount` | Maximum charge in minimum currency units |
| `payment_presets` | Quick-select preset amounts shown to users |
| `fee_percentage` | Percentage fee added on top (e.g. `2.9`) |
| `fee_fixed` | Fixed fee in minimum units (e.g. `30` = $0.30) |

### `[Appearance]`

| Key | Description |
|-----|-------------|
| `full_order_info` | Show full order info (with timestamp) to customers |
| `refill_on_checkout` | Allow wallet refill mid-checkout if credit is insufficient |
| `display_welcome_message` | Show welcome message on `/start` |
| `require_payment_for_orders` | Block new orders if user has a pending unverified crypto payment |

### `[CryptoSwap]`

| Key | Description | Example |
|-----|-------------|---------|
| `enabled` | Enable crypto payment mode | `true` |
| `price_api` | CoinGecko API base URL | `"https://api.coingecko.com/api/v3"` |
| `cache_ttl` | Price cache lifetime in seconds | `60` |
| `fee_percentage` | Swap fee charged on top | `1.0` |
| `quote_timeout` | Seconds the payment invoice is valid | `60` |
| `min_usd` | Minimum order value in USD | `10.0` |
| `max_usd` | Maximum order value in USD | `10000.0` |

### `[CryptoSwap.Coins]`

Maps ticker symbols to CoinGecko IDs:

```toml
[CryptoSwap.Coins]
BTC = "bitcoin"
LTC = "litecoin"
XMR = "monero"
"USDT-TRC20" = "tether"
ZCASH = "zcash"
```

### `[CryptoSwap.DepositAddresses]`

**These must be YOUR wallet addresses.** Customers will be instructed to send crypto to these addresses.

```toml
[CryptoSwap.DepositAddresses]
BTC = "bc1q..."          # Your Bitcoin deposit address
LTC = "ltc1q..."         # Your Litecoin deposit address
XMR = "4..."             # Your Monero deposit address
"USDT-TRC20" = "T..."    # Your USDT-TRC20 (Tron) deposit address
ZCASH = "zs1..."         # Your Zcash deposit address
```

### `[Bots.*]` — Multi-bot configuration

Up to 7 additional bots can be configured:

```toml
[Bots.bot1]
token = "BOT_1_TOKEN_HERE"
enabled = true
name = "ShopBot-1"
database = "sqlite:///bot1.sqlite"
directory = "ShopBot-1-TG-Bot"
```

Set `enabled = false` to disable a bot without removing it.

---

## Crypto Payment Setup

### Getting deposit addresses

| Coin | How to get an address |
|------|----------------------|
| **BTC** | Create a Bitcoin wallet (e.g. Electrum, Ledger). Copy a receiving address. |
| **LTC** | Create a Litecoin wallet (e.g. Litecoin Core, Exodus). Copy a receiving address. |
| **XMR** | Create a Monero wallet (Feather Wallet or Monero GUI). Copy the primary address. |
| **USDT-TRC20** | Create a Tron wallet (TronLink). Copy the TRC-20 compatible address. |
| **ZCASH** | Create a Zcash wallet (ZecWallet Lite). Copy a transparent (t-addr) address. |

### How the payment flow works

1. Customer adds items to cart and presses **Done**
2. Bot shows crypto payment options (BTC, LTC, XMR, USDT-TRC20, ZCASH) first, then wallet balance
3. Customer selects a coin
4. Bot shows a "Buy Crypto" resource panel (LocalCoinSwap, Binance, CoinATMRadar)
5. Bot displays the exact amount to send and your deposit address, with a countdown timer
6. Customer sends the crypto and presses **✅ I've Paid**
7. Customer enters the transaction hash (TX ID)
8. All admins with `receive_orders=True` are notified
9. Admin verifies the TX on a block explorer, then marks the order as **Complete** in the Live Orders menu
10. Customer is notified of order completion

### Verifying TX hashes as admin

1. Open the Live Orders menu (📦 Orders)
2. Find the pending crypto order
3. Copy the TX hash from the order notification
4. Verify on the appropriate block explorer:
   - BTC: [mempool.space](https://mempool.space)
   - LTC: [blockchair.com/litecoin](https://blockchair.com/litecoin)
   - XMR: [xmrchain.net](https://xmrchain.net)
   - USDT-TRC20: [tronscan.org](https://tronscan.org)
   - ZCASH: [zcashblockexplorer.com](https://zcashblockexplorer.com)
5. Confirm the amount matches the order total, then press **✅ Complete**

---

## Owner Mode Guide

Access the admin menu by sending `/start` if you are a registered admin.

| Button | Permission Required | Description |
|--------|--------------------|----|
| 📝 Products | `edit_products` | Add, edit, delete products |
| 📦 Orders | `receive_orders` | View and process pending orders in Live mode |
| 💰 Create transaction | `create_transactions` + Cash enabled | Manually credit/debit a customer's wallet |
| 💳 Transaction list | `create_transactions` | Browse all transactions, paginated |
| 📄 .csv | `create_transactions` | Export all transactions as CSV |
| 🏵 Edit Managers | `is_owner` | Add or manage admin accounts |
| 👤 Switch to customer mode | any | Enter customer mode |

### Live Orders mode

- All pending orders (including crypto orders) are shown with **✅ Complete** and **✴️ Refund** buttons
- Pressing **Complete** marks the order as delivered and notifies the customer
- Pressing **Refund** asks for a reason, marks the order refunded, and reverses any wallet transaction

---

## Customer Mode Guide

1. Send `/start` to begin
2. Select **🛒 Order products** to browse the shop
3. Press **➕ Add** under any product to add it to your cart
4. When done, press **✅ Done** and optionally leave a note
5. Select a payment method:
   - Choose a crypto coin (BTC, LTC, XMR, USDT-TRC20, ZCASH) for primary payment
   - Or choose **💵 Pay with Wallet Balance** if you have credit
6. For crypto: send the exact amount to the shown address, press **✅ I've Paid**, enter your TX hash
7. For wallet: payment is deducted immediately
8. Check your order status with **🛍 My orders**

### Shipping Details

Select **📦 Shipping Details** from the main menu to enter your delivery address.  
Your saved address is automatically attached to every order you place.

---

## Running as a Service (systemd)

```bash
# Start
systemctl start greed

# Stop
systemctl stop greed

# Restart (after config changes)
systemctl restart greed

# View live logs
journalctl -u greed -f

# Check status
systemctl status greed
```

---

## Updating

```bash
cd /opt/greed
git pull
source venv/bin/activate
pip install -r requirements.txt
systemctl restart greed
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Bot doesn't respond | Check `journalctl -u greed -f` for errors; verify token in `config/config.toml` |
| `Invalid token` error | Re-check your token from @BotFather; ensure no extra spaces |
| `Config file errors` | Run `python core.py` manually; it will print the offending key |
| Crypto prices unavailable | CoinGecko rate limit may be hit; increase `cache_ttl` in config |
| Orders menu crashes | Ensure `delivery_date` / `refund_date` are not mixed up in the DB |
| Database errors on startup | Delete `database.sqlite` to start fresh (loses all data) |
| Service won't start | Check permissions: `ls -la /opt/greed`; ensure `root` owns all files |
| Can't become admin | You must be the **first** user to send `/start` after a fresh database |

---

## License

[AGPL-3.0](LICENSE.txt) — © Steffo99 and contributors
