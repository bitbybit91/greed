# Strings / localization file for greed
# Can be edited, but DON'T REMOVE THE REPLACEMENT FIELDS (words surrounded by {curly braces})

# Currency symbol
currency_symbol = "€"

# Positioning of the currency symbol
currency_format_string = "{symbol} {value}"

# Quantity of a product in stock
in_stock_format_string = "מוצרים למכירה {quantity}"

# Copies of a product in cart
in_cart_format_string = "פריטים בעגלה {quantity}"

# Product information
product_format_string = "<b>{name}</b>\n" \
                        "{description}\n" \
                        "{price}\n" \
                        "<b>{cart}</b>"

# Order number, displayed in the order info
order_number = " #{id} הזמנה מספר"

# Order info string, shown to the admins
order_format_string = "{user} על ידי\n" \
                      "{date} נוצר בתאריך\n" \
                      "\n" \
                      "{items}\n" \
                      "<b>{value}</b>: סך הכל\n" \
                      "\n" \
                      "{notes}: הערות הקונה\n"

# Order info string, shown to the user
user_order_format_string = "{status_emoji} <b>הזמנה {status_text}</b>\n" \
                           "{items}\n" \
                           "סך הכל: <b>{value}</b>\n" \
                           "\n" \
                           "הערות: {notes}\n"

# Transaction page is loading
loading_transactions = "<i>טוען הזמנות...\n" \
                       "פעולה זו יכולה לקחת כמה דקות</i>"

# Transactions page
transactions_page = "עמוד <b>{page}</b>:\n" \
                    "\n" \
                    "{transactions}"

# transactions.csv caption
csv_caption = "קובץ מסד נתונים עם כל פירוטי העסקאות נוצר כעת\n" \
              "תוכל להשתמש במגוון כלי מסד נתונים כדי לפתוח קובץ זה" \
              " ולראות את כל הנתונים"

# Conversation: the start command was sent and the bot should welcome the user
conversation_after_start = "! היי וברוך הבא \n" \
                           "הלקוחות שלנו חשובים לנו ונשמח לעמוד לרשותכם לכל עת בעמוד הבית"

# Conversation: to send an inline keyboard you need to send a message with it
conversation_open_user_menu = "היי וברוך הבא\n" \
                              "💰 <b>{credit}</b> :  כמה כסף יש לי בארנק\n" \
                              "\n" \
                              "<i>לחץ על הכפתור שבתפריט כדי לבחור שירות\n" \
                              "אם המקלדת נפתחה, לחץ על ארבעת הריבועים הקטנים" \
                              "בשורת הטקסט</i>"

# Conversation: like above, but for administrators
conversation_open_admin_menu = "אתה המנהל של החנות הזו <b>Manager</b>!\n" \
                               "?מה ברצונך לעשות\n" \
                               "\n" \
                               "<i>לחץ על הכפתור הרלוונטי כדי לבחור אפשרות מהתפריט\n" \
                               "אם המקלדת נפתחת, תוכל לפתוח את התפריט על ידי לחיצה על האייקון " \
                               " עם ארבעת העיגולים הקטנים בשורת ההקלדה</i>"

# Conversation: select a payment method
conversation_payment_method = "?איך תרצה לטעון כסף לחשבונך"

# Conversation: select a product to edit
conversation_admin_select_product = "✏️ איזה מוצרים תרצה לערוך"

# Conversation: select a product to delete
conversation_admin_select_product_to_delete = "❌ איזה מוצרים תרצה למחוק"

# Conversation: select a user to edit
conversation_admin_select_user = "בחר איזה משתמש תרצה לערוך"

# Conversation: click below to pay for the purchase
conversation_cart_actions = "<i>תוכל להוסיף מוצרים לעגלת הקניות בלחיצה על כפתור הוסף" \
                            " כשסיימת להוסיף את כל הפריטים תוכל לחזור להודעה זאת" \
                            " ולחץ כל כפתור בוצע לסיום</i>"

