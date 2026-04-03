# Strings / localization file for greed
# Can be edited, but DON'T REMOVE THE REPLACEMENT FIELDS (words surrounded by {curly braces})

# Currency symbol
currency_symbol = "€"

# Positioning of the currency symbol
currency_format_string = "{symbol} {value}"

# Quantity of a product in stock
in_stock_format_string = "{quantity} उपलब्ध हैं"

# Copies of a product in cart
in_cart_format_string = "{quantity} कार्ट में"

# Product information
product_format_string = "<b>{name}</b>\n" \
                        "{description}\n" \
                        "{price}\n" \
                        "<b>{cart}</b>"

# Order number, displayed in the order info
order_number = "आदेश #{id}"

# Order info string, shown to the admins
order_format_string = "के द्वारा {user}\n" \
                      "तिथि पर बनाया गया: {date}\n" \
                      "\n" \
                      "{items}\n" \
                      "कुल: <b>{value}</b>\n" \
                      "\n" \
                      "ग्राहक नोट: {notes}\n"

# Order info string, shown to the user
user_order_format_string = "{status_emoji} <b>आदेश {status_text}</b>\n" \
                           "{items}\n" \
                           "कुल: <b>{value}</b>\n" \
                           "\n" \
                           "टिप्पणियाँ: {notes}\n"

# Transaction page is loading
loading_transactions = "<i>लेन-देन लोड हो रहे हैं...\n" \
                       "कृपया कुछ सेकंड प्रतीक्षा करें।</i>"

# Transactions page
transactions_page = "पृष्ठ <b>{page}</b>:\n" \
                    "\n" \
                    "{transactions}"

# transactions.csv caption
csv_caption = "बॉट डेटाबेस में संचित सभी लेन-देन को समरूपित करने वाला एक 📄 .csv फ़ाइल बनाई गई है।\n" \
              "आप इस फ़ाइल को अन्य कार्यक्रमों के साथ खोल सकते हैं, जैसे LibreOffice Calc, डेटा प्रसंस्करण के लिए।"

# Conversation: the start command was sent and the bot should welcome the user
conversation_after_start = "नमस्ते!\n" \
                           "greed में आपका स्वागत है!\n" \
                           "यह कोड सॉफ़्टवेयर का 🅱️ <b>बीटा</b> संस्करण है।\n" \
                           "यह पूरी तरह से उपयोग योग्य है, लेकिन कुछ बग्स अब भी मौजूद हो सकते हैं।\n" \
                           "यदि आपको कोई मिलता है, तो कृपया उन्हें https://github.com/Steffo99/greed/issues पर रिपोर्ट करें।"

# Conversation: to send an inline keyboard you need to send a message with it
conversation_open_user_menu = "आप क्या करना चाहेंगे?\n" \
                              "💰 आपके पास <b>{credit}</b> अपने वॉलेट में है।\n" \
                              "\n" \
                              "<i>नीचे की कीबोर्ड पर किसी ऑपरेशन का चयन करने के लिए एक कुंजी दबाएं।\n" \
                              "अगर कीबोर्ड नहीं खुला है, तो आप चार छोटे वर्ग वाले बटन को दबाकर इसे खोल सकते हैं।</i>"

# Conversation: like above, but for administrators
conversation_open_admin_menu = "आप इस दुकान के 💼 <b>प्रबंधक</b> हैं!\n" \
                               "आप क्या करना चाहेंगे?\n" \
                               "\n" \
                               "<i>एक क्रिया चुनने के लिए नीचे कीबोर्ड पर कुंजी दबाएं।\n" \
                               "अगर कीबोर्ड नहीं खुला है, तो आप मैसेज बार में चार छोटे वर्ग वाले बटन को दबाकर उसे खोल सकते हैं।</i>"

# Conversation: select a payment method
conversation_payment_method = "आप अपने वॉलेट में फंड कैसे जोड़ना चाहेंगे?"

# Conversation: select a product to edit
conversation_admin_select_product = "✏️ आप कौनसा उत्पाद संपादित करना चाहेंगे?"

