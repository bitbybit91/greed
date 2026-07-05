<div align="center">

![](.media/icon-128x128_round.png)

# Greed

A customizable, multilanguage Telegram shop bot with support for Telegram Payments and crypto deposits.

</div>

---

## Table of Contents

1. [Features](#features)
2. [Screenshots](#screenshots)
3. [Ubuntu 20.04 VPS — Full Installation Guide](#ubuntu-2004-vps--full-installation-guide)
4. [Configuration Reference](#configuration-reference)
5. [Running as a Systemd Service](#running-as-a-systemd-service)
6. [Owner (Admin) Mode Guide](#owner-admin-mode-guide)
7. [Customer Mode Guide](#customer-mode-guide)
8. [Troubleshooting](#troubleshooting)
9. [Contributing](#contributing)

---

## Features

- 🛒 Product catalog with images and descriptions
- 💳 Telegram native card payments (via payment providers)
- 💵 Cash payment option with user ID for in-person pickup
- ₿ Crypto deposit addresses (BTC, ETH, USDT TRC20/ERC20)
- 📦 Live orders dashboard for admins
- 💰 Manual transaction / credit creation by admins
- 📄 CSV export of all transactions
- 🌐 Multilanguage support (en, it, ru, uk, zh_cn, he, es_mx, pt_br, hi)
- 👥 Multi-admin with per-permission configuration

---

## Screenshots

![](.media/screenshot-1.png)

![](.media/screenshot-2.png)

![](.media/screenshot-3.png)

---

## Ubuntu 20.04 VPS — Full Installation Guide

### 1. Update the system

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Python 3 and dependencies

```bash
sudo apt install -y python3 python3-pip python3-venv git
```

Verify the Python version (3.8 or higher required):

```bash
python3 --version
```

### 3. Clone the repository

```bash
cd ~
git clone https://github.com/bitbybit91/greed.git
cd greed
```

### 4. Create a Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

> **Tip:** To re-activate the virtual environment in future sessions run:
> `source ~/greed/venv/bin/activate`

### 5. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Create a Telegram bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/newbot` and follow the prompts to choose a display name and a username (must end in `bot`).
3. Copy the **bot token** (looks like `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`).

### 7. First run — generate the config file

```bash
python3 core.py
```

The bot will print:

```
FATAL | Core | A config file has been created. Customize it, then restart greed!
```

This copies `config/template_config.toml` → `config/config.toml`. Open it:

```bash
nano config/config.toml
```

#### 7a. Set the bot token

```toml
[Telegram]
token = "PASTE_YOUR_BOT_TOKEN_HERE"
```

#### 7b. Set the language

```toml
[Language]
default_language = "en"
fallback_language = "en"
```

Available language codes: `en`, `it`, `ru`, `uk`, `zh_cn`, `he`, `es_mx`, `pt_br`, `hi`

#### 7c. Set the currency

```toml
[Payments]
currency = "USD"
currency_exp = 2
currency_symbol = "$"
```

Find your currency's `currency_exp` value at:
https://core.telegram.org/bots/payments/currencies.json

#### 7d. (Optional) Enable credit card payments

1. Message [@BotFather](https://t.me/BotFather) → select your bot → **Payments** → choose a payment provider and follow the steps.
2. Copy the **payment token** into:

```toml
[Payments.CreditCard]
credit_card_token = "PASTE_YOUR_PAYMENT_TOKEN_HERE"
min_amount = 100
max_amount = 100000
```

#### 7e. (Optional) Enable crypto deposits

Crypto deposits are handled manually: the customer sends crypto and then tells the admin the transaction hash; the admin credits the balance using **Create transaction**.

```toml
[Payments.Crypto]
enable_crypto = true
bitcoin_address    = "bc1qYOUR_BTC_ADDRESS"
ethereum_address   = "0xYOUR_ETH_ADDRESS"
usdt_trc20_address = "TYOUR_TRON_USDT_ADDRESS"
usdt_erc20_address = "0xYOUR_ERC20_USDT_ADDRESS"
```

Leave any address field as `""` to hide that coin.

#### 7f. (Optional) Enable cash payment

```toml
[Payments.Cash]
enable_pay_with_cash = true
enable_create_transaction = true
```

Save and close (`Ctrl+O`, Enter, `Ctrl+X`).

### 8. Start the bot

```bash
python3 core.py
```

You should see:

```
INFO | Core | @YourBotUsername is starting!
```

Send `/start` to your bot in Telegram. **The very first user to send `/start` is automatically made the owner/admin.**

---

## Running as a Systemd Service

Running as a service keeps the bot running after SSH disconnect and restarts it automatically after crashes or reboots.

### 1. Create the service file

```bash
sudo nano /etc/systemd/system/greed.service
```

Paste (replace `YOUR_USERNAME` with your Linux user):

```ini
[Unit]
Description=Greed Telegram Shop Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/greed
ExecStart=/home/YOUR_USERNAME/greed/venv/bin/python3 core.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 2. Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable greed
sudo systemctl start greed
```

### 3. Useful commands

| Command | Purpose |
|---------|---------|
| `sudo systemctl status greed` | Show service status |
| `sudo systemctl restart greed` | Restart the bot |
| `sudo systemctl stop greed` | Stop the bot |
| `sudo journalctl -u greed -f` | Stream live logs |
| `sudo journalctl -u greed -n 100` | Show last 100 log lines |

---

## Configuration Reference

Full template: [`config/template_config.toml`](config/template_config.toml)

| Section | Key | Default | Description |
|---------|-----|---------|-------------|
| `[Language]` | `default_language` | `"it"` (template default; recommended: `"en"`) | Default language code |
| `[Language]` | `fallback_language` | `"en"` | Fallback for missing strings |
| `[Language]` | `enabled_languages` | all | List of enabled language codes |
| `[Database]` | `engine` | SQLite | SQLAlchemy database URI |
| `[Telegram]` | `token` | *(required)* | Bot token from BotFather |
| `[Telegram]` | `conversation_timeout` | `7200` | Session expiry in seconds |
| `[Telegram]` | `long_polling_timeout` | `30` | Long-poll timeout in seconds |
| `[Payments]` | `currency` | `"EUR"` | ISO 4217 currency code |
| `[Payments]` | `currency_symbol` | `"€"` | Symbol shown to users |
| `[Payments.Cash]` | `enable_pay_with_cash` | `true` | Show cash payment option |
| `[Payments.Cash]` | `enable_create_transaction` | `true` | Admins can create transactions |
| `[Payments.CreditCard]` | `credit_card_token` | `""` | Telegram Payments token (empty = disabled) |
| `[Payments.CreditCard]` | `min_amount` | `1000` | Minimum topup in minor units |
| `[Payments.CreditCard]` | `max_amount` | `10000` | Maximum topup in minor units |
| `[Payments.CreditCard]` | `fee_percentage` | `2.9` | Fee percentage charged on card topup |
| `[Payments.CreditCard]` | `fee_fixed` | `30` | Fixed fee in minor units on card topup |
| `[Payments.Crypto]` | `enable_crypto` | `false` | Show crypto deposit option |
| `[Payments.Crypto]` | `bitcoin_address` | `""` | BTC deposit address |
| `[Payments.Crypto]` | `ethereum_address` | `""` | ETH deposit address |
| `[Payments.Crypto]` | `usdt_trc20_address` | `""` | USDT (TRC20/TRON) deposit address |
| `[Payments.Crypto]` | `usdt_erc20_address` | `""` | USDT (ERC20/ETH) deposit address |
| `[Appearance]` | `display_welcome_message` | `true` | Show welcome message on /start |
| `[Appearance]` | `full_order_info` | `false` | Show full order info to customers |
| `[Appearance]` | `refill_on_checkout` | `true` | Offer topup if credit insufficient at checkout |
| `[Logging]` | `level` | `"INFO"` | Log level: DEBUG / INFO / WARNING / ERROR |

---

## Owner (Admin) Mode Guide

The **first user** to send `/start` to the bot is automatically promoted to owner. All others start as customers.

### Admin menu buttons

| Button | What it does |
|--------|-------------|
| 📝 Products | Add, edit, or delete products |
| 📦 Orders | Enter Live Orders mode to manage orders in real time |
| 💰 Create transaction | Manually add or deduct credit for any customer |
| 💳 Transaction list | Browse all transactions page by page |
| 📄 .csv | Download all transactions as a CSV spreadsheet |
| 🏵 Edit Managers | Promote users to admin and set their permissions |
| 👤 Switch to customer mode | Preview the shop as a customer would see it |

### Adding a product

1. **📝 Products → ✨ New product**
2. Enter the product **name** (must be unique).
3. Enter the **description**.
4. Enter the **price** (e.g. `9.99`). Type `X` to mark the product as "not for sale".
5. Send a **photo** or press **⏭ Skip** to add no image.
6. A ✅ confirmation appears when the product is saved.

### Editing a product

1. **📝 Products** → select the product name from the list.
2. Answer each prompt. Press **⏭ Skip** to keep the current value.

### Deleting a product

1. **📝 Products → ❌ Delete product** → select the product.
2. The product is marked as deleted and no longer visible to customers.

### Managing orders (Live Orders mode)

1. **📦 Orders** — pending orders appear immediately.
2. For each order:
   - **✅ Complete** — marks as fulfilled and notifies the customer.
   - **✴️ Refund** — prompts for a reason, refunds credit, notifies the customer.
3. New orders from customers arrive in real time.
4. Press **🛑 Stop** to exit live orders mode.

### Crediting a customer manually

1. **💰 Create transaction**
2. Select the customer.
3. Enter the amount (positive = add credit, negative = deduct credit).  
   Example: `10.00` adds $10.00; `-5.00` deducts $5.00.
4. Enter a note (the customer will see it).

> **Crypto workflow:** When a customer completes a crypto deposit, verify the on-chain transaction, then use **Create transaction** to credit their balance.

### Promoting an admin

1. **🏵 Edit Managers** → select the user → confirm promotion.
2. Toggle permissions:
   - **Edit products** — add/edit/delete products
   - **Receive orders** — access Live Orders mode
   - **Manage transactions** — create transactions, view list, download CSV
   - **Show to customer** — name appears in the Help → Contact store screen
3. **✅ Done** saves the settings.

---

## Customer Mode Guide

Customers start by sending `/start` to the bot.

### Customer menu buttons

| Button | What it does |
|--------|-------------|
| 🛒 Order products | Browse the catalog and add items to cart |
| 🛍 My orders | View the status of your last 20 orders |
| 💵 Add funds | Top up your wallet |
| 🇬🇧 Language | Change the display language |
| ❓ Help / Support | Bot guide and store contact info |
| ℹ️ Bot info | Information about the bot software |

### Placing an order

1. Press **🛒 Order products**.
2. Products appear one by one with an **➕ Add** button.
3. Press **➕ Add** to add a copy; press **➖ Remove** to remove one.
4. Scroll down to the cart summary and press **✅ Done**.
5. Optionally leave a note (press **⏭ Skip** to skip).
6. If you have enough credit the order is placed; otherwise you are prompted to top up.

### Topping up with cash

1. **💵 Add funds → 💵 With cash**
2. Your unique user ID is shown — give this to the store manager so they can credit your account.

### Topping up with a credit/debit card

1. **💵 Add funds → 💳 By credit card**
2. Select an amount or type a custom amount.
3. A Telegram payment invoice opens — complete the payment inside Telegram.

### Topping up with crypto

1. **💵 Add funds → ₿ Pay with Crypto**
2. The bot shows the wallet addresses for each enabled coin.
3. Send your crypto from your own wallet.
4. Contact the store (via **❓ Help → 👨‍💼 Contact the store**) with your transaction hash/ID so the manager can credit your balance.

---

## Troubleshooting

### Bot doesn't respond after `/start`

- Check the token is correct in `config/config.toml`.
- View logs: `sudo journalctl -u greed -f`
- The bot only works in **private chats** — it rejects group messages by design.

### "A config file has been created" on every startup

- The bot exits after creating the config. Edit `config/config.toml`, then start it again.

### Config validation errors at startup

- Every key in `config/template_config.toml` must also exist in `config/config.toml` with the **same type**.
- If you updated the bot code, compare your config with the template and add any missing sections (e.g. `[Payments.Crypto]`).

### Credit card payment doesn't add balance

- Ensure `credit_card_token` is set to a valid token.
- Use a **test** token during development (from BotFather Payments → test mode) and a **live** token in production.

### Crypto addresses not showing to customers

- Set `enable_crypto = true` under `[Payments.Crypto]`.
- Ensure at least one address field is non-empty.
- If you had an existing `config.toml`, add the `[Payments.Crypto]` block from the template.

### Orders page shows an error or crashes

- Make sure you are viewing an order that is still **pending** (not already completed or refunded).

### Bot crashes with database errors

- Check the `engine` path is correct and the bot has write permissions.
- For PostgreSQL, ensure the `psycopg2-binary` package is installed: `pip install psycopg2-binary`

### Sessions expire too quickly

Increase the timeout in `config/config.toml`:

```toml
[Telegram]
conversation_timeout = 14400  # 4 hours
```

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

Translations live in the [`strings/`](strings/) directory. Copy an existing file (e.g. `en.py`) and translate each string value.