# Conversation: confirm the cart contents
conversation_confirm_cart = "🛒 העגלה שלך מכילה את הפריטים הבאים\n" \
                            "{product_list}" \
                            "<b>{total_cost}</b> :סך הכל\n" \
                            "\n" \
                            "<i>אם אתה מעוניין להמשיך, לחץ על הכפתור סיום\n" \
                            "לביטול, לחץ על מנת לבטל עסקה</i>"

# Conversation: the user activated the live orders mode
conversation_live_orders_start = "אתה כעת במצב עריכה לייב <b>Live Orders</b>\n" \
                                 "כל ההזמנות החדשות שנוצרות על ידי קונים יוצגו כאן בזמן אמת" \
                                 " ואתה תוכל לסמן אותם כבוצעו בהצלחה ✅" \
                                 " ✴️ או לבחור להחזיר את הכסף ללקוחות\n" \
                                 "\n" \
                                 "<i>לחץ על כפתור עצור בתפריט כדי לעצור את" \
                                 " הטעינה</i>"

# Conversation: help menu has been opened
conversation_open_help_menu = " ?היי, איזה עזרה אתה צריך"

# Conversation: confirm promotion to admin
conversation_confirm_admin_promotion = "?האם אתה בטוח שברצונך לקדם משתמש זה להיות מנהל\n" \
                                       "לא תוכל לבטל פעולה זו!"

# Conversation: language select menu header
conversation_language_select = "בחר שפה:"

# Conversation: switching to user mode
conversation_switch_to_user_mode = " כעת תעבור למצב שמדמה קונה בחנות.\n" \
                                   "/start אם תרצה לחזור בכל זמן לחזור לפאל הניהול, לחץ על"

# Notification: the conversation has expired
conversation_expired = "🕐 המערכת זיהתה שלא הייתה שום פעילות כבר זמן ממושך. לכן המערכת מושהית" \
                       " כדי לחסוך במשאבים\n" \
                       "/start כדי להתחיל מחדש פשוט לחצו על"

# User menu: order
menu_order = "🛒 רשימת פריטים"

# User menu: order status
menu_order_status = "🛍 ההזמנות שלי"

# User menu: add credit
menu_add_credit = "💵 טעינת כסף בחשבון"

# User menu: bot info
menu_bot_info = "ℹ ️מידע על הבוט"

# User menu: cash
menu_cash = "💵 במזומן"

# User menu: credit card
menu_credit_card = "💳 בכרטיס אשראי"

# Admin menu: products
menu_products = "📝️ מוצרים"

# Admin menu: orders
menu_orders = "📦 הזמנות"

# Menu: transactions
menu_transactions = "💳 רשימת כל העסקאות"

# Menu: edit credit
menu_edit_credit = "💰 יצירת עסקה"

# Admin menu: go to user mode
menu_user_mode = "👤 החלף למצב מדמה משתמש"

# Admin menu: add product
menu_add_product = "✨ הוספת מוצר חדש"

# Admin menu: delete product
menu_delete_product = "❌ מחיקת מוצר קיים"

# Menu: cancel
menu_cancel = "🔙 ביטול"

# Menu: skip
menu_skip = "⏭ דלג"

# Menu: done
menu_done = "✅️ בוצע"

# Menu: pay invoice
menu_pay = "💳 תשלום"

# Menu: complete
menu_complete = "✅ בוצע"

# Menu: refund
menu_refund = "✴️ החזר כספי"

# Menu: stop
menu_stop = "🛑 עצור"

# Menu: add to cart
menu_add_to_cart = "➕ הוסף"

# Menu: remove from cart
menu_remove_from_cart = "➖ מחק"

# Menu: help menu
menu_help = "❓ עזרה/תמיכה"

# Menu: guide
menu_guide = "📖 מדריך"

# Menu: next page
menu_next = "▶️ הבא"

# Menu: previous page
menu_previous = "◀️ הקודם"

# Menu: contact the shopkeeper
menu_contact_shopkeeper = "👨‍ 💼 צור קשר עם החנות"

# Menu: generate transactions .csv file
menu_csv = "📄 .csv"

# Menu: edit admins list
menu_edit_admins = "🏵 עריכת מנהלים"

