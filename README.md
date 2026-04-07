<div align="center"> 

![](.media/icon-128x128_round.png) 

# Greed

[Customizable](config/template_config.toml) and [multilanguage](strings) Telegram shop bot with [Telegram Payments support](https://core.telegram.org/bots/payments) and cryptocurrency payment integration.

</div>

## Features

- **For customers:**
  - Browse and order products
  - Pay with wallet balance, credit card, or cryptocurrency (BTC, LTC, XMR, USDT-TRC20, ZCASH)
  - Buy Bitcoin via trusted P2P exchanges
  - Get a crypto wallet recommendation
  - View order status and history
  - Multi-language support (9 languages)

- **For store managers:**
  - Create, edit, and delete products
  - Receive live order notifications
  - Process crypto payments with TX hash verification
  - Manage transactions and export to CSV
  - Run up to 7 bot instances simultaneously

## Documentation

| Guide | Description |
|-------|-------------|
| [📦 Installation Guide](docs/INSTALL.md) | System requirements, setup, and deployment |
| [⚙️ Configuration Reference](docs/CONFIG.md) | Every config option explained |
| [📖 Usage Guide](docs/USAGE.md) | How-to for customers and admins |
| [📋 Legacy Docs](docs/README.md) | Original documentation and technical details |

## Quick Start

```bash
git clone https://github.com/bitbybit91/greed.git
cd greed
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -OO core.py  # generates config
nano config/config.toml  # add your bot token
python -OO core.py  # start the bot
```

Then send `/start` to your bot in Telegram.

## Screenshots

![](.media/screenshot-1.png)

![](.media/screenshot-2.png)

![](.media/screenshot-3.png)