# Conversation: select a product to delete
conversation_admin_select_product_to_delete = "❌ आप कौनसा उत्पाद हटाना चाहेंगे?"

# Conversation: select a user to edit
conversation_admin_select_user = "संपादित करने के लिए एक उपयोगकर्ता का चयन करें।"

# Conversation: click below to pay for the purchase
conversation_cart_actions = "<i>उपर स्क्रोल करके उन उत्पादों के नीचे जाकर उन्हें कार्ट में जोड़ने के लिए नीचे दिए गए " \
                            "जोड़ें बटन को दबाएं। जब आपका कार्ट तैयार हो, तो इस संदेश पर वापस जाएं और " \
                            "नीचे दिए गए डन बटन को दबाएं।</i>"

# Conversation: confirm the cart contents
conversation_confirm_cart = "🛒 आपका कार्ट निम्नलिखित उत्पादों को समेत रखता है:\n" \
                            "{product_list}" \
                            "कुल: <b>{total_cost}</b>\n" \
                            "\n" \
                            "<i>यदि आप आगे बढ़ना चाहते हैं, तो इस संदेश के नीचे दिए गए डन बटन को दबाएं।\n" \
                            "रद्द करने के लिए, रद्द बटन दबाएं।</i>"

# Live orders mode: start
conversation_live_orders_start = "आप <b>लाइव आदेश</b> मोड में हैं\n" \
                                 "ग्राहकों द्वारा नई आदेश प्लेस किए जाने पर वे इस चैट में वास्तविक समय में प्रकट होंगे, और आप" \
                                 " उन्हें ✅ पूरा किया गया मार्क" \
                                 " कर सकेंगे या ग्राहक को क्रेडिट ✴️ वापस कर सकेंगे।"

# Live orders mode: stop receiving messages
conversation_live_orders_stop = "<i>फ़ीड बंद करने के लिए इस संदेश के नीचे दिए गए स्टॉप बटन को दबाएं।</i>"

# Conversation: help menu has been opened
conversation_open_help_menu = "आपको किस प्रकार की सहायता चाहिए?"

# Conversation: confirm promotion to admin
conversation_confirm_admin_promotion = "क्या आप इस उपयोगकर्ता को 💼 प्रबंधक बनाना चाहते हैं?\n" \
                                       "यह एक अपरिपरिणामी क्रिया है!"

# Conversation: language select menu header
conversation_language_select = "एक भाषा चुनें:"

# Conversation: switching to user mode
conversation_switch_to_user_mode = "आप 👤 ग्राहक मोड में स्विच कर रहे हैं।\nयदि आप 💼 प्रबंधक मेनू पर वापस जाना चाहते हैं, तो /start के साथ बातचीत फिर से शुरू करें।"

# Notification: the conversation has expired
conversation_expired = "🕐 मैंने कुछ समय से कोई संदेश प्राप्त नहीं किए हैं, इसलिए मैंने संविदान को संचयन संबंधित संसाधनों को बचाने के लिए बंद कर दिया है।\nयदि आप एक नई बातचीत शुरू करना चाहते हैं, तो एक नई /start कमांड भेजें।"

# User menu: order
menu_order = "🛒 उत्पाद आर्डर करें"

# User menu: order status
menu_order_status = "🛍 मेरे आदेश"

# User menu: add credit
menu_add_credit = "💵 फंड जोड़ें"

# User menu: bot info
menu_bot_info = "ℹ️ बॉट जानकारी"

# User menu: cash
menu_cash = "💵 नकद से"

# User menu: credit card
menu_credit_card = "💳 क्रेडिट कार्ड से"

# Admin menu: products
menu_products = "📝 उत्पाद"

# Admin menu: orders
menu_orders = "📦 आदेश"

# Menu: transactions
menu_transactions = "💳 लेन-देन सूची"

# Menu: edit credit
menu_edit_credit = "💰 लेन-देन बनाएं"

# Admin menu: go to user mode
menu_user_mode = "👤 ग्राहक मोड पर स्विच करें"