# Menu: language
menu_language = "🇮🇱 שפות נוספות"

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
text_not_processed = "מושהה"

# Text: completed order
text_completed = "הסתיים"

# Text: refunded order
text_refunded = "כסף הוחזר"

# Text: product not for sale
text_not_for_sale = "לא למכירה"

# Add product: name?
ask_product_name = "איזה שם תרצה לתת למוצר?"

# Add product: description?
ask_product_description = "איזה תיאור תרצה לתת למוצר?"

# Add product: price?
ask_product_price = "מה מחיר המוצר?\n" \
                    "אם ברצונך לדגם על שלב זה כעת <code>X</code> אנא הקלד"

# Add product: image?
ask_product_image = "🖼 איזה תמונה לתת למוצר?\n" \
                    "\n" \
                    "<i>העלה תמונה, או דלג על שלב זה כעת על ידי לחיצה על כפתור דלג</i>"

# Order product: notes?
ask_order_notes = "?תרצה להשאיר הודעה לחנות\n" \
                  "💼 כך מנהלי החנות יוכלו לקרוא אותה לפני המשלוח\n" \
                  "\n" \
                  "<i>הקלד את ההודעה שתרצה להשאיר, או לחץ על דלג" \
                  " כדי לא להשאיר הודעה כלל</i>"

# Refund product: reason?
ask_refund_reason = " מה הסיבה להחזר הכסף\n" \
                    "👤  המשתמש יוכל לראות זאת"

# Edit credit: notes?
ask_transaction_notes = " הוסף הערה לעסקא זו\n" \
                        "👤 זה יוצג משתמש לאחר שהוא יטעי כסף לחשבונו" \
                        " ולמנהלים ברשימת העסקאות."

# Edit credit: amount?
ask_credit = "איך תרצה לשנות את הסכום הטעון בחשבון הלקוח?\n" \
             "\n" \
             "<i>שלח הודעה עם הסכום שתרצה להעיק לו\n" \
             " </i><code>+</code><i> השתמש בסימן הבא כדי להוסיף כסף לחשבונו" \
             " כדי להוריד סכום מחשבונו </i><code>-</code><i> והשתמש בסימן</i>"

# Header for the edit admin message
admin_properties = "<b>הרשאות של {name}:</b>"

# Edit admin: can edit products?
prop_edit_products = "עריכת פריטים"

# Edit admin: can receive orders?
prop_receive_orders = "קבלת הזמנות"

# Edit admin: can create transactions?
prop_create_transactions = "ניהול עסקאות"

# Edit admin: show on help message?
prop_display_on_help = "הצגללקוח"

# Thread has started downloading an image and might be unresponsive
downloading_image = "אני מוריד את התמונה כעת!\n" \
                    "זה יכול לקחת קצת זמן... אנא המתן בסבלנות!\n" \
                    "אני לא אוכל לענות לך בזמן שאני טוען את התמונה"

# Edit product: current value
edit_current_value = "המחיר כרגע הוא\n" \
                     "<pre>{value}</pre>\n" \
                     "\n" \
                     "<i>לחץ על כפתור דלג אם ברצונך לשמור על ערך זה</i>"

# Payment: cash payment info
payment_cash = "תוכל לשלם במזומן בחנות עצמה\n" \
               "תשלום בקופה ונא העבר זאת למנהל\n" \
               "<b>{user_cash_id}</b>"

# Payment: invoice amount
payment_cc_amount = "?איזה סכום תרצה להוסיף לחשבונך\n" \
                    "\n" \
                    "<i>בחר סכום מהרשימה, או לחלופין הקלד את הסכום שתרצה לטעון</i>"

# Payment: add funds invoice title
payment_invoice_title = "טעינת כספים"

# Payment: add funds invoice description
payment_invoice_description = " {amount}: תשלום על חשבון זה יוסיף את הסכום הבא לחשבונך "

# Payment: label of the labeled price on the invoice
payment_invoice_label = "מעדכן"

# Payment: label of the labeled price on the invoice
payment_invoice_fee_label = "עמלת העברה"

