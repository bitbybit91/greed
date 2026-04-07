# Strings / localization file for greed
# Can be edited, but DON'T REMOVE THE REPLACEMENT FIELDS (words surrounded by {curly braces})

# Currency symbol
currency_symbol = "€"

# Positioning of the currency symbol
currency_format_string = "{symbol} {value}"

# Quantity of a product in stock
in_stock_format_string = "{quantity} available"

# Copies of a product in cart
in_cart_format_string = "{quantity} in cart"

# Product information
product_format_string = "<b>{name}</b>\n" \
                        "{description}\n" \
                        "{price}\n" \
                        "<b>{cart}</b>"

# Order number, displayed in the order info
order_number = "Order #{id}"

# Order info string, shown to the admins
order_format_string = "by {user}\n" \
                      "Created on {date}\n" \
                      "\n" \
                      "{items}\n" \
                      "TOTAL: <b>{value}</b>\n" \
                      "\n" \
                      "Customer notes: {notes}\n"

# Order info string, shown to the user
user_order_format_string = "{status_emoji} <b>Order {status_text}</b>\n" \
                           "{items}\n" \
                           "TOTAL: <b>{value}</b>\n" \
                           "\n" \
                           "Notes: {notes}\n"

# Transaction page is loading
loading_transactions = "<i>Loading transactions...\n" \
                       "Please wait a few seconds.</i>"

# Transactions page
transactions_page = "Page <b>{page}</b>:\n" \
                    "\n" \
                    "{transactions}"

# transactions.csv caption
csv_caption = "A 📄 .csv file containing all transactions stored in the bot database was generated.\n" \
              "You can open this file with other programs, such as LibreOffice Calc, to process" \
              " the data."

# Conversation: the start command was sent and the bot should welcome the user
conversation_after_start = "Hello!\n" \
                           "Welcome to greed!\n" \
                           "This is the 🅱️ <b>Beta</b> version of the software.\n" \
                           "It is fully usable, but there may be some bugs are still present.\n" \
                           "If you find any, please report them at https://github.com/Steffo99/greed/issues."

# Conversation: to send an inline keyboard you need to send a message with it
conversation_open_user_menu = "What would you like to do?\n" \
                              "💰 You have <b>{credit}</b> in your wallet.\n" \
                              "\n" \
                              "<i>Press a key on the bottom keyboard to select an operation.\n" \
                              "If the keyboard has not opened, you can open it by pressing the button with four small" \
                              " squares in the message bar.</i>"

# Conversation: like above, but for administrators
conversation_open_admin_menu = "You are a 💼 <b>Manager</b> of this store!\n" \
                               "What would you like to do?\n" \
                               "\n" \
                               "<i>Press a key on the bottom keyboard to select an operation.\n" \
                               "If the keyboard has not opened, you can open it by pressing the button with four small" \
                               " squares in the message bar.</i>"

# Conversation: select a payment method
conversation_payment_method = "How do you want to add funds to your wallet?"

# Conversation: select a product to edit
conversation_admin_select_product = "✏️ What product do you want to edit?"

# Conversation: select a product to delete
conversation_admin_select_product_to_delete = "❌ What product do you want to delete?"

# Conversation: select a user to edit
conversation_admin_select_user = "Select an user to edit."

# Conversation: click below to pay for the purchase
conversation_cart_actions = "<i>Add products to cart by scrolling up and pressing the Add button below" \
                            " the products you want to add to the cart. When you're done, go back to this message and" \
                            " press the Done button below.</i>"

# Conversation: confirm the cart contents
conversation_confirm_cart = "🛒 Your cart contains the following products:\n" \
                            "{product_list}" \
                            "Total: <b>{total_cost}</b>\n" \
                            "\n" \
                            "<i>If you want to proceed, press the Done button below this message.\n" \
                            "To cancel, press the Cancel button.</i>"

# Live orders mode: start
conversation_live_orders_start = "You are in <b>Live Orders</b> mode\n" \
                                 "All new orders placed by customers will appear in real time in this chat, and you" \
                                 " will be able to mark them as ✅ Completed" \
                                 " or ✴️ Refund the credit to the customer."

# Live orders mode: stop receiving messages
conversation_live_orders_stop = "<i>Press the Stop button below this message to stop the" \
                                " feed.</i>"

# Conversation: help menu has been opened
conversation_open_help_menu = "What kind of help do you need?"

# Conversation: confirm promotion to admin
conversation_confirm_admin_promotion = "Are you sure you want to promote this user to 💼 Manager?\n" \
                                       "It is an irreversible action!"