# Admin menu: add product
menu_add_product = "✨ नया उत्पाद"

# Admin menu: delete product
menu_delete_product = "❌ उत्पाद हटाएं"

# Menu: cancel
menu_cancel = "🔙 रद्द करें"

# Menu: skip
menu_skip = "⏭ छोड़ें"

# Menu: done
menu_done = "✅ किया गया"

# Menu: pay invoice
menu_pay = "💳 भुगतान करें"

# Menu: complete
menu_complete = "✅ पूरा करें"

# Menu: refund
menu_refund = "✴️ वापसी"

# Menu: stop
menu_stop = "🛑 रोकें"

# Menu: add to cart
menu_add_to_cart = "➕ जोड़ें"

# Menu: remove from cart
menu_remove_from_cart = "➖ हटाएं"

# Menu: help menu
menu_help = "❓ मदद / समर्थन"

# Menu: guide
menu_guide = "📖 मार्गदर्शन"

# Menu: next page
menu_next = "▶️ अगला पृष्ठ"

# Menu: previous page
menu_previous = "◀️ पिछला पृष्ठ"

# Menu: contact the shopkeeper
menu_contact_shopkeeper = "👨‍💼 दुकानदार से संपर्क करें"

# Menu: generate transactions .csv file
menu_csv = "📄 लेन-देन .csv फ़ाइल बनाएं"

# Menu: edit admins list
menu_edit_admins = "🏵 प्रबंधक सूची संपादित करें"

# Menu: language
menu_language = "🇬🇧 भाषा"

# Emoji: unprocessed order
emoji_not_processed = "*️⃣ अप्रक्रियित आदेश"

# Emoji: completed order
emoji_completed = "✅ पूरा हुआ आदेश"

# Emoji: refunded order
emoji_refunded = "✴️ वापसी किया गया आदेश"

# Emoji: yes
emoji_yes = "✅ हां"

# Emoji: no
emoji_no = "🚫 नहीं"

# Text: unprocessed order
text_not_processed = "अप्रक्रियित"

# Text: completed order
text_completed = "पूरा हुआ"

# Text: refunded order
text_refunded = "वापसी किया गया"

# Text: product not for sale
text_not_for_sale = "बेचने के लिए नहीं"

# Add product: name?
ask_product_name = "उत्पाद का नाम क्या होना चाहिए?"

# Add product: description?
ask_product_description = "उत्पाद का विवरण क्या होना चाहिए?"

# Add product: price?
ask_product_price = "उत्पाद की मूल्य क्या होनी चाहिए?\n" \
                    "<code>X</code> दर्ज करें अगर आप इस उत्पाद को अब बेचना नहीं चाहते हैं."

# Add product: image?
ask_product_image = "🖼 आप इस उत्पाद को किस छवि के साथ चाहेंगे?\n" \
                    "<i>तस्वीर भेजें, या इस चरण को छोड़ें और कोई छवि न जोड़ें.</i>"

# Order product: notes?
ask_order_notes = "क्या आप आदेश के साथ एक नोट छोड़ना चाहेंगे?\n" \
                  "💼 यह दुकान प्रबंधकों को दिखाई देगा.\n" \
                  "<i>नोट के साथ एक संदेश भेजें जिसे आप छोड़ना चाहते हैं, या इस संदेश के नीचे स्थित" \
                  " स्किप बटन दबाकर कुछ न छोड़ें.</i>"

# Refund product: reason?
ask_refund_reason = "इस वापसी के साथ एक कारण जोड़ें।\n" \
                    "👤 यह ग्राहक को दिखाई देगा।"

# Edit credit: notes?
ask_transaction_notes = "इस लेन-देन के साथ एक नोट जोड़ें।\n" \
                        "👤 यह ग्राहक को क्रेडिट/डेबिट करने के बाद और लेन-देन लॉग में 💼 प्रबंधकों को दिखाई देगा।"

