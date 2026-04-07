# Strings / localization file for greed
# Can be edited, but DON'T REMOVE THE REPLACEMENT FIELDS (words surrounded by {curly braces})

# Currency symbol
currency_symbol = "R$"

# Positioning of the currency symbol
currency_format_string = "{symbol} {value}"

# Quantity of a product in stock
in_stock_format_string = "{quantity} disponível"

# Copies of a product in cart
in_cart_format_string = "{quantity} no carrinho"

# Product information
product_format_string = "<b>{name}</b>\n" \
                        "{description}\n" \
                        "{price}\n" \
                        "<b>{cart}</b>"

# Order number, displayed in the order info
order_number = "Pedido #{id}"

# Order info string, shown to the admins
order_format_string = "por  {user}\n" \
                      "Criado em {date}\n" \
                      "\n" \
                      "{items}\n" \
                      "TOTAL: <b>{value}</b>\n" \
                      "\n" \
                      "Cliente notas: {notes}\n"

# Order info string, shown to the user
user_order_format_string = "{status_emoji} <b>Pedido {status_text}</b>\n" \
                           "{items}\n" \
                           "TOTAL: <b>{value}</b>\n" \
                           "\n" \
                           "Notas: {notes}\n"

# Transaction page is loading
loading_transactions = "<i>Carregando transações...\n" \
                       "Por favor aguarde alguns segundos.</i>"

# Transactions page
transactions_page = "Página <b>{page}</b>:\n" \
                    "\n" \
                    "{transactions}"

# transactions.csv caption
csv_caption = "Um arquivo  📄 .csv contem todas transações guardadas no banco de dados do bot foi gerado.\n" \
              "Você pode abrir um arquivo com outros programas, como LibreOffice Calc, Excel para processar" \
              " os dados."

# Conversation: the start command was sent and the bot should welcome the user
conversation_after_start = "Olá!\n" \
                           "Bem Vindo ao greed!\n" \
                           "Isto é uma versão  🅱️ <b>Beta</b> do software.\n" \
                           "É completamente usavel, mas pode haver bugs ainda presente.\n" \
                           "Se você encontrar algum, por favor, relate-o em https://github.com/Steffo99/greed/issues."

# Conversation: to send an inline keyboard you need to send a message with it
conversation_open_user_menu = "O que você gostaria de fazer?\n" \
                              "💰 Você tem <b>{credit}</b> na sua carteira.\n" \
                              "\n" \
                              "<i>Pressione uma tecla no teclado abaixo para selecionar uma operação.\n" \
                              "Se o teclado não abriu, você pode abri-lo pressionando o botão com quatro  quadrados" \
                              " pequenos na barra de menssagem.</i>"

# Conversation: like above, but for administrators
conversation_open_admin_menu = "Você é um  💼 <b>Gerente</b> desta loja!\n" \
                               "O que você gostaria de fazer?\n" \
                               "\n" \
                               "<i>Pressione uma tecla no teclado abaixo para selecionar uma operação.\n" \
                               "Se o teclado não abriu, você pode abri-lo pressionando o botão com quatro  quadrados" \
                               " pequenos na barra de menssagem.</i>"

# Conversation: select a payment method
conversation_payment_method = "Como você deseja adicionar fundos à sua carteira?"

# Conversation: select a product to edit
conversation_admin_select_product = "✏️ Qual produto você deseja editar?"

# Conversation: select a product to delete
conversation_admin_select_product_to_delete = "❌ Qual produto você deseja apagar?"

# Conversation: select a user to edit
conversation_admin_select_user = "Selecione um usuario pra editar."

# Conversation: click below to pay for the purchase
conversation_cart_actions = "<i>Adicione produtos ao carrinho, rolando para cima e pressionando o botão Adicionar abaixo" \
                            " os produtos que você deseja adicionar ao carrinho. Quando terminar, volte para esta mensagem e" \
                            " pressione o botão Concluído abaixo.</i>"

