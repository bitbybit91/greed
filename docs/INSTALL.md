# Installation Guide

## System Requirements

- **Python 3.8+** (Python 3.9+ recommended)
- **Git** for cloning the repository
- **Internet connection** (Telegram API + CoinGecko price data)
- **1+ Telegram bot tokens** from [@BotFather](https://t.me/BotFather)
- **(Optional)** A payment provider token for credit card payments
- **(Optional)** Tor for enhanced privacy with Monero/Zcash transactions

## Option A: Install via pip (Linux/macOS)

### Step 1: Clone the repository

```bash
git clone https://github.com/bitbybit91/greed.git
cd greed
```

### Step 2: Create and activate a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: (Optional) Install colored logging

```bash
pip install coloredlogs
```

### Step 5: Generate the configuration file

```bash
python -OO core.py
```

This will create `config/config.toml` from the template. The bot will exit after generating the config.

### Step 6: Edit the configuration

```bash
nano config/config.toml
```

See [CONFIG.md](CONFIG.md) for a complete reference of all configuration options.

At minimum, you need to set:
- `[Telegram] token` — Your bot token from @BotFather
- `[CryptoSwap.DepositAddresses]` — Your deposit addresses for each coin
- `[CryptoSwap.FeeAddresses]` — Your fee collection addresses

### Step 7: Start the bot

```bash
python -OO core.py
```

### Step 8: Become the Manager

Open Telegram and send `/start` to your bot. The first user to interact with the bot is automatically promoted to 💼 Manager with full permissions.

## Option B: Install via Docker

### Requirements

- [Docker Engine](https://docs.docker.com/get-docker/)
- An Internet connection
- A Telegram bot token

### Steps

1. Run the container to generate config files:

```bash
docker run --volume "$(pwd)/config:/etc/greed" \
           --volume "$(pwd)/strings:/usr/src/greed/strings" \
           --volume "$(pwd)/data:/var/lib/greed" \
           ghcr.io/steffo99/greed
```

2. Edit `config/config.toml` with your settings.

3. Start the bot:

```bash
docker run --detach --restart always \
           --volume "$(pwd)/config:/etc/greed" \
           --volume "$(pwd)/strings:/usr/src/greed/strings" \
           --volume "$(pwd)/data:/var/lib/greed" \
           ghcr.io/steffo99/greed
```

## Post-Install: First Run

1. Start the bot → it generates `config/config.toml`
2. Edit `config/config.toml` (see [CONFIG.md](CONFIG.md))
3. Restart the bot
4. Send `/start` to your bot in Telegram → you become Manager

## systemd Service Setup

For production deployment on Linux, use the provided systemd service file.

### Step 1: Create a system user

```bash
sudo useradd greed --system --home /srv/greed --shell /usr/sbin/nologin
```

### Step 2: Set up the application directory

```bash
sudo mkdir -p /srv/greed
sudo cp -r . /srv/greed/
sudo chown -R greed: /srv/greed
```

### Step 3: Create the virtual environment

```bash
sudo -u greed python3 -m venv /srv/greed/venv
sudo -u greed /srv/greed/venv/bin/pip install -r /srv/greed/requirements.txt
```

### Step 4: Install the systemd service

```bash
sudo cp deploy/greed-swap.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### Step 5: Start and enable the service

```bash
sudo systemctl start greed-swap
sudo systemctl enable greed-swap
```

### Step 6: Check status and logs

```bash
sudo systemctl status greed-swap
sudo journalctl -u greed-swap -f
```

Or use the management script:

```bash
sudo ./deploy/manage-bots.sh status
sudo ./deploy/manage-bots.sh logs
```

## Running Multiple Bots

Greed supports up to 7 bot instances running simultaneously in a single process. Each bot is configured in the `[Bots.*]` section of `config/config.toml`.

### Configuration

```toml
[Bots.bot1]
token = "YOUR_FIRST_BOT_TOKEN"
enabled = true
name = "ShopBot-1"
directory = "ShopBot-1-TG-Bot"

[Bots.bot2]
token = "YOUR_SECOND_BOT_TOKEN"
enabled = true
name = "ShopBot-2"
directory = "ShopBot-2-TG-Bot"
```

### Directory Structure

Each bot gets its own working directory (created automatically):

```
/srv/greed/
├── ShopBot-1-TG-Bot/
├── ShopBot-2-TG-Bot/
├── config/
├── core.py
└── ...
```

### Memory Considerations

With 7 bots running, memory management is enforced:

- **max_workers_per_bot** (default: 50) — Limits concurrent worker threads per bot
- **worker_idle_timeout** (default: 1800s) — Idle workers are automatically cleaned up
- The systemd service sets `MemoryMax=512M` to prevent runaway memory usage
- Maximum theoretical threads: 7 bots × 50 workers = 350 threads

### Monitoring

Use the management script to monitor all bots:

```bash
./deploy/manage-bots.sh status   # Check service status
./deploy/manage-bots.sh logs     # Follow logs in real-time
```