# Conversation: language select menu header
conversation_language_select = "Select a language:"

# Conversation: switching to user mode
conversation_switch_to_user_mode = " You are switching to 👤 Customer mode.\n" \
                                   "If you want to go back to the 💼 Manager menu, restart the conversation with /start."

# Notification: the conversation has expired
conversation_expired = "🕐  I haven't received any messages in a while, so I closed the conversation to save" \
                       " resources.\n" \
                       "If you want to start a new one, send a new /start command."

# User menu: order
menu_order = "🛒 Order products"

# User menu: order status
menu_order_status = "🛍 My orders"

# User menu: add credit
menu_add_credit = "💵 Add funds"

# User menu: bot info
menu_bot_info = "ℹ️ Bot info"

# User menu: cash
menu_cash = "💵 With cash"

# User menu: credit card
menu_credit_card = "💳 By credit card"

# Admin menu: products
menu_products = "📝️ Products"

# Admin menu: orders
menu_orders = "📦 Orders"

# Menu: transactions
menu_transactions = "💳 Transaction list"

# Menu: edit credit
menu_edit_credit = "💰 Create transaction"

# Admin menu: go to user mode
menu_user_mode = "👤 Switch to customer mode"

# Admin menu: add product
menu_add_product = "✨ New product"

# Admin menu: delete product
menu_delete_product = "❌ Delete product"

# Menu: cancel
menu_cancel = "🔙 Cancel"

# Menu: skip
menu_skip = "⏭ Skip"

# Menu: done
menu_done = "✅️ Done"

# Menu: pay invoice
menu_pay = "💳 Pay"

# Menu: complete
menu_complete = "✅ Complete"

# Menu: refund
menu_refund = "✴️ Refund"

# Menu: stop
menu_stop = "🛑 Stop"

# Menu: add to cart
menu_add_to_cart = "➕ Add"

# Menu: remove from cart
menu_remove_from_cart = "➖ Remove"

# Menu: help menu
menu_help = "❓ Help / Support"

# Menu: guide
menu_guide = "📖 Guide"

# Menu: next page
menu_next = "▶️ Next"

# Menu: previous page
menu_previous = "◀️ Previous"

# Menu: contact the shopkeeper
menu_contact_shopkeeper = "👨‍💼 Contact the store"

# Menu: generate transactions .csv file
menu_csv = "📄 .csv"

# Menu: edit admins list
menu_edit_admins = "🏵 Edit Managers"

# Menu: language
menu_language = "🇬🇧 Language"

# Emoji: unprocessed order
emoji_not_processed = "*️⃣"

# Emoji: completed order
emoji_completed = "✅"

# Emoji: refunded order
emoji_refunded = "✴️"

# Emoji: yes
emoji_yes = "✅"

# Emoji: no
emoji_no = "🚫"

# Text: unprocessed order
text_not_processed = "pending"

# Text: completed order
text_completed = "completed"

# Text: refunded order
text_refunded = "refunded"

# Text: product not for sale
text_not_for_sale = "Not for sale"

# Add product: name?
ask_product_name = "What should the product name be?"

# Add product: description?
ask_product_description = "What should the product description be?"

# Add product: price?
ask_product_price = "What should the product price be?\n" \
                    "Enter <code>X</code> if don't want the product to be for sale yet."

# Add product: image?
ask_product_image = "🖼 What image do you want the product to have?\n" \
                    "\n" \
                    "<i>Send the photo, or Skip this phase and don't add any image.</i>"

# Order product: notes?
ask_order_notes = "Would you like to leave a note along with the order?\n" \
                  "💼 It will be visible to the store Managers.\n" \
                  "\n" \
                  "<i>Send a message with the note you want to leave, or press the Skip button below this" \
                  " message to leave nothing.</i>"

# Refund product: reason?
ask_refund_reason = " Attach a reason to this refund.\n" \
                    "👤  It will be visible to the customer."

# Edit credit: notes?
ask_transaction_notes = " Attach a note to this transaction.\n" \
                        "👤 It will be visible to the customer after crediting / debiting" \
                        " and to 💼 Admins in the transaction log."

# Edit credit: amount?
ask_credit = "How do you want to change the customer's credit?\n" \
             "\n" \
             "<i>Send a message containing the amount.\n" \
             "Use the sign </i><code>+</code><i> to add credit to the customer's account," \
             " and the sign </i><code>-</code><i> to deduce it.</i>"