# Conversation: confirm the cart contents
conversation_confirm_cart = "🛒 Seu carrinho contém os seguintes produtos:\n" \
                            "{product_list}" \
                            "Total: <b>{total_cost}</b>\n" \
                            "\n" \
                            "<i>Se quiser continuar, pressione o botão Concluído abaixo desta mensagem.\n" \
                            "Para cancelar, pressione o botão Cancelar.</i>"

# Live orders mode: start
conversation_live_orders_start = "Você esta no modo <b>Live Pedidos</b> \n" \
                                 "Todos os novos pedidos feitos pelos clientes aparecerão em tempo real neste chat, e você" \
                                 " poderá marcá-los como ✅ Concluídos" \
                                 " ou ✴️ Reembolsar o crédito ao cliente."

# Live orders mode: stop receiving messages
conversation_live_orders_stop = "<i>Pressione o botão há abaixo desta mensagem para parar o" \
                                " feed.</i>"

# Conversation: help menu has been opened
conversation_open_help_menu = "Que tipo de ajuda você precisa?"

# Conversation: confirm promotion to admin
conversation_confirm_admin_promotion = "Tem certeza de que deseja promover este usuário a 💼 Gerente?\n" \
                                       "É uma açao irreversivel!"

# Conversation: language select menu header
conversation_language_select = "Seleciona uma linguagem:"

# Conversation: switching to user mode
conversation_switch_to_user_mode = " Você está mudando para o modo 👤 Cliente.\n" \
                                   "Se quiser voltar ao menu 💼 Manager, reinicie a conversa com / start."

# Notification: the conversation has expired
conversation_expired = "🕐  Faz um tempo que não recebo nenhuma mensagem, então fechei a conversa para salvar" \
                       " recursos.\n" \
                       "Se você deseja iniciar um novo, envie um novo comando / start."

# User menu: order
menu_order = "🛒 Pedido de Produtos"

# User menu: order status
menu_order_status = "🛍 Meus Pedidos"

# User menu: add credit
menu_add_credit = "💵 Adicionar fundos"

# User menu: bot info
menu_bot_info = "ℹ️ Bot info"

# User menu: cash
menu_cash = "💵 Com dinheiro"

# User menu: credit card
menu_credit_card = "💳 Com Cartão de Crédito"

# Admin menu: products
menu_products = "📝️ Produtos"

# Admin menu: orders
menu_orders = "📦 Pedidos"

# Menu: transactions
menu_transactions = "💳 Lista de Transações"

# Menu: edit credit
menu_edit_credit = "💰 Criar transação"

# Admin menu: go to user mode
menu_user_mode = "👤 Mudar para o modo de cliente"

# Admin menu: add product
menu_add_product = "✨ Novo Produto"

# Admin menu: delete product
menu_delete_product = "❌ Apagar produto"

# Menu: cancel
menu_cancel = "🔙 Cancelar"

# Menu: skip
menu_skip = "⏭ Pular"

# Menu: done
menu_done = "✅️ Concluido"

# Menu: pay invoice
menu_pay = "💳 Pagar"

# Menu: complete
menu_complete = "✅ Complete"

# Menu: refund
menu_refund = "✴️ Devolver"

# Menu: stop
menu_stop = "🛑 Parar"

# Menu: add to cart
menu_add_to_cart = "➕ Add"

# Menu: remove from cart
menu_remove_from_cart = "➖ Remover"

# Menu: help menu
menu_help = "❓ Ajuda / Suporte"

# Menu: guide
menu_guide = "📖 Guia"

# Menu: next page
menu_next = "▶️ Proximo"

# Menu: previous page
menu_previous = "◀️ Anterior"

# Menu: contact the shopkeeper
menu_contact_shopkeeper = "👨‍💼 Contatar a loja"

# Menu: generate transactions .csv file
menu_csv = "📄 .csv"

# Menu: edit admins list
menu_edit_admins = "🏵 Editar Gerentes"

# Menu: language
menu_language = "🇬🇧 Linguagem"

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
text_not_processed = "pendente"

