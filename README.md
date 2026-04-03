<div align="center">

![](.media/icon-128x128_round.png)

# Greed — Crypto Swap Bot

A multi-bot Telegram crypto swap platform built on [greed](https://github.com/Steffo99/greed).
Supports cryptocurrency price checking, wallet management, and peer-to-peer swaps — all inside Telegram.

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE.txt)

</div>

---

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation](#installation)
   - [Option A: Install via pip (Linux/macOS)](#option-a-install-via-pip-linuxmacos)
   - [Option B: Install via Docker](#option-b-install-via-docker)
4. [Configuration](#configuration)
   - [Telegram Bot Token](#1-telegram-bot-token)
   - [Database](#2-database)
   - [Crypto Swap Settings](#3-crypto-swap-settings)
   - [Multi-Bot Mode](#4-multi-bot-mode-optional)
   - [Payment Settings](#5-payment-settings)
   - [Language](#6-language)
   - [Environment Variables](#7-environment-variables)
5. [Usage](#usage)
   - [Starting the Bot](#starting-the-bot)
   - [First Run (Become Manager)](#first-run-become-manager)
   - [User Commands](#user-commands)
   - [Admin Commands](#admin-commands)
6. [Keeping the Bot Running](#keeping-the-bot-running)
   - [Using screen](#using-screen)
   - [Using systemd](#using-systemd)
   - [Using Docker (detached)](#using-docker-detached)
7. [Updating](#updating)
8. [Project Structure](#project-structure)
9. [Troubleshooting](#troubleshooting)
10. [License](#license)

---

## Features

### For Users
- 🔄 **Crypto Swaps** — swap between supported cryptocurrencies with real-time quotes
- 👛 **Wallet Management** — view balances, deposit addresses, and request withdrawals
- 📊 **Live Prices** — check current exchange rates for all supported trading pairs
- 📜 **Swap History** — view all past swaps with status tracking
- 🛒 **Shop Orders** — browse products, place orders (original greed functionality)
- 💵 **Add Funds** — top up via cash or credit card (Telegram Payments)
- 🌍 **Multilanguage** — supports English, Italian, Ukrainian, Russian, Chinese, Hebrew, Spanish, Portuguese, Hindi

### For Admins / Managers
- 🔄 **Manage Swaps** — approve or reject pending swaps
- ⚙️ **Trading Pairs** — enable/disable pairs, set fees, min/max amounts
- 📝 **Products** — create, edit, delete shop products
- 📦 **Live Orders** — receive and process orders in real-time
- 💰 **Transactions** — create manual transactions, export to CSV
- 🏵 **Manager Permissions** — add managers with granular permissions

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.8 or higher |
| Git | Any recent version |
| Internet connection | Required (Telegram API + price feeds) |
| Telegram bot token | From [@BotFather](https://t.me/BotFather) |
| Payment provider token | _(optional)_ From [@BotFather](https://t.me/BotFather) |
| Docker | _(optional)_ For containerized deployment |

---

## Installation

### Option A: Install via pip (Linux/macOS)

```bash
# 1. Clone the repository
git clone https://github.com/bitbybit91/greed.git
cd greed

# 2. Switch to the crypto-swap-bot branch
git checkout crypto-swap-bot

# 3. Create a Python virtual environment
python3 -m venv venv

# 4. Activate the virtual environment
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. (Optional) Install colored console output
pip install coloredlogs

# 7. Generate the configuration file (first run creates config/config.toml)
python -OO core.py
# The bot will exit with: "A config file has been created. Customize it, then restart greed!"

# 8. Edit the configuration file
nano config/config.toml
# (See the Configuration section below for details)

# 9. Start the bot
python -OO core.py
```

### Option B: Install via Docker

```bash
# 1. Create the working directories
mkdir -p config strings data

# 2. Run the container (first run generates config/config.toml)
docker run \
  --volume "$(pwd)/config:/etc/greed" \
  --volume "$(pwd)/strings:/usr/src/greed/strings" \
  --volume "$(pwd)/data:/var/lib/greed" \
  ghcr.io/bitbybit91/greed:crypto-swap-bot
# The container will exit after creating the config file.

# 3. Edit the configuration file
nano config/config.toml
# (See the Configuration section below for details)

# 4. Start the bot
docker run \
  --volume "$(pwd)/config:/etc/greed" \
  --volume "$(pwd)/strings:/usr/src/greed/strings" \
  --volume "$(pwd)/data:/var/lib/greed" \
  ghcr.io/bitbybit91/greed:crypto-swap-bot
```

---

## Configuration

All configuration is in `config/config.toml`. Do **not** edit `config/template_config.toml` — it is the reference template.

### 1. Telegram Bot Token

Get a token from [@BotFather](https://t.me/BotFather) on Telegram, then set it:

```toml
[Telegram]
token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
conversation_timeout = 7200
long_polling_timeout = 30
timed_out_pause = 1
error_pause = 5
con_pool_size = 10
```

### 2. Database

By default, SQLite is used. For production, consider PostgreSQL:

```toml
[Database]
# SQLite (default):
engine = "sqlite:///database.sqlite"

# PostgreSQL (recommended for production):
# engine = "postgresql://user:password@localhost:5432/greed"
```

You can also override this with the `DB_ENGINE` environment variable.

### 3. Crypto Swap Settings

```toml
[CryptoSwap]
# Master switch for crypto swap features
enabled = true

# Cryptocurrencies to support
enabled_currencies = ["BTC", "ETH", "USDT", "SOL", "DOGE"]

# CoinGecko API (free tier — no key needed for basic use)
price_api_url = "https://api.coingecko.com/api/v3/simple/price"
price_api_key = ""

# Cache prices for 30 seconds to avoid rate limits
price_cache_ttl = 30

# Default swap fee (1%)
default_fee_percentage = 1.0

# Swap amount limits (in source currency units)
min_swap_amount = 1.0
max_swap_amount = 50000.0

# Quote validity period (60 seconds)
swap_confirmation_timeout = 60
```

### 4. Multi-Bot Mode (optional)

Run multiple Telegram bots from a single instance:

```toml
[Bots.main]
token = "111111111:FIRST_BOT_TOKEN"
enabled = true
name = "Main Swap Bot"

[Bots.secondary]
token = "222222222:SECOND_BOT_TOKEN"
enabled = true
name = "Secondary Bot"
```

> If no `[Bots]` section is present, the bot runs in single-bot mode using `[Telegram].token`.

### 5. Payment Settings

```toml
[Payments]
currency = "USD"
currency_exp = 2
currency_symbol = "$"

[Payments.Cash]
enable_pay_with_cash = true
enable_create_transaction = true

[Payments.CreditCard]
credit_card_token = "YOUR_PAYMENT_PROVIDER_TOKEN"
min_amount = 100
max_amount = 10000
payment_presets = [1.00, 5.00, 10.00, 25.00]
tip_presets = []
max_tip_amount = 0
fee_percentage = 2.9
fee_fixed = 30
name_required = false
email_required = false
phone_required = false
```

### 6. Language

```toml
[Language]
enabled_languages = ["en", "it", "uk", "ru", "zh_cn", "he", "es_mx", "pt_br", "hi"]
default_language = "en"
fallback_language = "en"
```

### 7. Environment Variables

| Variable | Description | Default |
|---|---|---|
| `CONFIG_PATH` | Path to the TOML config file | `config/config.toml` |
| `DB_ENGINE` | SQLAlchemy database URI (overrides config) | _(from config)_ |

---

## Usage

### Starting the Bot

```bash
# With pip installation:
source venv/bin/activate
python -OO core.py

# With Docker:
docker run \
  --volume "$(pwd)/config:/etc/greed" \
  --volume "$(pwd)/strings:/usr/src/greed/strings" \
  --volume "$(pwd)/data:/var/lib/greed" \
  ghcr.io/bitbybit91/greed:crypto-swap-bot
```

### First Run (Become Manager)

1. Start the bot (see above).
2. Open Telegram and send `/start` to your bot.
3. The **first user** to send `/start` is automatically promoted to 💼 **Manager**.
4. Stop the bot with **Ctrl+C**.

### User Commands

| Command | Description |
|---|---|
| `/start` | Start or restart the conversation |
| `/swap` | Initiate a crypto swap |
| `/price` | View live cryptocurrency prices |
| `/wallet` | View your crypto wallet balances |
| `/history` | View your swap history |

**From the menu keyboard:**

| Button | Action |
|---|---|
| 🔄 Swap Crypto | Start a new crypto swap |
| 👛 My Wallet | View balances and deposit addresses |
| 📊 Live Prices | Check current exchange rates |
| 📜 Swap History | Review past swaps |
| 🛒 Order Products | Browse and order shop products |
| 💵 Add Funds | Top up your fiat wallet |
| ℹ️ Bot Info | About the bot |
| ❓ Help / Support | Get help |
| 🇬🇧 Language | Change display language |

### Admin Commands

Admins access the manager panel by sending `/start`:

| Button | Action |
|---|---|
| 🔄 Manage Swaps | Approve / reject pending swaps |
| ⚙️ Trading Pairs | Configure supported pairs, fees, and limits |
| 📝 Products | Add / edit / delete products |
| 📦 Orders | View and process customer orders |
| 💳 Transaction List | View all transactions |
| 💰 Create Transaction | Manually credit/debit a user |
| 📄 .csv | Export transactions as CSV |
| 🏵 Edit Managers | Add managers and set permissions |
| 👤 Switch to Customer Mode | Test the bot as a regular user |

---

## Keeping the Bot Running

### Using `screen`

```bash
# Start in a screen session
screen -S greed
source venv/bin/activate
python -OO core.py

# Detach: press Ctrl+A, then Ctrl+D
# Reattach later:
screen -r greed
```

### Using `systemd`

1. Create a system user:
   ```bash
   sudo useradd greed --system --no-create-home
   ```

2. Set ownership (assuming install at `/srv/greed`):
   ```bash
   sudo chown -R greed: /srv/greed
   ```

3. Create `/etc/systemd/system/greed-swap.service`:
   ```ini
   [Unit]
   Name=greed-swap
   Description=Greed Crypto Swap Bot
   Wants=network-online.target
   After=network-online.target nss-lookup.target

   [Service]
   Type=exec
   User=greed
   WorkingDirectory=/srv/greed
   ExecStart=/srv/greed/venv/bin/python -OO /srv/greed/core.py
   Environment=PYTHONUNBUFFERED=1
   Restart=on-failure
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start greed-swap
   sudo systemctl enable greed-swap

   # Check status:
   sudo systemctl status greed-swap

   # View logs:
   sudo journalctl -u greed-swap -f
   ```

### Using Docker (detached)

```bash
docker run \
  --detach \
  --restart always \
  --name greed-swap \
  --volume "$(pwd)/config:/etc/greed" \
  --volume "$(pwd)/strings:/usr/src/greed/strings" \
  --volume "$(pwd)/data:/var/lib/greed" \
  ghcr.io/bitbybit91/greed:crypto-swap-bot

# View logs:
docker logs -f greed-swap

# Stop:
docker stop greed-swap

# Restart:
docker start greed-swap
```

---

## Updating

### pip installation

```bash
cd /path/to/greed
git stash
git pull origin crypto-swap-bot
git stash pop
source venv/bin/activate
pip install -r requirements.txt
python -OO core.py
```

### Docker installation

```bash
# Stop and remove the old container
docker stop greed-swap
docker rm greed-swap

# Pull the latest image
docker pull ghcr.io/bitbybit91/greed:crypto-swap-bot

# Start a new container
docker run \
  --detach \
  --restart always \
  --name greed-swap \
  --volume "$(pwd)/config:/etc/greed" \
  --volume "$(pwd)/strings:/usr/src/greed/strings" \
  --volume "$(pwd)/data:/var/lib/greed" \
  ghcr.io/bitbybit91/greed:crypto-swap-bot
```

---

## Project Structure

```
greed/
├── core.py                 # Main entry point, update dispatcher, multi-bot launcher
├── worker.py               # Per-user conversation thread (shop + crypto swap flows)
├── database.py             # SQLAlchemy ORM models (User, Product, CryptoWallet, SwapOrder, etc.)
├── duckbot.py              # Telegram Bot API wrapper with retry logic & rate limiting
├── crypto_swap.py          # Core swap engine: pricing, quoting, execution
├── bot_manager.py          # Multi-bot orchestrator
├── nuconfig.py             # TOML configuration loader & validator
├── localization.py         # i18n string loader with fallback
├── utils.py                # Utility functions (HTML escape, crypto formatting, address validation)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container build configuration
├── config/
│   ├── template_config.toml  # Template configuration (DO NOT edit directly)
│   └── config.toml           # Your configuration (auto-generated on first run, gitignored)
├── strings/
│   ├── en.py               # English strings (primary)
│   ├── it.py               # Italian
│   ├── uk.py               # Ukrainian
│   ├── ru.py               # Russian
│   ├── zh_cn.py            # Simplified Chinese
│   ├── he.py               # Hebrew
│   ├── es_mx.py            # Spanish (Mexican)
│   ├── pt_br.py            # Portuguese (Brazilian)
│   └── hi.py               # Hindi
├── docs/
│   └── README.md           # Original documentation
├── .gitignore
├── LICENSE.txt             # AGPL-3.0
└── CONTRIBUTING.md
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `config/template_config.toml does not exist!` | Run the bot from the project root directory (`cd greed`) |
| `A config file has been created. Customize it, then restart greed!` | Edit `config/config.toml` with your bot token, then restart |
| `The token you have entered in the config file is invalid` | Check your bot token from [@BotFather](https://t.me/BotFather) |
| `There were errors while parsing the config file` | Your `config.toml` is missing keys from `template_config.toml`. Compare and add missing sections |
| `Unable to fetch current prices` | Check your internet connection and `price_api_url` setting. The bot will fall back to cached prices |
| `Insufficient balance` | The user doesn't have enough crypto in their wallet to perform the swap |
| Bot doesn't respond to messages | Send `/start` to restart the conversation. Check bot logs for errors |
| Database locked (SQLite) | Consider switching to PostgreSQL for production multi-bot setups |

---

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE.txt).

Based on [greed](https://github.com/Steffo99/greed) by [@Steffo99](https://github.com/Steffo99).