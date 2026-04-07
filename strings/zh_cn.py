# Strings / localization file for greed
# Can be edited, but DON'T REMOVE THE REPLACEMENT FIELDS (words surrounded by {curly braces})

# Currency symbol
currency_symbol = "¥"

# Positioning of the currency symbol
currency_format_string = "{symbol} {value}"

# Quantity of a product in stock
in_stock_format_string = "{quantity} 可用"

# Copies of a product in cart
in_cart_format_string = "{quantity} 在购物车中"

# Product information
product_format_string = "<b>{name}</b>\n" \
                        "{description}\n" \
                        "{price}\n" \
                        "<b>{cart}</b>"

# Order number, displayed in the order info
order_number = "订单号 #{id}"

# Order info string, shown to the admins
order_format_string = "来自 {user}\n" \
                      "创建于 {date}\n" \
                      "\n" \
                      "{items}\n" \
                      "总计: <b>{value}</b>\n" \
                      "\n" \
                      "客户注释: {notes}\n"

# Order info string, shown to the user
user_order_format_string = "{status_emoji} <b>订单 {status_text}</b>\n" \
                           "{items}\n" \
                           "总计: <b>{value}</b>\n" \
                           "\n" \
                           "注释: {notes}\n"

# Transaction page is loading
loading_transactions = "<i>正在载入交易中...\n" \
                       "请稍等片刻.....</i>"

# Transactions page
transactions_page = "Page <b>{page}</b>:\n" \
                    "\n" \
                    "{transactions}"

# transactions.csv caption
csv_caption = "生成了一个📄.csv文件,其中包含bot的数据库中多所有事物\n" \
              "您可以使用其他程序(例如LibreOffice Calc)打开此文件并进行处理数据" \
 \
# Conversation: the start command was sent and the bot should welcome the user
conversation_after_start = "您好!\n" \
                           "欢迎使用greed系统!\n" \
                           "此软件版本是🅱️ <b>的Beta</b>版本.\n" \
                           "它完全可用，但可能仍然存在一些错误.\n" \
                           "“如果发现任何问题，请在https://github.com/Steffo99/greed/issues 中报告."

# Conversation: to send an inline keyboard you need to send a message with it
conversation_open_user_menu = "您想做什么?\n" \
                              "💰 您有<b>{credit}</b>在您的钱包里.\n" \
                              "\n" \
                              "<i>按底部键盘上的键以选择操作.\n" \
                              "如果选项框尚未打开，则可以通过按四个小按钮来打开它." \
                              "也就是消息栏中的方块.</i>"

# Conversation: like above, but for administrators
conversation_open_admin_menu = "您是这家店的💼 <b>经理</b>\n" \
                               "您想做什么?\n" \
                               "\n" \
                               "<i>按底部键盘上的键以选择操作.\n" \
                               "如果选项框尚未打开，则可以通过按四个小按钮来打开它." \
                               "也就是消息栏中的方块.</i>"

# Conversation: select a payment method
conversation_payment_method = "您想如何向您的钱包充值？"

# Conversation: select a product to edit
conversation_admin_select_product = "✏️ 您要编辑什么产品？"

# Conversation: select a product to delete
conversation_admin_select_product_to_delete = "❌ 您要删除什么产品?"

# Conversation: select a user to edit
conversation_admin_select_user = "选择要编辑的用户."

# Conversation: click below to pay for the purchase
conversation_cart_actions = "<i>向上滚动并按下下面的添加按钮，将产品添加到购物车." \
                            " 您要添加到购物车的产品。完成后，返回此消息，然后" \
                            " 按下面的“完成”按钮.</i>"

# Conversation: confirm the cart contents
conversation_confirm_cart = "🛒 您的购物车包含以下产品:\n" \
                            "{product_list}" \
                            "总共: <b>{total_cost}</b>\n" \
                            "\n" \
                            "<i>如果要继续，请按此消息下方的“完成”按钮.\n" \
                            "如果要取消，请按取消按钮.</i>"

# Live orders mode: start
# TODO: This string is incomplete!
# conversation_live_orders_start = "您处于<b>实时订单</b>模式\n" \
#                                  "客户下的所有新订单将实时显示在此聊天中," \
#                                  "您可以将能够将它们标记为 ✅ 已完成." \
#                                  " 或者 ✴️ 您可以退款给客户.\n" \
#                                  " 反馈</i>"

# Live orders mode: stop receiving messages
# TODO: This string is missing.
# conversation_live_orders_stop = ""

# Conversation: help menu has been opened
conversation_open_help_menu = "您需要什么样的帮助?"

# Conversation: confirm promotion to admin
conversation_confirm_admin_promotion = "您确定要将此用户提升为💼经理吗？\n" \
                                       "这是不可逆转的行动!"

