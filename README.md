<div align="center">

![](.media/icon-128x128_round.png)

# Greed

**A customizable, multilanguage Telegram shop bot with native Telegram Payments support.**

[![Documentation](https://img.shields.io/badge/docs-available-blue)](docs/README.md)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE.txt)

</div>

---

## What Is This?

**Greed** is a self-hosted Telegram bot that turns any Telegram account into a fully functional online shop. Customers browse your product catalogue, add funds to their in-bot wallet (via cash or a Telegram Payments provider), and place orders — all without leaving Telegram. Store managers receive a live stream of incoming orders and can manage products, transactions, and staff directly through the same chat interface.

It is aimed at hobbyists, small business owners, and developers who want a ready-made shop bot they can run on their own server with full control over their data.

> ⚠️ **Heads-up:** Greed started as a school finals project and is provided as-is. No uptime or support guarantees are made. Use in production at your own risk.

---

## Features

**For customers:**
- Browse and order products through an interactive Telegram menu
- Top up an in-bot wallet via cash or Telegram Payments (credit card)
- Check the status of all past orders
- Switch the bot's language from inside the chat
- Read help and information about the shop

**For store managers:**
- Create, edit, and delete products
- Receive a real-time feed of new orders to fulfil or refund
- Manually add funds to any user's wallet
- View the full transaction history
- Export transactions as a CSV file
- Promote users to manager and configure their permissions

**General:**
- 9 built-in languages: Italian, English, Ukrainian, Russian, Simplified Chinese, Hebrew, Spanish (Mexican), Brazilian Portuguese, Hindi
- Easily add new languages by creating a single Python file
- SQLite by default; PostgreSQL and other SQLAlchemy-compatible databases supported
- Docker image available for one-command deployment

---

## Requirements (Before You Start)

You will need the following tools installed on your computer or server before you begin.

| Tool | Minimum Version | How to Check | Download Link |
|------|----------------|--------------|---------------|
| **Python** — lets your computer run Python programs | 3.10 | `python3 --version` | https://www.python.org/downloads/ |
| **pip** — Python's package installer, used to download the bot's dependencies | comes with Python | `pip --version` | https://pip.pypa.io/en/stable/installation/ |
| **Git** — downloads the source code from GitHub | any recent | `git --version` | https://git-scm.com/downloads |
| **A Telegram bot token** — proves to Telegram that you own the bot | — | get one from [@BotFather](https://t.me/BotFather) | https://t.me/BotFather |
| **A Telegram Payments token** *(optional)* — enables credit-card top-ups | — | connect a payment provider in [@BotFather](https://t.me/BotFather) → Payments | https://t.me/BotFather |

> 🐳 **Prefer Docker?** If you have [Docker Engine](https://docs.docker.com/get-docker/) installed you can skip Python and pip entirely — see [Running with Docker](#running-with-docker) below.

---

## Quick Start (Copy, Paste, Done)

These six steps get the bot running as fast as possible.

**1. Clone the repository** (download the source code to your machine):
```bash
git clone https://github.com/Steffo99/greed.git
cd greed
```

**2. Create and activate a virtual environment** (keeps the bot's packages isolated from the rest of your system):
```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Generate the config file** (the bot will create `config/config.toml` and then exit — this is normal):
```bash
python -OO core.py
```

**5. Add your Telegram bot token** to `config/config.toml`:
```bash
nano config/config.toml   # or open the file in any text editor
```
Find the line that reads `token = "123456789:YOUR_TOKEN_GOES_HERE_______________"` and replace the placeholder with the token you got from [@BotFather](https://t.me/BotFather).

**6. Start the bot:**
```bash
python -OO core.py
```

Open Telegram and send `/start` to your bot. The first user to do so is automatically promoted to 💼 Manager.

---

## Detailed Installation

### Step 1 — Clone the repository

"Cloning" downloads the project files from GitHub to your computer.

```bash
git clone https://github.com/Steffo99/greed.git
cd greed
```

### Step 2 — Create a virtual environment

A virtual environment (venv) is a private folder where Python packages for this project are stored, so they don't interfere with anything else on your system.

```bash
python3 -m venv venv
```

Activate it (you must do this every time you open a new terminal):

```bash
# Linux / macOS
source venv/bin/activate

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

You'll see `(venv)` appear at the start of your prompt when it's active. ✅

### Step 3 — Install dependencies

This downloads all the Python libraries the bot needs:

```bash
pip install -r requirements.txt
```

Optionally, install coloured log output (makes the console easier to read):

```bash
pip install coloredlogs
```

### Step 4 — Create the config file

Run the bot once. It will notice that `config/config.toml` doesn't exist yet, copy the template, and exit with a message asking you to customize it:

```bash
python -OO core.py
```

Expected output:
```
FATAL    | … | A config file has been created. Customize it, then restart greed!
```

### Step 5 — Edit `config/config.toml`

Open the newly created `config/config.toml` in a text editor and fill in at minimum:

| Setting | Where to find it | Example |
|---------|-----------------|---------|
| `[Telegram] token` | [@BotFather](https://t.me/BotFather) → `/newbot` | `"110201543:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw"` |
| `[Payments.CreditCard] credit_card_token` | [@BotFather](https://t.me/BotFather) → Payments *(optional)* | `"284685063:TEST:…"` |
| `[Language] default_language` | Your choice | `"en"` |

> ⚠️ Edit **`config/config.toml`**, not `config/template_config.toml`. The template is used only to validate your config and will be overwritten on updates.

### Step 6 — Start the bot

```bash
python -OO core.py
```

Open Telegram and send `/start` to your bot. The very first person to do this becomes the manager automatically.

---

## Configuration

All configuration lives in `config/config.toml`. Two environment variables can override key settings (useful for Docker deployments).

### Environment variables

| Variable | Required? | Default | What It Does | Example |
|----------|-----------|---------|--------------|---------|
| `CONFIG_PATH` | No | `config/config.toml` | Path to the TOML config file | `/etc/greed/config.toml` |
| `DB_ENGINE` | No | value in config file | SQLAlchemy database URL; overrides `[Database] engine` in the config | `sqlite:////var/lib/greed/database.sqlite` |
| `PYTHONUNBUFFERED` | No | unset | Set to `1` to flush log output immediately (recommended in Docker) | `1` |

### Key config-file settings

| Section | Key | Default | What It Does |
|---------|-----|---------|--------------|
| `[Language]` | `default_language` | `"it"` | Language shown to users whose device language isn't available |
| `[Language]` | `fallback_language` | `"en"` | Language used when a string is missing in the user's language |
| `[Database]` | `engine` | `"sqlite:///database.sqlite"` | SQLAlchemy connection string for the database |
| `[Telegram]` | `token` | *(must be set)* | Your Telegram bot token |
| `[Telegram]` | `conversation_timeout` | `7200` | Seconds of inactivity before a user's session is discarded |
| `[Payments]` | `currency` | `"EUR"` | ISO 4217 currency code used for all prices |
| `[Payments]` | `currency_symbol` | `"€"` | Symbol shown to users next to prices |
| `[Payments.Cash]` | `enable_pay_with_cash` | `true` | Show "Pay with cash" option to users |
| `[Payments.CreditCard]` | `credit_card_token` | *(optional)* | Telegram Payments provider token; leave blank to disable card payments |
| `[Payments.CreditCard]` | `min_amount` / `max_amount` | `1000` / `10000` | Min/max top-up in the smallest currency unit (e.g. cents) |
| `[Appearance]` | `display_welcome_message` | `true` | Show a welcome message when users send `/start` |
| `[Logging]` | `level` | `"INFO"` | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `FATAL` |

### Ready-to-copy `config.toml` minimal example

```toml
[Language]
enabled_languages = ["en"]
default_language = "en"
fallback_language = "en"

[Database]
engine = "sqlite:///database.sqlite"

[Telegram]
token = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
conversation_timeout = 7200
long_polling_timeout = 30
timed_out_pause = 1
error_pause = 5
con_pool_size = 10

[Payments]
currency = "USD"
currency_exp = 2
currency_symbol = "$"

[Payments.Cash]
enable_pay_with_cash = true
enable_create_transaction = true

[Payments.CreditCard]
credit_card_token = "YOUR_PAYMENT_PROVIDER_TOKEN_HERE"
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

[Appearance]
full_order_info = false
refill_on_checkout = true
display_welcome_message = true

[Logging]
format = "{asctime} | {threadName} | {name} | {message}"
level = "INFO"
```

---

## Running the App

### Development mode (bare Python)

```bash
# Make sure your venv is active first
source venv/bin/activate

python -OO core.py
```

The `-OO` flag removes debugging assertions and docstrings, reducing memory usage. You can omit it while debugging.

### Keep it running with `screen` (simple)

`screen` is a terminal multiplexer — it keeps the bot alive even after you close your SSH session.

```bash
screen venv/bin/python -OO core.py
```

Detach by pressing **Ctrl+A** then **Ctrl+D**. Reattach later with `screen -r`.

### Keep it running with `systemd` (recommended for servers)

Assuming you installed greed in `/srv/greed`:

```bash
sudo useradd greed --system
sudo chown -R greed: /srv/greed
```

Create `/etc/systemd/system/bot-greed.service`:

```ini
[Unit]
Description=Greed Telegram Shop Bot
Wants=network-online.target
After=network-online.target nss-lookup.target

[Service]
Type=exec
User=greed
WorkingDirectory=/srv/greed
ExecStart=/srv/greed/venv/bin/python -OO /srv/greed/core.py
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl start bot-greed
sudo systemctl enable bot-greed   # auto-start on reboot
```

### Running with Docker

Docker bundles everything the bot needs into a single container — no Python installation required.

**One-shot run:**
```bash
docker run \
  --volume "$(pwd)/config:/etc/greed" \
  --volume "$(pwd)/strings:/usr/src/greed/strings" \
  --volume "$(pwd)/data:/var/lib/greed" \
  ghcr.io/steffo99/greed
```

**Run in the background and restart automatically:**
```bash
docker run \
  --detach \
  --restart always \
  --volume "$(pwd)/config:/etc/greed" \
  --volume "$(pwd)/strings:/usr/src/greed/strings" \
  --volume "$(pwd)/data:/var/lib/greed" \
  ghcr.io/steffo49/greed
```

The three `--volume` mounts are:
- `config/` → `/etc/greed` — your `config.toml` lives here
- `strings/` → `/usr/src/greed/strings` — localization files (optional customisation)
- `data/` → `/var/lib/greed` — the SQLite database is stored here

> 📝 The Docker image reads `CONFIG_PATH=/etc/greed/config.toml` and `DB_ENGINE=sqlite:////var/lib/greed/database.sqlite` by default.

---

## Verify It Works

Greed is a Telegram bot — there is no web interface or port to open. Success looks like this:

1. **Console output** after starting shows something like:
   ```
   INFO | Core | core | @YourBotName is starting!
   ```
   No `FATAL` or `ERROR` lines should appear.

2. **In Telegram**, open a chat with your bot and send `/start`.
   - The bot should greet you with a menu.
   - The very first user to send `/start` is automatically promoted to 💼 Manager and will see a manager menu.

3. **Confirm manager access** by checking the Telegram menu for manager options such as "🛍 Products", "📦 Orders", and "💳 Transactions".

---

## Project Structure

```
greed/
├── core.py              # Entry point — starts the bot, dispatches Telegram updates
├── worker.py            # Conversation handler — one thread per active user chat
├── database.py          # SQLAlchemy models and database helpers
├── localization.py      # Loads and serves translated strings
├── nuconfig.py          # TOML config loader with template-validation
├── utils.py             # Shared utility functions
├── duckbot.py           # Telegram bot factory (wraps python-telegram-bot)
├── crypto_manager.py    # Optional: cryptocurrency payment support
├── woo_importer.py      # Optional: WooCommerce product importer
├── requirements.txt     # Python dependency list
├── Dockerfile           # Container image definition
│
├── config/
│   ├── template_config.toml   # Canonical config template (do not edit)
│   ├── config.toml            # Your personal config (created on first run)
│   └── mode_config.toml       # Bot mode settings
│
├── strings/             # Localisation files, one Python module per language
│   ├── en.py            # English strings
│   ├── it.py            # Italian strings
│   └── …               # Other languages
│
├── modes/               # Pluggable shop modes
│   ├── shop_mode.py
│   ├── investment_mode.py
│   └── swap_mode.py
│
└── docs/
    └── README.md        # Extended installation and technical documentation
```

---

## Common Problems & Fixes

| Error / Symptom | Why It Happens | How To Fix It |
|-----------------|---------------|---------------|
| `FATAL … A config file has been created. Customize it, then restart greed!` | First run — `config/config.toml` didn't exist yet. | This is **expected**. Edit `config/config.toml` with your token, then run the bot again. |
| `FATAL … The token you have entered … is invalid.` | The `token` value in your config is still the placeholder or is wrong. | Copy the exact token from [@BotFather](https://t.me/BotFather) into `[Telegram] token`. |
| `FATAL … There were errors while parsing the config file.` | Your config is missing a key that exists in `template_config.toml`. | Compare your `config.toml` to `template_config.toml` and add any missing sections or keys. |
| `ModuleNotFoundError: No module named 'telegram'` | Dependencies aren't installed, or the venv isn't active. | Run `pip install -r requirements.txt` with the venv active (`source venv/bin/activate`). |
| `pip: command not found` | pip is not in your PATH. | Try `python3 -m pip install -r requirements.txt` instead. |
| Bot does not respond in Telegram | Bot started but token is wrong, or there are network issues. | Check the console for `FATAL` messages; confirm your token is correct; ensure the server has internet access. |
| Bot only works in private chats | By design — Greed ignores messages in group chats and replies with an error. | Ask users to open a direct (private) message with the bot. |
| `OperationalError: unable to open database file` | The directory for the SQLite file doesn't exist. | Create the missing directory, e.g. `mkdir -p /var/lib/greed`, then restart. |
| Docker: `config.toml not found` | The `config/` directory wasn't mounted or is empty. | Create `config/config.toml` on the host first (run `python -OO core.py` once outside Docker to generate it), then mount it. |
| `Permission denied` when writing the database | The process user doesn't have write access to the data directory. | `chmod 755 <data_dir>` or use `chown` to give the running user ownership. |

---

## Frequently Asked Questions

**Can I use a PostgreSQL database instead of SQLite?**
Yes. Set `engine` in `[Database]` to a PostgreSQL URL, e.g. `******localhost/greed`, or override it with the `DB_ENGINE` environment variable. You'll need to `pip install psycopg2-binary` as well.

**How do I add a new language?**
Copy any existing file from `strings/` (e.g. `strings/en.py`), rename it to your [IETF language tag](https://en.wikipedia.org/wiki/IETF_language_tag) (e.g. `strings/de.py`), translate the strings inside, and add the tag to `enabled_languages` in your config.

**How do I promote another user to manager?**
As an existing manager, use the manager menu inside the bot. Alternatively, the very first `/start` command ever received by the bot auto-promotes that user.

**Does the bot support multiple shops / currencies?**
No — one running instance equals one shop. Run separate instances with separate configs and databases for multiple shops.

**Is there a hosted/cloud version?**
No. Greed is self-hosted only.

---

## Contributing

Bug reports and feature requests are welcome as [GitHub Issues](https://github.com/Steffo99/greed/issues). Code improvements can be submitted as [Pull Requests](https://github.com/Steffo49/greed/pulls).

If you cannot access GitHub, you can report issues in the [Telegram group](https://t.me/greed_project) or send [git patches](https://git-scm.com/docs/git-format-patch) by email to [ste.pigozzi+patch@gmail.com](mailto:ste.pigozzi+patch@gmail.com).

Please avoid contacting the maintainer on other social media platforms.

---

## Screenshots

<div align="center">

![](.media/screenshot-1.png)

![](.media/screenshot-2.png)

![](.media/screenshot-3.png)

</div>

---

## License

Greed is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0-or-later)**. See [LICENSE.txt](LICENSE.txt) for the full text.

In plain terms: you are free to use, modify, and distribute this software, but if you run a modified version as a network service (e.g. a public bot), you must also make your modified source code available to users.
