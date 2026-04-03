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