# Conversation: language select menu header
conversation_language_select = "选择一种语言:"

# Conversation: switching to user mode
conversation_switch_to_user_mode = " 您将切换到👤客户模式.\n" \
                                   "如果您想重新回到💼经理,请使用 /start."

# Notification: the conversation has expired
conversation_expired = "🕐  我有一段时间没有收到任何消息，因此我关闭了对话以保存" \
                       "资源.\n" \
                       "如果您要开始一个新的，发送一个新的/start 命令."

# User menu: order
menu_order = "🛒 订单"

# User menu: order status
menu_order_status = "🛍 我的订单"

# User menu: add credit
menu_add_credit = "💵 增加资金"

# User menu: bot info
menu_bot_info = "ℹ️ 关于机器人"

# User menu: cash
menu_cash = "💵 用现金"

# User menu: credit card
menu_credit_card = "💳 用信用卡"

# Admin menu: products
menu_products = "📝️ 产品展示"

# Admin menu: orders
menu_orders = "📦 订单"

# Menu: transactions
menu_transactions = "💳 交易清单"

# Menu: edit credit
menu_edit_credit = "💰 创建交易"

# Admin menu: go to user mode
menu_user_mode = "👤 切换到客户模式"

# Admin menu: add product
menu_add_product = "✨ 新产品"

# Admin menu: delete product
menu_delete_product = "❌ 删除产品"

# Menu: cancel
menu_cancel = "🔙 取消"

# Menu: skip
menu_skip = "⏭ 跳过"

# Menu: done
menu_done = "✅️ 已完成"

# Menu: pay invoice
menu_pay = "💳 支付"

# Menu: complete
menu_complete = "✅ 完成"

# Menu: refund
menu_refund = "✴️ 退还"

# Menu: stop
menu_stop = "🛑 停止"

# Menu: add to cart
menu_add_to_cart = "➕ 添加"

# Menu: remove from cart
menu_remove_from_cart = "➖ 去除"

# Menu: help menu
menu_help = "❓ 帮助 / 支持"

# Menu: guide
menu_guide = "📖 指南"

# Menu: next page
menu_next = "▶️ 下一个"

# Menu: previous page
menu_previous = "◀️ 上一个"

# Menu: contact the shopkeeper
menu_contact_shopkeeper = "👨‍💼 联系商店"

# Menu: generate transactions .csv file
menu_csv = "📄 .csv"

# Menu: edit admins list
menu_edit_admins = "🏵 编辑经理"

# Menu: language
menu_language = "🇨🇳 语言"

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
text_not_processed = "待定"

# Text: completed order
text_completed = "已完成"

# Text: refunded order
text_refunded = "已退还"

# Text: product not for sale
text_not_for_sale = "不出售"

# Add product: name?
ask_product_name = "产品名称应为?"

# Add product: description?
ask_product_description = "产品说明应该是什么?"

# Add product: price?
ask_product_price = "产品价格应该是多少?\n" \
                    "输入 <code>X</code> 如果不希望该产品被出售"

# Add product: image?
ask_product_image = "🖼 您希望产品具有什么图片？\n" \
                    "\n" \
                    "<i>发送照片，或跳过此阶段不添加任何图像。</i>"

# Order product: notes?
ask_order_notes = "您想在订单上留下笔记吗？\n" \
                  "💼 这将对商店经理可见。\n" \
                  "\n" \
                  "<i>发送包含您要离开的便笺的消息，或按此下面的“跳过”按钮" \
                  " 将不留任何东西.</i>"

# Refund product: reason?
ask_refund_reason = " 为此退款附上原因。\n" \
                    "👤 会对客户可见."

# Edit credit: notes?
ask_transaction_notes = " 在此交易中附加注释.\n" \
                        "👤 计入之后会向客户可见 / debiting" \
                        " 并发送给交易日志中的💼经理."

# Edit credit: amount?
ask_credit = "您想如何更改客户的信用额度?\n" \
             "\n" \
             "<i>发送包含金额的消息.\n" \
             "使用标志 </i><code>+</code><i> 向客户的帐户添加信用额," \
             "使用标志  </i><code>-</code><i> 去减掉它.</i>"

# Header for the edit admin message
admin_properties = "<b>{name}的权限:</b>"

# Edit admin: can edit products?
prop_edit_products = "编辑产品"

# Edit admin: can receive orders?
prop_receive_orders = "接收订单"

# Edit admin: can create transactions?
prop_create_transactions = "管理交易"

# Edit admin: show on help message?
prop_display_on_help = "向客户展示"

# Thread has started downloading an image and might be unresponsive
downloading_image = "我正在下载您的照片\n" \
                    "这可能需要一段时间...请耐心等待\n" \
                    "下载时，我将无法回复您。"

