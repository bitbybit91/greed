<div align="center">

![](.media/icon-128x128_round.png)

# Greed

A [customizable](config/template_config.toml), [multilanguage](strings) Telegram shop bot with [Telegram Payments support](https://core.telegram.org/bots/payments).

</div>

---

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Prerequisites](#prerequisites)
- [Installation on Ubuntu VPS](#installation-on-ubuntu-vps)
  - [1. System Setup](#1-system-setup)
  - [2. Clone the Repository](#2-clone-the-repository)
  - [3. Create a Virtual Environment](#3-create-a-virtual-environment)
  - [4. Install Dependencies](#4-install-dependencies)
  - [5. Create Your Configuration File](#5-create-your-configuration-file)
  - [6. Edit the Configuration](#6-edit-the-configuration)
  - [7. Start the Bot](#7-start-the-bot)
  - [8. Run as a Background Service (systemd)](#8-run-as-a-background-service-systemd)
- [Docker Installation](#docker-installation)
- [Configuration Reference](#configuration-reference)
  - [Language](#language)
  - [Database](#database)
  - [Telegram](#telegram)
  - [Payments](#payments)
  - [Payments — Cash](#payments--cash)
  - [Payments — Credit Card](#payments--credit-card)
  - [Appearance](#appearance)
  - [Logging](#logging)
- [Environment Variables](#environment-variables)
- [Supported Languages](#supported-languages)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

**For customers:**
- Browse and order products directly in Telegram
- Add funds to a wallet via cash or credit card (Telegram Payments)
- View order history
- Switch between supported languages

**For store managers:**
- Create, edit, and delete products (with images and descriptions)
- Receive a live stream of new orders
- Manually create wallet transactions for users
- Export transaction history as CSV
- Grant and manage admin permissions

---

## Screenshots

![](.media/screenshot-1.png)

![](.media/screenshot-2.png)

![](.media/screenshot-3.png)

---

## Prerequisites

| Requirement | Details |
|---|---|
| **Operating System** | Ubuntu 20.04+ (any Debian-based distro works) |
| **Python** | 3.10 or newer |
| **Telegram Bot Token** | Obtain one from [@BotFather](https://t.me/BotFather) |
| **Payment Provider Token** *(optional)* | Obtain from [@BotFather](https://t.me/BotFather) → bot → Payments |

---

## Installation on Ubuntu VPS

### 1. System Setup

Update the package index and install the required system packages:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3.10-venv python3-pip git
```

> **Note:** On Ubuntu 22.04+, Python 3.10 is usually available by default. On older versions, you may need to add the `deadsnakes` PPA first:
> ```bash
> sudo apt install -y software-properties-common
> sudo add-apt-repository ppa:deadsnakes/ppa -y
> sudo apt update
> sudo apt install -y python3.10 python3.10-venv
> ```

Verify Python is installed:

```bash
python3 --version
```

### 2. Clone the Repository

```bash
cd /opt
sudo git clone https://github.com/Steffo99/greed.git
sudo chown -R $USER:$USER /opt/greed
cd /opt/greed
```

### 3. Create a Virtual Environment

```bash
python3.10 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Create Your Configuration File

The first time you run the bot it will automatically create `config/config.toml` from the template and exit. You can also copy it manually:

```bash
cp config/template_config.toml config/config.toml
```

### 6. Edit the Configuration

Open the config file with your preferred editor:

```bash
nano config/config.toml
```

At minimum, you **must** set these values:

```toml
[Telegram]
token = "YOUR_BOT_TOKEN_FROM_BOTFATHER"

[Payments]
currency = "USD"          # or your preferred ISO currency code
currency_exp = 2
currency_symbol = "$"

[Language]
default_language = "en"
```

See the [Configuration Reference](#configuration-reference) below for all available options.

### 7. Start the Bot

```bash
# Make sure you are inside the project directory with the venv active
cd /opt/greed
source venv/bin/activate
python -OO core.py
```

The bot will start polling for Telegram updates. You should see log output confirming a successful connection.

### 8. Run as a Background Service (systemd)

Create a systemd unit file so the bot starts on boot and restarts on failure:

```bash
sudo nano /etc/systemd/system/greed.service
```

Paste the following:

```ini
[Unit]
Description=Greed Telegram Shop Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/greed
ExecStart=/opt/greed/venv/bin/python -OO core.py
Restart=on-failure
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

> Replace `YOUR_USERNAME` with the actual Linux user that owns the `/opt/greed` directory.

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable greed
sudo systemctl start greed
```

Check the status and logs:

```bash
sudo systemctl status greed
sudo journalctl -u greed -f
```

---

## Docker Installation

If you prefer Docker, you can run the bot without installing Python on the host:

```bash
# Install Docker (if not already installed)
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable docker --now

# Create directories for persistent data
mkdir -p ~/greed/config ~/greed/data ~/greed/strings

# Copy your config file into the config directory
# (edit it before starting the container)
cp config/template_config.toml ~/greed/config/config.toml
nano ~/greed/config/config.toml

# Run the container
sudo docker run -d \
  --name greed \
  --restart unless-stopped \
  --volume ~/greed/config:/etc/greed \
  --volume ~/greed/strings:/usr/src/greed/strings \
  --volume ~/greed/data:/var/lib/greed \
  ghcr.io/steffo99/greed
```

View logs:

```bash
sudo docker logs -f greed
```

---

## Configuration Reference

All configuration lives in `config/config.toml` (TOML format). Every option is documented below.

### Language

```toml
[Language]
enabled_languages = ["it", "en", "uk", "ru", "zh_cn", "he", "es_mx", "pt_br", "hi"]
default_language = "en"
fallback_language = "en"
```

| Key | Type | Description |
|---|---|---|
| `enabled_languages` | list of strings | Language codes the bot will offer to users. |
| `default_language` | string | Language used when the user's language cannot be detected or is not enabled. |
| `fallback_language` | string | Language used when a string is missing in the user's language. Use `"en"` or `"it"` for the best coverage. |

### Database

```toml
[Database]
engine = "sqlite:///database.sqlite"
```

| Key | Type | Description |
|---|---|---|
| `engine` | string | [SQLAlchemy database URL](https://docs.sqlalchemy.org/en/14/core/engines.html). Default is a local SQLite file. Supports PostgreSQL, MySQL, and other engines. Ignored if the `DB_ENGINE` environment variable is set. |

**Examples:**

```toml
# SQLite (default)
engine = "sqlite:///database.sqlite"

# PostgreSQL
engine = "postgresql://user:password@localhost:5432/greed"

# MySQL
engine = "mysql+pymysql://user:password@localhost:3306/greed"
```

> When using PostgreSQL or MySQL, install the corresponding Python driver (`psycopg2-binary` or `PyMySQL`) in the virtual environment.

### Telegram

```toml
[Telegram]
token = "123456789:YOUR_TOKEN_GOES_HERE_______________"
conversation_timeout = 7200
long_polling_timeout = 30
timed_out_pause = 1
error_pause = 5
con_pool_size = 10
```

| Key | Type | Default | Description |
|---|---|---|---|
| `token` | string | — | **Required.** Bot token from [@BotFather](https://t.me/BotFather). |
| `conversation_timeout` | int | `7200` | Seconds of inactivity before a user conversation thread expires. |
| `long_polling_timeout` | int | `30` | Seconds to wait during long-polling before retrying. |
| `timed_out_pause` | int | `1` | Seconds to wait before retrying after a timeout. |
| `error_pause` | int | `5` | Seconds to wait before retrying after an API error. |
| `con_pool_size` | int | `10` | Size of the HTTP connection pool to Telegram. |

### Payments

```toml
[Payments]
currency = "EUR"
currency_exp = 2
currency_symbol = "€"
```

| Key | Type | Default | Description |
|---|---|---|---|
| `currency` | string | `"EUR"` | [ISO 4217](https://en.wikipedia.org/wiki/ISO_4217) currency code. |
| `currency_exp` | int | `2` | Number of decimal places (e.g., `2` for USD/EUR, `0` for JPY). See [Telegram currency list](https://core.telegram.org/bots/payments/currencies.json). |
| `currency_symbol` | string | `"€"` | Symbol shown to users in price displays. |

### Payments — Cash

```toml
[Payments.Cash]
enable_pay_with_cash = true
enable_create_transaction = true
```

| Key | Type | Default | Description |
|---|---|---|---|
| `enable_pay_with_cash` | bool | `true` | Show the "Pay with cash" option in the Add Credit menu. |
| `enable_create_transaction` | bool | `true` | Show the "Create transaction" option in the Manager menu. |

### Payments — Credit Card

```toml
[Payments.CreditCard]
credit_card_token = ""
min_amount = 1000
max_amount = 10000
payment_presets = [10.00, 25.00, 50.00, 100.00]
tip_presets = []
max_tip_amount = 0
fee_percentage = 2.9
fee_fixed = 30
name_required = true
email_required = true
phone_required = true
```

| Key | Type | Default | Description |
|---|---|---|---|
| `credit_card_token` | string | `""` | Payment provider token from [@BotFather](https://t.me/BotFather). Leave empty to disable credit card payments. |
| `min_amount` | int | `1000` | Minimum payment amount in smallest currency units (e.g., 1000 = $10.00). |
| `max_amount` | int | `10000` | Maximum payment amount in smallest currency units (e.g., 10000 = $100.00). |
| `payment_presets` | list of floats | `[10.00, 25.00, 50.00, 100.00]` | Quick-select amounts when adding wallet credit. |
| `tip_presets` | list of ints | `[]` | Suggested tip amounts in smallest currency units. Maximum 4 values. Empty disables tips. |
| `max_tip_amount` | int | `0` | Maximum tip in smallest currency units. `0` disables tipping. |
| `fee_percentage` | float | `2.9` | Percentage fee added to credit card transactions. Set to `0` to disable. |
| `fee_fixed` | int | `30` | Fixed fee in smallest currency units added to credit card transactions. Set to `0` to disable. |
| `name_required` | bool | `true` | Require the customer's name during payment. |
| `email_required` | bool | `true` | Require the customer's email during payment. |
| `phone_required` | bool | `true` | Require the customer's phone number during payment. |

> **Fee formula:** `total = amount + amount × fee_percentage / 100 + fee_fixed`

### Appearance

```toml
[Appearance]
full_order_info = false
refill_on_checkout = true
display_welcome_message = true
```

| Key | Type | Default | Description |
|---|---|---|---|
| `full_order_info` | bool | `false` | Show full order details (order number + timestamp) to customers. |
| `refill_on_checkout` | bool | `true` | Allow users to add wallet funds during checkout if balance is insufficient. |
| `display_welcome_message` | bool | `true` | Display a welcome message when a user sends `/start`. |

### Logging

```toml
[Logging]
format = "{asctime} | {threadName} | {name} | {message}"
level = "INFO"
```

| Key | Type | Default | Description |
|---|---|---|---|
| `format` | string | see above | Python [logging format string](https://docs.python.org/3/library/logging.html#logrecord-attributes). |
| `level` | string | `"INFO"` | Minimum log level. Options: `FATAL`, `ERROR`, `WARNING`, `INFO`, `DEBUG`. |

---

## Environment Variables

| Variable | Description |
|---|---|
| `CONFIG_PATH` | Override the config file path. Default: `config/config.toml` |
| `DB_ENGINE` | Override the database engine URL (takes precedence over config file). |
| `PYTHONUNBUFFERED` | Set to `1` for real-time log output (recommended for systemd/Docker). |

---

## Supported Languages

| Code | Language | Contributor |
|---|---|---|
| `it` | Italian | [Steffo99](https://github.com/Steffo99) |
| `en` | English | [DarrenWestwood](https://github.com/DarrenWestwood) |
| `uk` | Ukrainian | [pzhuk](https://github.com/pzhuk), [Trentyn](https://github.com/Trentyn) |
| `ru` | Russian | [pzhuk](https://github.com/pzhuk) |
| `zh_cn` | Simplified Chinese | [zhihuiyuze](https://github.com/zhihuiyuze) |
| `he` | Hebrew | [netanelkoli](https://github.com/netanelkoli) |
| `es_mx` | Spanish (Mexico) | [mastersuv](https://github.com/mastersuv) |
| `pt_br` | Portuguese (Brazil) | [eufelipemateus](https://github.com/eufelipemateus) |
| `hi` | Hindi | [hybridvamp](https://github.com/hybridvamp) |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `config/template_config.toml does not exist!` | Make sure you are running the bot from the project root directory (`cd /opt/greed`). |
| Bot creates `config/config.toml` and exits | This is expected on first run. Edit `config/config.toml` with your settings and run again. |
| `python: command not found` | Use `python3` instead, or activate the virtual environment (`source venv/bin/activate`). |
| Telegram API timeout errors | Check your VPS network connectivity. Increase `long_polling_timeout` or `error_pause` in the config. |
| Credit card payments not working | Ensure `credit_card_token` is set to a valid provider token from [@BotFather](https://t.me/BotFather). |
| Database errors with PostgreSQL/MySQL | Install the driver: `pip install psycopg2-binary` (PostgreSQL) or `pip install PyMySQL` (MySQL). |
| Bot not starting on reboot | Verify the systemd service is enabled: `sudo systemctl enable greed`. |
| Permission denied errors | Ensure the service user owns the project directory: `sudo chown -R YOUR_USERNAME:YOUR_USERNAME /opt/greed`. |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

---

## License

This project is licensed under the [GNU Affero General Public License v3.0 or later](LICENSE.txt).