# Header for the edit admin message
admin_properties = "<b>Permissions of {name}:</b>"

# Edit admin: can edit products?
prop_edit_products = "Edit products"

# Edit admin: can receive orders?
prop_receive_orders = "Receive orders"

# Edit admin: can create transactions?
prop_create_transactions = "Manage transactions"

# Edit admin: show on help message?
prop_display_on_help = "Show to customer"

# Thread has started downloading an image and might be unresponsive
downloading_image = "I'm downloading your photo!\n" \
                    "It might take a while... Please be patient!\n" \
                    "I won't be able to answer you while I'm downloading."

# Edit product: current value
edit_current_value = "The current value is:\n" \
                     "<pre>{value}</pre>\n" \
                     "\n" \
                     "<i>Press the Skip button below this message to keep the same value.</i>"

# Payment: cash payment info
payment_cash = "You can pay in cash at the physical location of the store.\n" \
               "Pay at checkout, and give this id to the manager:\n" \
               "<b>{user_cash_id}</b>"

# Payment: invoice amount
payment_cc_amount = "How many funds do you want to add to your wallet?\n" \
                    "\n" \
                    "<i>Select an amount with the buttons below, or enter it manually with the normal keyboard</i>"

# Payment: add funds invoice title
payment_invoice_title = "Adding funds"

# Payment: add funds invoice description
payment_invoice_description = "Paying this invoice will add {amount} to your wallet."

# Payment: label of the labeled price on the invoice
payment_invoice_label = "Reload"

# Payment: label of the labeled price on the invoice
payment_invoice_fee_label = "Transaction fee"

# Notification: order has been placed
notification_order_placed = "A new order was placed:\n" \
                            "\n" \
                            "{order}"

# Notification: order has been completed
notification_order_completed = "Your order has been completed!\n" \
                               "\n" \
                               "{order}"

# Notification: order has been refunded
notification_order_refunded = "Your order has been refunded!\n" \
                              "\n" \
                              "{order}"

# Notification: a manual transaction was applied
notification_transaction_created = "ℹ️  A new transaction has been applied to your wallet:\n" \
                                   "{transaction}"

# Refund reason
refund_reason = "Refund reason:\n" \
                "{reason}"

# Info: informazioni sul bot
bot_info = 'This bot is using <a href="https://github.com/Steffo99/greed">greed</a>,' \
           ' a framework by @Steffo for Telegram payments released under the' \
           ' <a href="https://github.com/Steffo99/greed/blob/master/LICENSE.txt">' \
           'Affero General Public License 3.0</a>.\n'

# Help: guide
help_msg = "greed's guide is available at this address:\n" \
           "https://github.com/Steffo99/greed/wiki"

# Help: contact shopkeeper
contact_shopkeeper = "Currently, the staff available to provide user assistance is composed of:\n" \
                     "{shopkeepers}\n" \
                     "<i>Click / Tap one of their names to contact them in a Telegram chat.</i>"

# Success: product has been added/edited to the database
success_product_edited = "✅ The product has been successfully added/modified!"

# Success: product has been added/edited to the database
success_product_deleted = "✅ The product has been successfully deleted!"

# Success: order has been created
success_order_created = "✅ The order was sent successfully!\n" \
                        "\n" \
                        "{order}"

# Success: order was marked as completed
success_order_completed = "✅ You marked the order #{order_id} as completed."

# Success: order was refunded successfully
success_order_refunded = "✴️ Order #{order_id} was refunded."

# Success: transaction was created successfully
success_transaction_created = "✅ The transaction was successfully created!\n" \
                              "{transaction}"

# Error: message received not in a private chat
error_nonprivate_chat = "⚠️ This bot only works in private chats."

# Error: a message was sent in a chat, but no worker exists for that chat.
# Suggest the creation of a new worker with /start
error_no_worker_for_chat = "⚠️ The conversation with the bot was interrupted.\n" \
                           "To restart it, send the /start command to the bot."

# Error: a message was sent in a chat, but the worker for that chat is not ready.
error_worker_not_ready = "🕒 The conversation with the bot is currently starting.\n" \
                         "Please, wait a few moments before sending more commands!"

# Error: add funds amount over max
error_payment_amount_over_max = "⚠️ The maximum amount that can be added in a single transaction is {max_amount}."

# Error: add funds amount under min
error_payment_amount_under_min = "⚠️ The minimum amount that can be added in a single transaction is {min_amount}."