# Text: completed order
text_completed = "completo"

# Text: refunded order
text_refunded = "devolvido"

# Text: product not for sale
text_not_for_sale = "Não está a venda"

# Add product: name?
ask_product_name = "Qual deve ser o nome do produto?"

# Add product: description?
ask_product_description = "Qual deve ser a descrição do produto?"

# Add product: price?
ask_product_price = "Qual deve ser o preço do produto?\n" \
                    "Entre <code>X</code> se ainda não quiser que o produto esteja à venda."

# Add product: image?
ask_product_image = "🖼 Que imagem você quer que o produto tenha?\n" \
                    "\n" \
                    "<i>Envie a foto ou ignore esta fase e não adicione nenhuma imagem.</i>"

# Order product: notes?
ask_order_notes = "Gostaria de deixar um recado junto com o pedido?\n" \
                  "💼 Ele ficará visível para os gerentes da loja.\n" \
                  "\n" \
                  "<i>Envie uma mensagem com a nota que deseja deixar ou pressione o botão Ignorar abaixo desta" \
                  " mensagem para não deixar nada.</i>"

# Refund product: reason?
ask_refund_reason = " Anexe um motivo para este reembolso.\n" \
                    "👤  Ele ficará visível para o cliente."

# Edit credit: notes?
ask_transaction_notes = " Anexe uma nota a esta transação.\n" \
                        "👤 Será visível para o cliente após o crédito / débito" \
                        " e para 💼 Gerentes no log de transações."

# Edit credit: amount?
ask_credit = "Como você deseja alterar o crédito do cliente?\n" \
             "\n" \
             "<i>Envie uma mensagem contendo o valor.\n" \
             "Use o sinal </i><code>+</code><i> para adicionar crédito à conta do cliente," \
             " e o sinal </i><code>-</code><i> para reduzir.</i>"

# Header for the edit admin message
admin_properties = "<b>Permissões de {name}:</b>"

# Edit admin: can edit products?
prop_edit_products = "Editar Produtos"

# Edit admin: can receive orders?
prop_receive_orders = "Orders Recebidas"

# Edit admin: can create transactions?
prop_create_transactions = "Gerenciar Transações"

# Edit admin: show on help message?
prop_display_on_help = "Mostrar ao Cliente"

# Thread has started downloading an image and might be unresponsive
downloading_image = "Estou baixando sua foto!\n" \
                    "Pode demorar um pouco ... Por favor, seja paciente!\n" \
                    "Não poderei responder durante o download."

# Edit product: current value
edit_current_value = "O valor atual é:\n" \
                     "<pre>{value}</pre>\n" \
                     "\n" \
                     "<i>Pressione o botão Ignorar abaixo desta mensagem para manter o mesmo valor.</i>"

# Payment: cash payment info
payment_cash = "Você pode pagar em dinheiro no local físico da loja.\n" \
               "Pague na finalização da compra e dê este id ao gerente:\n" \
               "<b>{user_cash_id}</b>"

# Payment: invoice amount
payment_cc_amount = "Quantos fundos você deseja adicionar à sua carteira?\n" \
                    "\n" \
                    "<i>Selecione um valor com os botões abaixo ou insira-o manualmente com o teclado normal</i>"

# Payment: add funds invoice title
payment_invoice_title = "Adicionando fundos"

# Payment: add funds invoice description
payment_invoice_description = "Pagando esta conta irá adicionar {amount} na sua carteira."

# Payment: label of the labeled price on the invoice
payment_invoice_label = "Recarregar"

# Payment: label of the labeled price on the invoice
payment_invoice_fee_label = "Taxa de Transação"

# Notification: order has been placed
notification_order_placed = "Um novo pedido foi feito:\n" \
                            "\n" \
                            "{order}"

# Notification: order has been completed
notification_order_completed = "Seu pedido foi completado!\n" \
                               "\n" \
                               "{order}"