# Edit credit: amount?
ask_credit = "आप ग्राहक के क्रेडिट को कैसे बदलना चाहते हैं?\n" \
             "<i>राशि शामिल करने वाले संदेश को भेजें।\n" \
             "ग्राहक के खाते में क्रेडिट जोड़ने के लिए </i><code>+</code><i> और उसे कम करने के लिए </i><code>-</code><i> का प्रयोग करें.</i>"

# Header for the edit admin message
admin_properties = "<b>{name} की अनुमतियाँ:</b>"

# Edit admin: can edit products?
prop_edit_products = "उत्पादों को संपादित करें"

# Edit admin: can receive orders?
prop_receive_orders = "आदेश प्राप्त करें"

# Edit admin: can create transactions?
prop_create_transactions = "लेन-देन प्रबंधित करें"

# Edit admin: show on help message?
prop_display_on_help = "ग्राहक को दिखाएं"

# Thread has started downloading an image and might be unresponsive
downloading_image = "मैं आपकी तस्वीर डाउनलोड कर रहा हूँ!\n" \
                    "यह कुछ समay लग सकता है... कृपया धैर्य रखें!\n" \
                    "मैं डाउनलोड करते समay आपके सवालों का उत्तर नहीं देंगा."

# Edit product: current value
edit_current_value = "वर्तमान मूल्य है:\n" \
                     "<pre>{value}</pre>\n" \
                     "<i>इस संदेश के नीचे स्थित स्किप बटन दबाकर समान मूल्य रखने के लिए कृपया दबाएं.</i>"

# Payment: cash payment info
payment_cash = "आप दुकान के भौतिक स्थान पर नकद में भुगतान कर सकते हैं।\n" \
               "चेकआउट पर भुगतान करें, और मैनेजर को इस आईडी दें:\n" \
               "<b>{user_cash_id}</b>"

# Payment: invoice amount
payment_cc_amount = "अपने वॉलेट में कितने फंड जोड़ना चाहेंगे?\n" \
                    "<i>नीचे दिए गए बटनों के साथ एक राशि का चयन करें, या सामान्य कीबोर्ड के साथ उसे मैन्युअल रूप से दर्ज करें.</i>"

# Payment: add funds invoice title
payment_invoice_title = "फंड जोड़ना"

# Payment: add funds invoice description
payment_invoice_description = "इस चालान को भुगतान करने से {amount} आपके वॉलेट में जोड़ा जाएगा."

# Payment: label of the labeled price on the invoice
payment_invoice_label = "रीलोड"

# Payment: label of the labeled price on the invoice
payment_invoice_fee_label = "लेन-देन शुल्क"

# Notification: order has been placed
notification_order_placed = "एक नया आदेश दिया गया है:\n" \
                            "{order}"

# Notification: order has been completed
notification_order_completed = "आपका आदेश पूरा हुआ है!\n" \
                               "{order}"

# Notification: order has been refunded
notification_order_refunded = "आपका आदेश वापस किया गया है!\n" \
                              "{order}"

# Notification: a manual transaction was applied
notification_transaction_created = "ℹ️ आपके वॉलेट में एक नई लेन-देन लागू की गई है:\n" \
                                   "{transaction}"

# Refund reason
refund_reason = "वापसी का कारण:\n" \
                "{reason}"

# Info: informazioni sul bot
bot_info = 'यह बॉट <a href="https://github.com/Steffo99/greed">greed</a> का उपयोग कर रहा है,' \
           ' जो @Steffo द्वारा बनाया गया है और Telegram भुगतान के लिए जारी किया गया है' \
           ' <a href="https://github.com/Steffo99/greed/blob/master/LICENSE.txt">' \
           'Affero General Public License 3.0</a> के तहत।\n'

# Help: guide
help_msg = "greed का मार्गदर्शन इस पते पर उपलब्ध है:\n" \
           "https://github.com/Steffo99/greed/wiki"

# Help: contact shopkeeper
contact_shopkeeper = "वर्तमान में, उपयोगकर्ता सहायता प्रदान करने के लिए उपलब्ध कर्मचारी इस प्रकार हैं:\n" \
                     "{shopkeepers}\n" \
                     "<i>किसी नाम पर क्लिक/टैप करें ताकि आप उनसे एक Telegram चैट में संपर्क कर सकें.</i>"