# Error: the invoice has expired and can't be paid
error_invoice_expired = "⚠️ This invoice has expired and was canceled. If you still want to add funds, use the Add" \
                        " funds menu option."

# Error: a product with that name already exists
error_duplicate_name = "️⚠️ A product with the same name already exists."

# Error: not enough credit to order
error_not_enough_credit = "⚠️ You do not have enough credit to place the order."

# Error: order has already been cleared
error_order_already_cleared = "⚠️  This order has already been processed."

# Error: no orders have been placed, so none can be shown
error_no_orders = "⚠️  You haven't placed any order yet, so there is nothing to display."

# Error: selected user does not exist
error_user_does_not_exist = "⚠️  The selected user does not exist."

# Fatal: conversation raised an exception
fatal_conversation_exception = "☢️ Oh no! An <b>error</b> interrupted this conversation\n" \
                               "The error was reported to the bot owner so that he can fix it.\n" \
                               "To restart the conversation, send the /start command again."

# Menu: buy bitcoin
menu_buy_bitcoin = "💰 Buy Bitcoin"

# Menu: get a wallet
menu_get_wallet = "📱 Get a Wallet"

# Buy bitcoin informational text
buy_bitcoin_text = "💰 <b>Buy Bitcoin</b>\n" \
                   "\n" \
                   "Purchase Bitcoin directly from these trusted peer-to-peer exchanges:\n" \
                   "\n" \
                   "• <b>LocalCoinSwap</b> — P2P exchange with 300+ payment methods\n" \
                   "• <b>Paxful</b> — Buy Bitcoin with gift cards, bank transfer, and more\n" \
                   "\n" \
                   "Tap a link below to get started:"

# Get wallet informational text
get_wallet_text = "📱 <b>Get a Crypto Wallet</b>\n" \
                  "\n" \
                  "You need a cryptocurrency wallet to receive your purchased coins.\n" \
                  "We recommend these trusted, non-custodial wallets:\n" \
                  "\n" \
                  "• <b>Trust Wallet</b> — Mobile wallet supporting 10M+ assets\n" \
                  "• <b>Exodus</b> — Beautiful desktop &amp; mobile wallet with built-in exchange\n" \
                  "\n" \
                  "Tap a link below to download:"

# Crypto payment: payment method selection
crypto_payment_method = "💳 <b>Payment Method</b>\n" \
                        "\n" \
                        "Choose how to pay for your order:\n" \
                        "\n" \
                        "Total: {total_cost}"

# Crypto payment: pay with wallet balance
crypto_pay_wallet = "💵 Pay with Wallet Balance"

# Crypto payment: pay with BTC
crypto_pay_btc = "₿ Pay with BTC"

# Crypto payment: pay with LTC
crypto_pay_ltc = "Ł Pay with LTC"

# Crypto payment: pay with XMR
crypto_pay_xmr = "ɱ Pay with XMR"

# Crypto payment: pay with USDT-TRC20
crypto_pay_usdt = "₮ Pay with USDT-TRC20"

# Crypto payment: pay with ZCASH
crypto_pay_zcash = "Ⓩ Pay with ZCASH"

# Crypto payment: order details with deposit address and countdown
crypto_payment_message = "📦 <b>Order #{order_id} — Pay with {coin}</b>\n" \
                         "\n" \
                         "Send exactly <code>{crypto_amount} {coin}</code> to:\n" \
                         "\n" \
                         "<code>{deposit_address}</code>\n" \
                         "\n" \
                         "💱 Rate: 1 {coin} = ${crypto_price_usd}\n" \
                         "💰 Total: ${order_total_usd} = {crypto_amount} {coin}\n" \
                         "\n" \
                         "⏳ Time remaining: {minutes}:{seconds}\n" \
                         "\n" \
                         "After sending, tap \"✅ I've Paid\" and enter your TX hash."

# Crypto payment: I've paid button
crypto_paid_button = "✅ I've Paid"

# Crypto payment: cancel button
crypto_cancel_button = "❌ Cancel"

# Crypto payment: ask for TX hash
crypto_ask_tx_hash = "Please enter your transaction hash (TX ID):"

# Crypto payment: payment submitted successfully
crypto_payment_submitted = "✅ Your payment has been submitted for verification.\n" \
                           "An admin will confirm delivery once the transaction is verified.\n" \
                           "\n" \
                           "TX Hash: <code>{tx_hash}</code>"

# Crypto payment: timer expired
crypto_payment_expired = "⏰ Payment window expired. Please start a new order."

