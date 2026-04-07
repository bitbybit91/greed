# Usage Guide

## For Customers

### Starting the Bot

Send `/start` to your Telegram bot to begin. The bot will greet you and display the main menu.

### Browsing Products

1. Tap **🛒 Order products** from the main menu
2. Browse the product catalog — each product shows its name, description, and price
3. Tap **➕ Add** below a product to add it to your cart
4. Tap **➖ Remove** to remove items
5. When you're done, tap **✅ Done** to proceed to checkout

### Paying with Cryptocurrency

When crypto payments are enabled, you'll see a payment method selection after confirming your cart:

1. **Add items to cart** and proceed to checkout as normal
2. **Choose a payment method:**
   - 💵 Pay with Wallet Balance (existing fiat flow)
   - ₿ Pay with BTC
   - Ł Pay with LTC
   - ɱ Pay with XMR
   - ₮ Pay with USDT-TRC20
   - Ⓩ Pay with ZCASH

3. **If you choose crypto**, you'll see:
   - The exact amount to send
   - The deposit address (tap to copy)
   - The current exchange rate
   - A countdown timer

4. **Send the exact crypto amount** to the displayed address from your wallet

5. **Tap "✅ I've Paid"** and enter your transaction hash (TX ID)
   - You can find this in your wallet's transaction history
   - It's a long string of letters and numbers

6. **Wait for admin confirmation** — the store admin will verify your transaction on the blockchain and confirm delivery

> **Important:** Send the payment before the countdown timer expires. If it expires, you'll need to start a new order (the exchange rate may have changed).

### Paying with Wallet Balance

If you have sufficient wallet credit:

1. Choose **💵 Pay with Wallet Balance**
2. The order total is deducted from your wallet credit
3. If your balance is insufficient, you'll be prompted to add funds

### Adding Funds

Tap **💵 Add funds** from the main menu to add credit to your wallet:
- **💵 With cash** — Get a payment ID to pay at a physical location
- **💳 By credit card** — Pay directly via Telegram Payments

### Buying Bitcoin

Tap **💰 Buy Bitcoin** from the main menu to see links to trusted peer-to-peer exchanges where you can purchase Bitcoin:

- **LocalCoinSwap** — P2P exchange with 300+ payment methods
- **Paxful** — Buy Bitcoin with gift cards, bank transfer, and more

### Getting a Wallet

Tap **📱 Get a Wallet** from the main menu to see recommended cryptocurrency wallets:

- **Trust Wallet** — Mobile wallet supporting millions of assets
- **Exodus** — Desktop and mobile wallet with built-in exchange

### Viewing Order Status

Tap **🛍 My orders** to see the status of your recent orders:
- *️⃣ **Pending** — Order placed, awaiting processing
- ✅ **Completed** — Order fulfilled
- ✴️ **Refunded** — Order refunded

### Changing Language

Tap **🇬🇧 Language** to select your preferred language. The bot supports:
Italian, English, Ukrainian, Russian, Chinese, Hebrew, Spanish, Portuguese, and Hindi.

---

## For Admins / Managers

### Becoming a Manager

The first user to send `/start` to a freshly configured bot is automatically promoted to 💼 Manager with full permissions. Additional managers can be promoted by the owner.

### Processing Crypto Payments

When a customer pays with cryptocurrency, you'll receive a notification:

```
🔔 New Crypto Payment
Order: #123
User: @username
Amount: 0.00123456 BTC
TX Hash: abc123def456...
Address: bc1q...
```

**To verify the payment:**

1. Copy the TX Hash from the notification
2. Check it on the appropriate block explorer:
   - **BTC:** [mempool.space/tx/{hash}](https://mempool.space)
   - **LTC:** [blockchair.com/litecoin/transaction/{hash}](https://blockchair.com/litecoin)
   - **XMR:** [xmrchain.net/tx/{hash}](https://xmrchain.net)
   - **USDT-TRC20:** [tronscan.org/#/transaction/{hash}](https://tronscan.org)
   - **ZCASH:** [explorer.zcha.in/transactions/{hash}](https://explorer.zcha.in)

3. Verify the amount and number of confirmations
4. Confirm delivery in the bot using the Live Orders mode

### Managing Products

From the admin menu, tap **📝 Products** to:
- **✨ New product** — Add a new product with name, description, price, and image
- **❌ Delete product** — Remove a product from the catalog
- Select an existing product to edit its details

### Managing Orders (Live Orders Mode)

Tap **📦 Orders** to enter Live Orders mode:
- See all pending orders in real-time
- Tap **✅ Complete** to mark an order as fulfilled
- Tap **✴️ Refund** to refund an order (with reason)

### Managing Transactions

- **💰 Create transaction** — Manually add or deduct credit from a user's wallet
- **💳 Transaction list** — Browse all transactions with pagination
- **📄 .csv** — Export all transactions as a CSV file

### Editing Managers

Tap **🏵 Edit Managers** (owner only) to promote users and configure permissions:
- **Edit products** — Can add, edit, and delete products
- **Receive orders** — Receives order notifications in Live Orders mode
- **Manage transactions** — Can create manual transactions and view logs
- **Show to customer** — Listed in the help/support contacts

### Switching to Customer Mode

Tap **👤 Switch to customer mode** to see the bot from a customer's perspective. Send `/start` again to return to the admin menu.

### Managing Multiple Bots

If you have multiple bots configured:

1. Edit `config/config.toml` to enable additional bots in the `[Bots.*]` sections
2. Each bot needs its own unique token from @BotFather
3. Set `enabled = true` for each bot you want to run
4. Restart the service — all enabled bots start automatically

Monitor all bots using the management script:
```bash
./deploy/manage-bots.sh status
./deploy/manage-bots.sh logs
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot doesn't respond to /start | Check the bot token in config.toml. Verify with @BotFather. |
| "The conversation was interrupted" | Send /start again to restart the conversation. |
| Credit card payments not working | Ensure `credit_card_token` is set in config. Verify with @BotFather. |
| Crypto prices not loading | Check internet connection. CoinGecko API may be rate-limited — wait and try again. |
| Payment timer expired | Start a new order. Crypto prices fluctuate, so a new quote is needed. |
| Bot crashes on startup | Check logs with `journalctl -u greed-swap`. Common causes: invalid token, database permissions, missing config keys. |
| Database locked (SQLite) | If running multiple bots, consider using PostgreSQL instead of SQLite. |
| Memory usage too high | Reduce `max_workers_per_bot` or `worker_idle_timeout` in config. |
| Bot not creating directories | Ensure the working directory is writable by the service user. |
| TX hash not accepted | Ensure you're entering the full transaction hash without spaces. |