# Success: product has been added/edited to the database
success_product_edited = "✅ उत्पाद को सफलता से जोड़ा/संशोधित किया गया है!"

# Success: product has been added/edited to the database
success_product_deleted = "✅ उत्पाद को सफलता से हटा दिया गया है!"

# Success: order has been created
success_order_created = "✅ आदेश सफलता से भेजा गया!\n" \
                        "{order}"

# Success: order was marked as completed
success_order_completed = "✅ आपने आदेश #{order_id} को पूरा किया है।"

# Success: order was refunded successfully
success_order_refunded = "✴️ आदेश #{order_id} को वापस किया गया था।"

# Success: transaction was created successfully
success_transaction_created = "✅ लेन-देन को सफलता से बनाया गया था!\n" \
                              "{transaction}"

# Error: message received not in a private chat
error_nonprivate_chat = "⚠️ यह बॉट केवल निजी चैट में काम करता है।"

# Error: a message was sent in a chat, but no worker exists for that chat.
# Suggest the creation of a new worker with /start
error_no_worker_for_chat = "⚠️ बॉट के साथ बातचीत टूट गई थी।\n" \
                           "इसे पुनः प्रारंभ करने के लिए, बॉट को /start कमांड भेजें।"

# Error: a message was sent in a chat, but the worker for that chat is not ready.
error_worker_not_ready = "🕒 बॉट के साथ बातचीत अभी प्रारंभ हो रही है।\n" \
                         "कृपया, और कमांड भेजने से पहले कुछ क्षण प्रतीक्षा करें!"

# Error: add funds amount over max
error_payment_amount_over_max = "⚠️ एक ही लेन-देन में जोड़ने की जा सकने वाली अधिकतम राशि {max_amount} है।"

# Error: add funds amount under min
error_payment_amount_under_min = "⚠️ एक ही लेन-देन में जोड़ने की जा सकने वाली न्यूनतम राशि {min_amount} है।"

# Error: the invoice has expired and can't be paid
error_invoice_expired = "⚠️ इस चालान की समय सीमा समाप्त हो गई है और यह भुगतान नहीं किया जा सकता है। अगर आप फंड जोड़ना चाहते हैं, तो 'फंड जोड़ना' मेनू विकल्प का उपयोग करें।"

# Error: a product with that name already exists
error_duplicate_name = "⚠️ इसी नाम के साथ एक उत्पाद पहले से मौजूद है।"

# Error: not enough credit to order
error_not_enough_credit = "⚠️ आपके पास आदेश देने के लिए पर्याप्त क्रेडिट नहीं है।"

# Error: order has already been cleared
error_order_already_cleared = "⚠️  इस आदेश को पहले से ही प्रक्रिया किया गया है।"

# Error: no orders have been placed, so none can be shown
error_no_orders = "⚠️  आपने अब तक कोई आदेश नहीं दिया है, इसलिए कुछ दिखाने के लिए कुछ नहीं है।"

# Error: selected user does not exist
error_user_does_not_exist = "⚠️  चयनित उपयोगकर्ता मौजूद नहीं है।"

# Fatal: conversation raised an exception
fatal_conversation_exception = "☢️ अरे नहीं! एक <b>त्रुटि</b> ने इस बातचीत को बाधित किया\n" \
                               "त्रुटि बॉट मालिक को सूचित की गई है ताकि वह इसे ठीक कर सके।\n" \
                               "बातचीत पुनः प्रारंभ करने के लिए, बॉट को /start कमांड भेजें."

# ============================================================
# CRYPTO SWAP STRINGS (English placeholders)
# ============================================================

# Menu buttons
menu_swap = "🔄 Swap"
menu_wallet = "👛 Wallet"
menu_prices = "📈 Prices"
menu_swap_history = "📜 Swap History"
menu_admin_swap_panel = "🔄 Swap Panel"
menu_admin_fee_summary = "💰 Fee Summary"
menu_admin_deposit = "⬆️ Manual Deposit"
menu_previous_page = "⬅️ Previous"
menu_next_page = "➡️ Next"