# Crypto payment: admin notification
crypto_admin_notification = "🔔 <b>New Crypto Payment</b>\n" \
                            "Order: #{order_id}\n" \
                            "User: {user_mention}\n" \
                            "Amount: {crypto_amount} {coin}\n" \
                            "TX Hash: {tx_hash}\n" \
                            "Address: {deposit_address}\n" \
                            "\n" \
                            "Use /complete_{order_id} to confirm delivery."

# Crypto payment: price fetch error
crypto_price_error = "⚠️ Unable to fetch current crypto prices. Please try again later."

# Crypto payment: cancelled
crypto_payment_cancelled = "❌ Crypto payment cancelled."

# --- Crypto payment during product checkout (added by fix_greed.py) ---
menu_pay_wallet_balance = "\U0001f4b5 Pay with Wallet Balance"
menu_pay_crypto = "\u20bf Pay with Crypto"
checkout_select_payment = ("\U0001f4b3 <b>Payment Method</b>\n\n"
                           "Total: <b>{total}</b>\n\n"
                           "How would you like to pay?")
checkout_select_crypto = "Select which cryptocurrency to pay with:"
checkout_crypto_invoice = ("\U0001f4e6 <b>Order \u2014 Pay with {currency}</b>\n\n"
                           "Send exactly <code>{crypto_amount}</code> to:\n\n"
                           "<code>{address}</code>\n\n"
                           "\U0001f4b1 Rate: 1 {currency} = {rate}\n"
                           "\U0001f4b0 Total: {fiat_total} = {crypto_amount} {currency}\n\n"
                           "After sending, tap <b>\u2705 I\u2019ve Paid</b> and provide your TX hash.")
checkout_crypto_no_address = ("\u26a0\ufe0f No deposit address configured for {currency}. "
                              "Please try another currency or contact support.")
checkout_enter_tx_hash = "Please enter your transaction hash (TX ID):"
checkout_crypto_pending = ("\u2705 <b>Payment recorded!</b>\n\n"
                           "Order has been placed and is pending crypto payment verification.\n"
                           "TX Hash: <code>{tx_hash}</code>\n\n"
                           "An administrator will verify your payment shortly.")
checkout_ive_paid = "\u2705 I\u2019ve Paid"
checkout_cancel_crypto = "\u274c Cancel"
notification_crypto_payment = ("\U0001f514 <b>New Crypto Payment</b>\n\n"
                               "Order: #{order_id}\n"
                               "User: {user}\n"
                               "Amount: {crypto_amount} {currency}\n"
                               "TX Hash: <code>{tx_hash}</code>\n"
                               "Address: <code>{address}</code>")
error_crypto_price_unavailable = "\u26a0\ufe0f Could not fetch {currency} price. Please try again."

# --- Crypto wallet funding (added for Add Credit crypto support) ---
menu_add_credit_crypto = "₿ Pay with Crypto"
ask_add_credit_crypto_amount = ("💰 <b>Add Funds with Crypto</b>\n\n"
                                "How much would you like to deposit? (USD)\n"
                                "Min: ${min_usd}  —  Max: ${max_usd}")
error_add_credit_crypto_amount = "⚠️ Invalid amount. Please enter a value between ${min_usd} and ${max_usd}."
add_credit_select_crypto = "Select which cryptocurrency to pay with:"
add_credit_crypto_invoice = ("💳 <b>Crypto Deposit</b>\n\n"
                             "Deposit: <b>{amount_usd}</b>\n"
                             "Send exactly <code>{crypto_amount}</code> <b>{currency}</b> to:\n\n"
                             "<code>{address}</code>\n\n"
                             "💱 Rate: 1 {currency} = {rate}\n\n"
                             "After sending, tap <b>✅ I've Paid</b> and provide your TX hash.")
add_credit_crypto_success = ("✅ <b>Deposit Recorded!</b>\n\n"
                             "Amount: {amount_usd} ({crypto_amount} {currency})\n"
                             "TX Hash: <code>{tx_hash}</code>\n\n"
                             "An administrator will verify your payment shortly.\n"
                             "Your balance will be updated after confirmation.")
error_no_coins_configured = "⚠️ No coins configured for crypto payment. Please contact support."
add_credit_crypto_admin_notification = ("🔔 <b>New Crypto Deposit</b>\n\n"
                                        "User: {user}\n"
                                        "Amount: {amount_usd} ({crypto_amount} {currency})\n"
                                        "TX Hash: <code>{tx_hash}</code>\n"
                                        "Address: <code>{address}</code>")