# Notification: order has been placed
notification_order_placed = "נוצרה הזמנה חדשה:\n" \
                            "\n" \
                            "{order}"

# Notification: order has been completed
notification_order_completed = "ההזמנה הוצרה בהצלחה\n" \
                               "\n" \
                               "{order}"

# Notification: order has been refunded
notification_order_refunded = "הכסף על ההזמנה הבא הוחזר בהצלחה\n" \
                              "\n" \
                              "{order}"

# Notification: a manual transaction was applied
notification_transaction_created = "ℹ️  עסקא חדשה קושרה לחשבונך\n" \
                                   "{transaction}"

# Refund reason
refund_reason = ":סיבה להחזר כספי\n" \
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
contact_shopkeeper = "המשתמשים שיכולים לספק תמיכה הם\n" \
                     "{shopkeepers}\n" \
                     "<i>לחץ על אחד השמות כדי ליצור עימם קשר בצאט פרטי</i>"

# Success: product has been added/edited to the database
success_product_edited = "✅ מוצר זה השתנה בהצלחה!"

# Success: product has been marked as deleted in the database
success_product_deleted = "✅ מוצר זה נמחק בהצלחה"

# Success: order has been created
success_order_created = "✅ ההזמנה נשלחה בהצלחה\n" \
                        "\n" \
                        "{order}"

# Success: order was marked as completed
success_order_completed = "✅ #{order_id} סימנת את העסקא הבאה כבוצעה בהצלחה"

# Success: order was refunded successfully
success_order_refunded = "✴️ #{order_id}: בוצע החזר כספי לעסקה"

# Success: transaction was created successfully
success_transaction_created = "✅ העסקה נוצרה בהצלחה\n" \
                              "{transaction}"

# Error: message received not in a private chat
error_nonprivate_chat = "⚠️ הבוט עובד רק בצאט פרטי"

# Error: a message was sent in a chat, but no worker exists for that chat.
# Suggest the creation of a new worker with /start
error_no_worker_for_chat = "⚠️ הפעילות עם הבוט הופסקה\n" \
                           "/start על מנת לחדש אותה, לחץ על"

# Error: add funds amount over max
error_payment_amount_over_max = "⚠️ הסכום המקסימלי האפשרי להוסיף לעסקה אחת הוא {max_amount}."

# Error: add funds amount under min
error_payment_amount_under_min = "⚠️ הסכום המינימלי האפשרי להוסיף לעסקה אחת הוא {min_amount}."

# Error: the invoice has expired and can't be paid
error_invoice_expired = "⚠️ החשבונית הזאת בוטלה , ולא ניתן להתשמש בה יותר. כדי לטעון כספים " \
                        " נא השתמש באפשרות טעינת הכספים מהתפריט הראשי"

# Error: a product with that name already exists
error_duplicate_name = "️⚠️ קיים בחנות מוצר בעל שם זהה"

# Error: not enough credit to order
error_not_enough_credit = "⚠️ אין לך מספיק כסף בארנק כדי לבצע את העסקה"

# Error: order has already been cleared
error_order_already_cleared = "⚠️  ההזמנה הזאתי כבר בוצעה"

# Error: no orders have been placed, so none can be shown
error_no_orders = "⚠️  לא ביצעת עדיין הזמנה, אז אין מה להציג"

# Error: selected user does not exist
error_user_does_not_exist = "⚠️  משתמש כזה לא קיים"

# Fatal: conversation raised an exception
fatal_conversation_exception = "☢️ באג גרם לקריסה An <b>error</b> הו לא\n" \
                               "הבאג דווח למנהל כדי שיוכל לטפל בבעיות אלה בעתיד\n" \
                               "/start על מנת לחדש את השיחה עם הבוט, אנא לחץ על"

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
add_credit_crypto_admin_notification = ("🔔 <b>New Crypto Deposit</b>\n\n"
                                        "User: {user}\n"
                                        "Amount: {amount_usd} ({crypto_amount} {currency})\n"
                                        "TX Hash: <code>{tx_hash}</code>\n"
                                        "Address: <code>{address}</code>")