# Swap flow
swap_select_source = "🔄 <b>Swap</b>\n\nSelect the cryptocurrency you want to swap <b>from</b>:"
swap_select_destination = "🔄 <b>Swap</b>\n\nYou're swapping <b>{source}</b>.\nNow select the cryptocurrency you want to swap <b>to</b>:"
swap_enter_amount = "🔄 <b>Swap {source} → {destination}</b>\n\nEnter the amount of <b>{source}</b> you want to swap:"
swap_confirm_quote = "🔄 <b>Swap Quote</b>\n\n" \
                     "You send: <b>{source_amount}</b>\n" \
                     "You receive: <b>{destination_amount}</b>\n" \
                     "Rate: {exchange_rate}\n" \
                     "Fee: <b>{fee_amount}</b>\n\n" \
                     "⏱ This quote expires in <b>{expires_in} seconds</b>.\n\n" \
                     "Do you want to confirm this swap?"
swap_confirm = "✅ Confirm Swap"
swap_success = "✅ <b>Swap #{swap_id} completed!</b>\n\n" \
               "Sent: <b>{source_amount}</b>\n" \
               "Received: <b>{destination_amount}</b>\n" \
               "Fee paid: <b>{fee_amount}</b>"
swap_failed = "❌ <b>Swap failed</b>\n\nReason: {error}"
swap_cancelled = "❌ Swap cancelled."

# Wallet strings
wallet_balance_header = "👛 <b>Your Crypto Wallet</b>\n\n{balances}"
wallet_no_balances = "<i>No balances yet. Make a deposit to get started.</i>"
wallet_deposit = "⬇️ Deposit"
wallet_select_currency_deposit = "Select a currency to deposit:"
wallet_deposit_address = "📥 <b>Deposit {currency}</b>\n\nSend your {currency} to:\n<code>{address}</code>\n\n<i>Your balance will be credited after manual verification by the operator.</i>"
wallet_no_deposit_address = "⚠️ No deposit address configured for {currency}."

# Prices
prices_header = "📈 <b>Live Crypto Prices (USD)</b>\n\n{prices}\n\n<i>Prices from CoinGecko. Updated every 30s.</i>"

# Swap history
swap_history_header = "📜 <b>Your Swap History</b>\n\n{entries}"
swap_history_empty = "📜 You haven't made any swaps yet."
swap_history_entry = "• <b>#{swap_id}</b> {source} → {destination} | {status} | {date}"

# Admin swap strings
admin_pending_swaps_header = "🔄 <b>Pending Swaps</b>\n\n{entries}"
admin_no_pending_swaps = "✅ No pending swaps."
admin_swap_entry = "• <b>#{swap_id}</b> User {user_id} | {source} → {destination} | {date}"
admin_no_fees_collected = "💰 No fees collected yet."
admin_fee_summary_header = "💰 <b>Fee Summary</b>\n\n{lines}"
admin_deposit_enter_user_id = "Enter the <b>user ID</b> to deposit funds to:"
admin_deposit_select_currency = "Select the <b>currency</b> to deposit:"
admin_deposit_enter_amount = "Enter the <b>amount</b> of {currency} to deposit:"
admin_deposit_success = "✅ Successfully deposited <b>{amount}</b> to user <b>{user_id}</b>."
admin_deposit_failed = "❌ Deposit failed: {error}"

# Error strings
error_insufficient_crypto_balance = "⚠️ Insufficient {currency} balance. Available: {available}, required: {required}."
error_pair_not_supported = "⚠️ The trading pair {source}/{destination} is not supported."
error_price_fetch_failed = "⚠️ Could not fetch current prices: {error}\nPlease try again in a moment."
error_swap_expired = "⚠️ Your swap quote has expired. Please start a new swap."
error_invalid_amount = "⚠️ Invalid amount. Please enter a positive number (e.g. 0.5 or 100)."