# Edit product: current value
edit_current_value = "当前值为:\n" \
                     "<pre>{value}</pre>\n" \
                     "\n" \
                     "<i>按此消息下方的“跳过”按钮以保持相同的值.</i>"

# Payment: cash payment info
payment_cash = "您可以在商店的实际位置以现金支付.\n" \
               "在结帐时付款，并将此ID交给经理:\n" \
               "<b>{user_cash_id}</b>"

# Payment: invoice amount
payment_cc_amount = "您想添加多少钱到钱包里？\n" \
                    "\n" \
                    "<i>使用下面的按钮选择一个金额，或使用键盘手动输入</i>"

# Payment: add funds invoice title
payment_invoice_title = "充值余额"

# Payment: add funds invoice description
payment_invoice_description = "支付此发票会将{amount} 添加到您的钱包中."

# Payment: label of the labeled price on the invoice
payment_invoice_label = "重新加载"

# Payment: label of the labeled price on the invoice
payment_invoice_fee_label = "交易费"

# Notification: order has been placed
notification_order_placed = "新订单是:\n" \
                            "\n" \
                            "{order}"

# Notification: order has been completed
notification_order_completed = "您的订单已完成\n" \
                               "\n" \
                               "{order}"

# Notification: order has been refunded
notification_order_refunded = "您的订单已退款\n" \
                              "\n" \
                              "{order}"

# Notification: a manual transaction was applied
notification_transaction_created = "ℹ️  新交易已应用于您的钱包:\n" \
                                   "{transaction}"

# Refund reason
refund_reason = "退款原因:\n" \
                "{reason}"

# Info: informazioni sul bot
bot_info = '此机器人正在使用 <a href="https://github.com/Steffo99/greed">greed</a>,' \
           ' @Steffo框架下的Telegram支付系统,中文翻译由@zhihuiyuze完成' \
           ' <a href="https://github.com/Steffo99/greed/blob/master/LICENSE.txt">' \
           'Affero General Public License 3.0</a>.\n'

# Help: guide
help_msg = "greed的指南可在此地址获得(未翻译):\n" \
           "https://github.com/Steffo99/greed/wiki"

# Help: contact shopkeeper
contact_shopkeeper = "目前可提供帮助和支持的人员包括:\n" \
                     "{shopkeepers}\n" \
                     "<i>点击他们的姓名之一，以通过Telegranm与他们联系.</i>"

# Success: product has been added/edited to the database
success_product_edited = "✅ 产品已成功添加/修改"

# Success: product has been marked as deleted in the database
success_product_deleted = "✅ 该产品已成功删除!"

# Success: order has been created
success_order_created = "✅ 订单已成功发送!\n" \
                        "\n" \
                        "{order}"

# Success: order was marked as completed
success_order_completed = "✅ 您的订单 #{order_id} 已标记完成."

# Success: order was refunded successfully
success_order_refunded = "✴️ 订单 #{order_id} 已退款."

# Success: transaction was created successfully
success_transaction_created = "✅ 交易已成功创建!\n" \
                              "{transaction}"

# Error: message received not in a private chat
error_nonprivate_chat = "⚠️ 该机器人仅适用于私人聊天."

# Error: a message was sent in a chat, but no worker exists for that chat.
# Suggest the creation of a new worker with /start
error_no_worker_for_chat = "⚠️ 与机器人对话被中断.\n" \
                           "要重新启动它，请将 /start 命令发送给机器人"

# Error: add funds amount over max
error_payment_amount_over_max = "⚠️ 单笔交易中可以添加的最大金额为{max_amount}."

# Error: add funds amount under min
error_payment_amount_under_min = "⚠️ 单笔交易中可以添加的最小金额为{min_amount}."

# Error: the invoice has expired and can't be paid
error_invoice_expired = "⚠️ 该发票已过期，且已被取消。 如果您仍想添加资金，请使用添加" \
                        " 资金菜单选项."

# Error: a product with that name already exists
error_duplicate_name = "️⚠️ 具有相同名称的产品已经存在."

# Error: not enough credit to order
error_not_enough_credit = "⚠️ 您的信用额不足，无法下订单."

# Error: order has already been cleared
error_order_already_cleared = "⚠️  该订单已被处理."

# Error: no orders have been placed, so none can be shown
error_no_orders = "⚠️  您尚未下任何订单，因此无任何显示."

# Error: selected user does not exist
error_user_does_not_exist = "⚠️  所选用户不存在."

# Fatal: conversation raised an exception
fatal_conversation_exception = "☢️ 啊啊啊啊! 一个 <b>error</b> 阻止了此对话\n" \
                               "该错误已报告给机器人所有者，以便他可以修复它\n" \
                               "如果要重新开始对话，请发送 /start"

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