# Notification: order has been refunded
notification_order_refunded = "Seu pedido foi reembolsado!\n" \
                              "\n" \
                              "{order}"

# Notification: a manual transaction was applied
notification_transaction_created = "ℹ️ Uma nova transação foi aplicada à sua carteira:\n" \
                                   "{transaction}"

# Refund reason
refund_reason = "Devolução razão:\n" \
                "{reason}"

# Info: informazioni sul bot
bot_info = 'Este bot esta usando <a href="https://github.com/Steffo99/greed">greed</a>,' \
           ' um framework criado por @Steffo para pagamentos no Telegram sob licença  ' \
           ' <a href="https://github.com/Steffo99/greed/blob/master/LICENSE.txt">' \
           'Affero General Public License 3.0</a>.\n'

# Help: guide
help_msg = "O guia de greed esta dispovivel no endereço:\n" \
           "https://github.com/Steffo99/greed/wiki"

# Help: contact shopkeeper
contact_shopkeeper = "Atualmente, a equipe disponível para prestar atendimento ao usuário é composta por:\n" \
                     "{shopkeepers}\n" \
                     "<i>Clique / Toque em um de seus nomes para contatá-los em um bate-papo do Telegram.</i>"

# Success: product has been added/edited to the database
success_product_edited = "✅ O produto foi adicionado / modificado com sucesso!"

# Success: product has been marked as deleted in the database
success_product_deleted = "✅ O produto foi excluído com sucesso!"

# Success: order has been created
success_order_created = "✅ O pedido foi enviado com sucesso!\n" \
                        "\n" \
                        "{order}"

# Success: order was marked as completed
success_order_completed = "✅ Voce marcou o pedido #{order_id} como completo."

# Success: order was refunded successfully
success_order_refunded = "✴️ Pedido #{order_id} foi reembolsado."

# Success: transaction was created successfully
success_transaction_created = "✅ A transação foi criada com sucesso!\n" \
                              "{transaction}"

# Error: message received not in a private chat
error_nonprivate_chat = "⚠️ Este bot funciona apenas em chats privados."

# Error: a message was sent in a chat, but no worker exists for that chat.
# Suggest the creation of a new worker with /start
error_no_worker_for_chat = "⚠️ A conversa com o bot foi interrompida.\n" \
                           "Para reiniciá-lo, envie o comando / start para o bot."

# Error: a message was sent in a chat, but the worker for that chat is not ready.
error_worker_not_ready = "🕒 A conversa com o bot está começando.\n" \
                         "Por favor, aguarde alguns instantes antes de enviar mais comandos!"

# Error: add funds amount over max
error_payment_amount_over_max = "⚠️ O valor máximo que pode ser adicionado em uma única transação é {max_amount}."

# Error: add funds amount under min
error_payment_amount_under_min = "⚠️ O valor mínimo que pode ser adicionado em uma única transação é {min_amount}."

# Error: the invoice has expired and can't be paid
error_invoice_expired = "⚠️ Esta fatura expirou e foi cancelada. Se você ainda deseja adicionar fundos, use o botão Adicionar" \
                        " opção de menu de fundos."

# Error: a product with that name already exists
error_duplicate_name = "️⚠️ Já existe um produto com o mesmo nome."

# Error: not enough credit to order
error_not_enough_credit = "⚠️ Você não tem crédito suficiente para fazer o pedido."

# Error: order has already been cleared
error_order_already_cleared = "⚠️ Este pedido já foi processado."

# Error: no orders have been placed, so none can be shown
error_no_orders = "⚠️ Você ainda não fez nenhum pedido, então não há nada para exibir."

# Error: selected user does not exist
error_user_does_not_exist = "⚠️  O usuário selecionado não existe."

# Fatal: conversation raised an exception
fatal_conversation_exception = "☢️ Oh no! Um <b>error</b> interrompeu esta conversa\n" \
                               "O erro foi relatado ao proprietário do bot para que ele pudesse corrigi-lo.\n" \
                               "Para reiniciar a conversa, envie o comando /start novamente."

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
