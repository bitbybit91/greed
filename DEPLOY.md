# Greed Bot Configuration & Deployment Guide

This guide covers advanced configuration options and deployment best practices for the Greed Telegram Shop Bot.

## Table of Contents

1. [Configuration Reference](#configuration-reference)
2. [Bitcoin Payment Setup](#bitcoin-payment-setup)
3. [Shipping Configuration](#shipping-configuration)
4. [Product Management](#product-management)
5. [Admin Management](#admin-management)
6. [Database Management](#database-management)
7. [Performance Tuning](#performance-tuning)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Backup & Recovery](#backup--recovery)
10. [Docker Deployment](#docker-deployment)

---

## Configuration Reference

### Complete Configuration File Structure

```toml
# /opt/greed/config/config.toml

# ============================================
# LANGUAGE SETTINGS
# ============================================
[Language]
# Available: it, en, uk, ru, zh_cn, he, es_mx, pt_br, hi
enabled_languages = ["en"]
default_language = "en"
fallback_language = "en"

# ============================================
# DATABASE SETTINGS
# ============================================
[Database]
# SQLite (simple, good for small shops)
engine = "sqlite:///database.sqlite"

# PostgreSQL (recommended for production)
# engine = "postgresql://user:password@localhost/dbname"

# MySQL/MariaDB
# engine = "mysql://user:password@localhost/dbname"

# ============================================
# TELEGRAM BOT SETTINGS
# ============================================
[Telegram]
# Bot token from @BotFather
token = "YOUR_BOT_TOKEN"

# Session timeout (seconds) - how long before inactive users are logged out
conversation_timeout = 7200

# Long polling timeout for getting updates
long_polling_timeout = 30

# Pause before retrying on timeout
timed_out_pause = 1

# Pause before retrying on error
error_pause = 5

# Connection pool size (increase for high traffic)
con_pool_size = 10

# ============================================
# PAYMENT SETTINGS
# ============================================
[Payments]
# ISO 4217 currency code
currency = "USD"

# Currency decimal places (2 for most currencies)
currency_exp = 2

# Display symbol
currency_symbol = "$"

# ============================================
# CASH PAYMENTS
# ============================================
[Payments.Cash]
# Allow cash payments
enable_pay_with_cash = true

# Allow admins to manually create transactions
enable_create_transaction = true

# ============================================
# BITCOIN PAYMENTS (Blockonomics)
# ============================================
[Payments.Bitcoin]
# Enable Bitcoin payments
enabled = true

# Blockonomics API key
api_key = "YOUR_BLOCKONOMICS_API_KEY"

# Minimum payment (in cents/minimum currency units)
min_amount = 1000  # $10.00

# Maximum payment
max_amount = 100000  # $1000.00

# Payment timeout (seconds)
payment_timeout = 3600  # 1 hour

# Required blockchain confirmations
# 0 = instant (risky), 1 = recommended, 3+ = high security
min_confirmations = 1

# Quick-select amounts for user convenience
payment_presets = [10.00, 25.00, 50.00, 100.00]

# ============================================
# SHIPPING SETTINGS
# ============================================
[Shipping]
# Enable shipping for physical products
enabled = true

# Require address for shipping
require_address = true

# ============================================
# SHIPPING METHODS
# ============================================
# Add as many methods as needed

[[Shipping.methods]]
id = "dhl"
name = "DHL Express"
description = "Fast international shipping (3-5 business days)"
base_cost = 1500  # Base cost in cents ($15.00)
cost_per_kg = 500  # Additional cost per kg ($5.00)

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
description = "Pick up at store (Free)"
base_cost = 0
cost_per_kg = 0

# ============================================
# APPEARANCE SETTINGS
# ============================================
[Appearance]
# Show full order details to customers
full_order_info = false

# Allow adding funds during checkout if balance is low
refill_on_checkout = true

# Show welcome message on /start
display_welcome_message = true

# ============================================
# LOGGING SETTINGS
# ============================================
[Logging]
# Log format
format = "{asctime} | {threadName} | {name} | {message}"

# Log level: FATAL, ERROR, WARNING, INFO, DEBUG
level = "INFO"
```

---

## Bitcoin Payment Setup

### Step 1: Create Blockonomics Account

```bash
# Navigate to Blockonomics website
# https://www.blockonomics.co/

# Sign up for a merchant account
# Verify your email
```

### Step 2: Add Your Bitcoin Wallet

1. **Go to Merchants → Wallet Watcher**
2. **Add your wallet's xPub key**
   
   To get xPub from common wallets:
   
   - **Electrum**: Wallet → Information → Master Public Key
   - **Ledger Live**: Account → Advanced → Extended public key
   - **Trezor**: Settings → Device → Show xPub

### Step 3: Generate API Key

1. **Go to Merchants → API Keys**
2. **Click "Generate New API Key"**
3. **Copy the key to your config file**

```toml
[Payments.Bitcoin]
api_key = "Your-Generated-API-Key-Here"
```

### Step 4: Configure Payment Settings

```toml
[Payments.Bitcoin]
enabled = true
api_key = "YOUR_API_KEY"

# Set appropriate limits based on your business
min_amount = 500      # $5.00 minimum
max_amount = 50000    # $500.00 maximum

# For faster checkout, use 0 confirmations (higher risk)
# For valuable items, use 2-3 confirmations
min_confirmations = 1

# Give users 1 hour to complete payment
payment_timeout = 3600
```

### Testing Bitcoin Payments

1. Send `/start` to your bot
2. Select "Add funds" → "Pay with Bitcoin"
3. Create a small test payment
4. Send Bitcoin to the displayed address
5. Wait for confirmation

---

## Shipping Configuration

### Adding Custom Shipping Methods

```toml
[[Shipping.methods]]
id = "express"                    # Unique identifier
name = "Express Shipping"         # Display name
description = "Next day delivery" # Description shown to users
base_cost = 2000                  # Base cost: $20.00
cost_per_kg = 1000                # Per kg: $10.00
```

### Shipping Cost Calculation

The shipping cost is calculated as:

```
Total Shipping = base_cost + (weight_kg × cost_per_kg)
```

Example:
- Product weight: 2.5 kg
- DHL: $15.00 base + (2.5 × $5.00) = $27.50

### Disabling Shipping

For digital-only stores:

```toml
[Shipping]
enabled = false
```

---

## Product Management

### Adding Products via Bot

1. Start the bot as an admin
2. Select "Products" from the menu
3. Select "New product"
4. Enter:
   - Product name
   - Description
   - Price (or 'X' for not for sale)
   - Weight (in grams, 0 for digital)
   - Image (optional)

### Product Weight Guidelines

- **Digital products**: 0g (no shipping required)
- **Light items** (books, electronics): 100-500g
- **Medium items** (clothing): 200-1000g
- **Heavy items** (equipment): 1000g+

### Managing Product Inventory

The bot doesn't track inventory by default. For stock management:

1. Set product as "not for sale" when out of stock
2. Create multiple product variants for different stock levels
3. Consider custom modifications for inventory tracking

---

## Admin Management

### First Admin Setup

The first user to send `/start` to the bot becomes the owner admin with full permissions.

### Adding Additional Admins

1. As owner, go to Admin menu
2. Select "Edit Managers"
3. Select a user
4. Toggle permissions:
   - **Edit Products**: Can add/edit/delete products
   - **Receive Orders**: Sees orders in live mode
   - **Manage Transactions**: Can create manual transactions
   - **Show to Customer**: Displayed in help/contact

### Admin Permission Reference

| Permission | Description |
|------------|-------------|
| edit_products | Create, modify, delete products |
| receive_orders | View and process orders in live mode |
| create_transactions | Manually credit/debit user wallets |
| display_on_help | Username shown in customer support |
| is_owner | Full access + manage other admins |

---

## Database Management

### SQLite Management

```bash
# View database
sqlite3 /opt/greed/database.sqlite

# List tables
.tables

# View users
SELECT * FROM users LIMIT 10;

# View recent orders
SELECT * FROM orders ORDER BY creation_date DESC LIMIT 10;

# Exit
.quit
```

### PostgreSQL Management

```bash
# Connect to database
sudo -u postgres psql greed_db

# List tables
\dt

# View users
SELECT * FROM users LIMIT 10;

# Exit
\q
```

### Database Migration

To switch from SQLite to PostgreSQL:

```bash
# 1. Export SQLite data
sqlite3 /opt/greed/database.sqlite .dump > backup.sql

# 2. Update config to PostgreSQL
# Edit config.toml

# 3. Restart bot (creates new tables)
sudo systemctl restart greed

# 4. Import data (may need SQL syntax adjustments)
psql greed_db < backup.sql
```

---

## Performance Tuning

### For High-Traffic Shops

```toml
[Telegram]
# Increase connection pool
con_pool_size = 20

# Adjust timeouts
conversation_timeout = 3600
long_polling_timeout = 60
error_pause = 2
```

### Memory Optimization

```bash
# Monitor memory usage
htop

# Set memory limits in systemd
sudo nano /etc/systemd/system/greed.service
```

Add to `[Service]` section:
```ini
MemoryLimit=512M
```

### Database Optimization

For PostgreSQL:

```sql
-- Analyze tables for better query planning
ANALYZE;

-- Vacuum to reclaim space
VACUUM ANALYZE;
```

For SQLite:

```bash
sqlite3 /opt/greed/database.sqlite "VACUUM;"
```

---

## Monitoring & Maintenance

### Setting Up Log Rotation

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/greed
```

```
/var/log/greed/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 greed greed
}
```

### Health Check Script

```bash
#!/bin/bash
# /opt/greed/healthcheck.sh

if ! systemctl is-active --quiet greed; then
    echo "Greed bot is down! Restarting..."
    systemctl restart greed
    # Optional: Send alert
    # curl -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
    #      -d "chat_id=$ADMIN_ID&text=Bot restarted!"
fi
```

```bash
# Make executable
chmod +x /opt/greed/healthcheck.sh

# Add to crontab (check every 5 minutes)
crontab -e
*/5 * * * * /opt/greed/healthcheck.sh
```

### Monitoring Commands

```bash
# Check service status
sudo systemctl status greed

# View recent logs
sudo journalctl -u greed -n 100

# Watch logs in real-time
sudo journalctl -u greed -f

# Check resource usage
htop -p $(pgrep -f "python.*core.py")
```

---

## Backup & Recovery

### Automated Backup Script

```bash
#!/bin/bash
# /opt/greed/backup.sh

BACKUP_DIR="/opt/greed/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp /opt/greed/database.sqlite "$BACKUP_DIR/database_$DATE.sqlite"

# Backup config
cp /opt/greed/config/config.toml "$BACKUP_DIR/config_$DATE.toml"

# Keep only last 7 days of backups
find $BACKUP_DIR -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Schedule daily backup
crontab -e
0 3 * * * /opt/greed/backup.sh >> /var/log/greed-backup.log 2>&1
```

### Recovery Steps

```bash
# Stop service
sudo systemctl stop greed

# Restore database
cp /opt/greed/backups/database_YYYYMMDD.sqlite /opt/greed/database.sqlite
chown greed:greed /opt/greed/database.sqlite

# Start service
sudo systemctl start greed
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "core.py"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  greed:
    build: .
    restart: always
    volumes:
      - ./config:/app/config
      - ./database.sqlite:/app/database.sqlite
    environment:
      - CONFIG_PATH=/app/config/config.toml
```

### Running with Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Multiple Instances with Docker

```yaml
version: '3.8'

services:
  shop1:
    build: .
    restart: always
    volumes:
      - ./config/shop1.toml:/app/config/config.toml
      - ./data/shop1.sqlite:/app/database.sqlite
    environment:
      - CONFIG_PATH=/app/config/config.toml

  shop2:
    build: .
    restart: always
    volumes:
      - ./config/shop2.toml:/app/config/config.toml
      - ./data/shop2.sqlite:/app/database.sqlite
    environment:
      - CONFIG_PATH=/app/config/config.toml
```

---

## Common Commands Reference

| Task | Command |
|------|---------|
| Start bot | `sudo systemctl start greed` |
| Stop bot | `sudo systemctl stop greed` |
| Restart bot | `sudo systemctl restart greed` |
| View status | `sudo systemctl status greed` |
| View logs | `sudo journalctl -u greed -f` |
| Edit config | `sudo -u greed nano /opt/greed/config/config.toml` |
| Test config | `sudo -u greed python3 /opt/greed/core.py` |
| Backup DB | `cp database.sqlite database.sqlite.bak` |

---

## Support

For issues and feature requests, please open an issue on GitHub or contact the store administrators listed in the bot's help menu.
