# Greed Bot Installation Guide

This guide provides step-by-step instructions for installing and configuring the Greed Telegram Shop Bot on a VPS for 24/7 operation.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Installing Dependencies](#installing-dependencies)
4. [Downloading Greed](#downloading-greed)
5. [Configuration](#configuration)
6. [Setting Up Blockonomics](#setting-up-blockonomics)
7. [Database Setup](#database-setup)
8. [Running as a Service](#running-as-a-service)
9. [Multiple Bot Instances](#multiple-bot-instances)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before starting, you will need:

- A VPS running Ubuntu 20.04/22.04 or Debian 11/12 (minimum 1GB RAM, 1 CPU)
- A Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- A Blockonomics API key (for Bitcoin payments) from [blockonomics.co](https://www.blockonomics.co/)
- Basic knowledge of Linux command line
- SSH access to your VPS

---

## Server Setup

### 1. Update System Packages

```bash
# Update package lists
sudo apt update

# Upgrade existing packages
sudo apt upgrade -y
```

### 2. Install Required System Packages

```bash
# Install Python and essential tools
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Install SQLite (default database)
sudo apt install -y sqlite3

# Optional: Install PostgreSQL for production use
# sudo apt install -y postgresql postgresql-contrib
```

### 3. Create a Dedicated User (Security Best Practice)

```bash
# Create greed user
sudo useradd -r -s /bin/bash -m -d /opt/greed greed

# Set password (optional, for maintenance access)
sudo passwd greed
```

---

## Installing Dependencies

### 4. Switch to Greed User

```bash
sudo su - greed
```

### 5. Create Virtual Environment

```bash
# Navigate to home directory
cd /opt/greed

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

---

## Downloading Greed

### 6. Clone the Repository

```bash
# Clone greed repository
git clone https://github.com/bitbybit91/greed.git .

# Or if already in a folder:
# git clone https://github.com/bitbybit91/greed.git /opt/greed
```

### 7. Install Python Dependencies

```bash
# Ensure virtual environment is active
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

---

## Configuration

### 8. Create Configuration File

```bash
# Copy template configuration
cp config/template_config.toml config/config.toml

# Edit configuration file
nano config/config.toml
```

### 9. Essential Configuration Options

Edit the following sections in `config/config.toml`:

#### Telegram Settings

```toml
[Telegram]
# Replace with your bot token from @BotFather
token = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

# Timeout settings (increase for better stability)
conversation_timeout = 7200
long_polling_timeout = 30
error_pause = 5
con_pool_size = 10
```

#### Payment Settings

```toml
[Payments]
# Currency code (USD, EUR, GBP, etc.)
currency = "USD"
currency_exp = 2
currency_symbol = "$"

[Payments.Cash]
enable_pay_with_cash = true
enable_create_transaction = true

[Payments.Bitcoin]
enabled = true
api_key = "YOUR_BLOCKONOMICS_API_KEY"
min_amount = 1000
max_amount = 100000
payment_timeout = 3600
min_confirmations = 1
payment_presets = [10.00, 25.00, 50.00, 100.00]
```

#### Shipping Configuration

```toml
[Shipping]
enabled = true
require_address = true

[[Shipping.methods]]
id = "dhl"
name = "DHL Express"
description = "Fast international shipping (3-5 business days)"
base_cost = 1500
cost_per_kg = 500

[[Shipping.methods]]
id = "fedex"
name = "FedEx"
description = "Reliable shipping (5-7 business days)"
base_cost = 1200
cost_per_kg = 400

[[Shipping.methods]]
id = "national"
name = "National Post"
description = "Standard domestic shipping (7-14 business days)"
base_cost = 500
cost_per_kg = 200

[[Shipping.methods]]
id = "pickup"
name = "Local Pickup"
description = "Pick up at store location (Free)"
base_cost = 0
cost_per_kg = 0
```

#### Language Settings

```toml
[Language]
enabled_languages = ["en"]
default_language = "en"
fallback_language = "en"
```

---

## Setting Up Blockonomics

### 10. Create Blockonomics Account

1. Go to [https://www.blockonomics.co/](https://www.blockonomics.co/)
2. Sign up for a merchant account
3. Navigate to **Merchants** → **API Keys**
4. Generate a new API key
5. Copy the API key to your config file

### 11. Configure Wallet in Blockonomics

1. Go to **Merchants** → **Wallet Watcher**
2. Add your Bitcoin wallet's xPub key
3. This allows Blockonomics to generate unique addresses for each payment

### 12. Set Callback URL (Optional)

For automatic payment notifications:
1. Go to **Merchants** → **Payment** settings
2. Set the callback URL (if you set up a webhook server)

---

## Database Setup

### 13. Using SQLite (Default - Simplest)

SQLite is configured by default. The database file will be created automatically.

```toml
[Database]
engine = "sqlite:///database.sqlite"
```

### 14. Using PostgreSQL (Recommended for Production)

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE USER greed WITH PASSWORD 'your_secure_password';
CREATE DATABASE greed_db OWNER greed;
GRANT ALL PRIVILEGES ON DATABASE greed_db TO greed;
\q
```

Update config:
```toml
[Database]
engine = "postgresql://greed:your_secure_password@localhost/greed_db"
```

---

## Running as a Service

### 15. Test the Bot First

```bash
# Activate virtual environment
source /opt/greed/venv/bin/activate

# Run the bot manually to test
python core.py
```

Press Ctrl+C to stop after confirming it works.

### 16. Install Systemd Service

```bash
# Exit greed user session
exit

# Copy service file
sudo cp /opt/greed/greed.service /etc/systemd/system/

# Set proper permissions
sudo chmod 644 /etc/systemd/system/greed.service

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable greed

# Start the service
sudo systemctl start greed

# Check status
sudo systemctl status greed
```

### 17. View Logs

```bash
# View recent logs
sudo journalctl -u greed -n 50

# Follow logs in real-time
sudo journalctl -u greed -f

# View logs from today
sudo journalctl -u greed --since today
```

### 18. Service Management Commands

```bash
# Stop the bot
sudo systemctl stop greed

# Restart the bot
sudo systemctl restart greed

# Disable auto-start
sudo systemctl disable greed

# Check if running
sudo systemctl is-active greed
```

---

## Multiple Bot Instances

To run multiple bots on the same server:

### 19. Create Separate Configurations

```bash
# Copy config for each bot
sudo -u greed cp /opt/greed/config/config.toml /opt/greed/config/config-shop1.toml
sudo -u greed cp /opt/greed/config/config.toml /opt/greed/config/config-shop2.toml

# Edit each configuration with different tokens and settings
sudo -u greed nano /opt/greed/config/config-shop1.toml
sudo -u greed nano /opt/greed/config/config-shop2.toml
```

### 20. Create Service Files for Each Instance

```bash
# Copy and modify service file
sudo cp /etc/systemd/system/greed.service /etc/systemd/system/greed-shop1.service
sudo cp /etc/systemd/system/greed.service /etc/systemd/system/greed-shop2.service
```

Edit each service file and change the CONFIG_PATH:

```bash
sudo nano /etc/systemd/system/greed-shop1.service
```

Change:
```ini
Environment="CONFIG_PATH=/opt/greed/config/config-shop1.toml"
```

### 21. Enable and Start Each Instance

```bash
sudo systemctl daemon-reload
sudo systemctl enable greed-shop1 greed-shop2
sudo systemctl start greed-shop1 greed-shop2
```

---

## Troubleshooting

### Common Issues

#### Bot Not Starting

```bash
# Check service status
sudo systemctl status greed

# Check for Python errors
sudo journalctl -u greed -n 100 --no-pager
```

#### Database Errors

```bash
# Check database file permissions
ls -la /opt/greed/database.sqlite

# Fix permissions if needed
sudo chown greed:greed /opt/greed/database.sqlite
```

#### Network/Telegram Errors

- Check your VPS firewall allows outbound HTTPS (port 443)
- Verify bot token is correct
- Check Telegram API status

#### Bitcoin Payment Issues

- Verify Blockonomics API key
- Check xPub is configured in Blockonomics
- Ensure payment callback is working

### Log Levels

Increase log verbosity for debugging:

```toml
[Logging]
level = "DEBUG"
```

### Reset Database

⚠️ **Warning**: This will delete all data!

```bash
# Stop service
sudo systemctl stop greed

# Backup and remove database
sudo -u greed mv /opt/greed/database.sqlite /opt/greed/database.sqlite.bak

# Start service (new database will be created)
sudo systemctl start greed
```

---

## Security Recommendations

1. **Use HTTPS** for any web callbacks
2. **Regular Updates**: Keep system and dependencies updated
3. **Firewall**: Configure UFW to only allow necessary ports
4. **Backups**: Set up regular database backups
5. **Monitoring**: Use tools like `fail2ban` and set up alerts

```bash
# Basic firewall setup
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable
```

---

## Next Steps

After installation:

1. Send `/start` to your bot on Telegram
2. You will be automatically made an admin (first user)
3. Add products through the admin menu
4. Configure shipping options
5. Test Bitcoin payments with a small amount

For more information, see the [Configuration Guide](DEPLOY.md).
