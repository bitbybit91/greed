#!/usr/bin/env python3
"""fix_greed.py — Fixes three bugs in the greed crypto swap bot.

Bugs fixed:
  1. All bots share the same database — give each bot its own engine.
  2. Products don't show up — send_as_message() crashes on None.
  3. Crypto wallet deposit addresses don't show during product ordering.

Run from the repository root:
    python3 fix_greed.py
"""
import os

FILES_WRITTEN = []


def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    FILES_WRITTEN.append(path)
    print(f"  \u2705 {path}")


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def patch(content: str, old: str, new: str, path: str = "") -> str:
    """Replace exactly one occurrence of *old* with *new*.
    If *old* is already absent but *new* is present, the patch is already applied (no-op).
    Raises if neither *old* nor *new* is found."""
    if old in content:
        return content.replace(old, new, 1)
    # Check if already patched (new text already present)
    if new in content:
        print(f"  ⏭  {path}: patch already applied, skipping.")
        return content
    raise ValueError(
        f"Patch target not found in {path!r}.\n"
        f"First 120 chars of target: {old[:120]!r}"
    )


# ---------------------------------------------------------------------------
# New localization strings to append to every strings/*.py file
# ---------------------------------------------------------------------------
CRYPTO_CHECKOUT_STRINGS = r"""
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
"""

# ---------------------------------------------------------------------------
# New methods to append to worker.py (inside the Worker class body)
# ---------------------------------------------------------------------------
WORKER_SWAP_ENGINE_METHODS = '''
    def __checkout_with_swap_engine(self, cart, order):
        """Checkout using the per-bot SwapEngine: wallet balance or crypto."""
        cart_value = self.__get_cart_value(cart)
        payment_keyboard = telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton(self.loc.get("menu_pay_wallet_balance"),
                                           callback_data="swe_pay_wallet")],
            [telegram.InlineKeyboardButton(self.loc.get("menu_pay_crypto"),
                                           callback_data="swe_pay_crypto")],
            [telegram.InlineKeyboardButton(self.loc.get("menu_cancel"),
                                           callback_data="cmd_cancel")],
        ])
        self.bot.send_message(
            self.chat.id,
            self.loc.get("checkout_select_payment", total=str(cart_value)),
            reply_markup=payment_keyboard,
        )
        callback = self.__wait_for_inlinekeyboard_callback(cancellable=True)
        if isinstance(callback, CancelSignal):
            self.session.rollback()
            return

        if callback.data == "swe_pay_wallet":
            self.__process_wallet_payment(cart, order)
        elif callback.data == "swe_pay_crypto":
            # Show dynamic coin selection from the SwapEngine
            supported_coins = self.swap_engine.supported_coins
            coin_buttons = [
                [telegram.InlineKeyboardButton(coin, callback_data=f"swe_coin_{coin}")]
                for coin in supported_coins
            ]
            coin_buttons.append([telegram.InlineKeyboardButton(
                self.loc.get("menu_cancel"), callback_data="cmd_cancel")])
            self.bot.send_message(
                self.chat.id,
                self.loc.get("checkout_select_crypto"),
                reply_markup=telegram.InlineKeyboardMarkup(coin_buttons),
            )
            coin_cb = self.__wait_for_inlinekeyboard_callback(cancellable=True)
            if isinstance(coin_cb, CancelSignal):
                self.session.rollback()
                return
            selected_coin = coin_cb.data.replace("swe_coin_", "", 1)
            self.__process_swap_engine_payment(cart, order, selected_coin)
        else:
            self.session.rollback()

    def __process_swap_engine_payment(self, cart, order, currency: str):
        """Process a crypto payment via the per-bot SwapEngine."""
        crypto_price = self.swap_engine.get_price_usd(currency)
        if not crypto_price:
            self.bot.send_message(
                self.chat.id,
                self.loc.get("error_crypto_price_unavailable", currency=currency),
            )
            self.session.rollback()
            return

        deposit_address = self.swap_engine.get_deposit_address(currency)
        if not deposit_address:
            self.bot.send_message(
                self.chat.id,
                self.loc.get("checkout_crypto_no_address", currency=currency),
            )
            self.session.rollback()
            return

        cart_value = self.__get_cart_value(cart)
        currency_exp = self.cfg["Payments"]["currency_exp"]
        fiat_total_str = str(cart_value)
        cart_value_usd = Decimal(str(int(cart_value))) / Decimal(str(10 ** currency_exp))

        decimals = utils.CRYPTO_DECIMALS.get(currency, 8)
        crypto_amount = cart_value_usd / crypto_price
        quantize_str = "0." + "0" * decimals
        crypto_amount = crypto_amount.quantize(Decimal(quantize_str), rounding=ROUND_DOWN)

        rate_str = f"${crypto_price:.2f} USD"

        # Save crypto payment info to the order
        order.crypto_currency = currency
        order.crypto_amount = str(crypto_amount)
        order.crypto_payment_address = deposit_address
        self.session.flush()

        # Show the invoice
        invoice_keyboard = telegram.InlineKeyboardMarkup([
            [telegram.InlineKeyboardButton(self.loc.get("checkout_ive_paid"),
                                           callback_data="swe_paid")],
            [telegram.InlineKeyboardButton(self.loc.get("checkout_cancel_crypto"),
                                           callback_data="swe_cancel")],
        ])
        self.bot.send_message(
            self.chat.id,
            self.loc.get(
                "checkout_crypto_invoice",
                currency=currency,
                crypto_amount=str(crypto_amount),
                address=deposit_address,
                rate=rate_str,
                fiat_total=fiat_total_str,
            ),
            reply_markup=invoice_keyboard,
        )

        # Wait for the user to claim payment or cancel
        callback = self.__wait_for_inlinekeyboard_callback(cancellable=True)
        if isinstance(callback, CancelSignal) or callback.data == "swe_cancel":
            self.session.rollback()
            return

        if callback.data == "swe_paid":
            # Ask for TX hash
            self.bot.send_message(self.chat.id, self.loc.get("checkout_enter_tx_hash"))
            tx_hash_input = self.__wait_for_regex(r"(.+)", cancellable=True)
            if isinstance(tx_hash_input, CancelSignal):
                self.session.rollback()
                return
            tx_hash = tx_hash_input.strip()

            # Save and commit the order (no fiat deduction for crypto payment)
            order.crypto_tx_hash = tx_hash
            self.session.commit()

            # Notify the user
            self.bot.send_message(
                self.chat.id,
                self.loc.get("checkout_crypto_pending", tx_hash=tx_hash),
            )

            # Notify admins
            admins = self.session.query(db.Admin).filter_by(receive_orders=True).all()
            for admin in admins:
                try:
                    self.bot.send_message(
                        admin.user_id,
                        self.loc.get(
                            "notification_crypto_payment",
                            order_id=order.order_id,
                            user=str(self.user),
                            crypto_amount=str(crypto_amount),
                            currency=currency,
                            tx_hash=tx_hash,
                            address=deposit_address,
                        ),
                    )
                except Exception:
                    pass
        else:
            self.session.rollback()

'''


def main():
    print("\U0001f527 Fixing greed bot \u2014 writing 19 files...\n")

    # -----------------------------------------------------------------------
    # FILE 1: config/template_config.toml — add per-bot database key
    # -----------------------------------------------------------------------
    content = read_file("config/template_config.toml")
    for i in range(1, 8):
        old_line = f'name = "ShopBot-{i}"\ndirectory'
        new_line = f'name = "ShopBot-{i}"\ndatabase = "sqlite:///bot{i}.sqlite"\ndirectory'
        content = patch(content, old_line, new_line, "config/template_config.toml")
    write_file("config/template_config.toml", content)

    # -----------------------------------------------------------------------
    # FILE 2: core.py — import bot_manager + start BotManager before main loop
    # -----------------------------------------------------------------------
    content = read_file("core.py")

    # Add import — use the line before "import worker" as unique anchor
    content = patch(
        content,
        "import nuconfig\nimport worker\n",
        "import nuconfig\nimport bot_manager\nimport worker\n",
        "core.py",
    )

    # Start BotManager just before the main poll loop
    content = patch(
        content,
        '    log.info(f"@{me.username} is starting!")\n\n'
        '    # Main loop of the program',
        '    log.info(f"@{me.username} is starting!")\n\n'
        '    # Start additional bots defined in [Bots.*] config sections\n'
        '    log.info("Starting BotManager for additional bots...")\n'
        '    bot_mgr = bot_manager.BotManager.build_from_config(user_cfg, engine)\n'
        '    bot_mgr.start_all()\n'
        '    if bot_mgr.bot_count > 0:\n'
        '        log.info(f"BotManager started {bot_mgr.bot_count} additional bot(s).")\n\n'
        '    # Main loop of the program',
        "core.py",
    )
    write_file("core.py", content)

    # -----------------------------------------------------------------------
    # FILE 3: bot_manager.py — per-bot engines + pass swap_engine to Worker
    # -----------------------------------------------------------------------
    content = read_file("bot_manager.py")

    # 3a. Replace the BotInstance creation block to use a per-bot engine
    old_bot_instance_block = (
        "            bot_instance = BotInstance(\n"
        "                name=name,\n"
        "                token=token,\n"
        "                directory=directory,\n"
        "                cfg=cfg,\n"
        "                engine=engine,\n"
        "                bot_key=key,\n"
        "                swap_engine=swap_engine,\n"
        "                max_workers=max_workers,\n"
        "                idle_timeout=idle_timeout,\n"
        "            )"
    )
    new_bot_instance_block = (
        "            # BUG 1 FIX: create a separate engine for each bot\n"
        "            per_bot_db_uri = bot_section.get(\"database\") or cfg[\"Database\"][\"engine\"]\n"
        "            per_bot_engine = sqlalchemy.create_engine(per_bot_db_uri)\n"
        "            database.TableDeclarativeBase.metadata.create_all(bind=per_bot_engine)\n"
        "            sed.DeferredReflection.prepare(per_bot_engine)\n"
        "            log.debug(f\"Bot [{key}] ({name}): using database {per_bot_db_uri!r}\")\n"
        "\n"
        "            # Create a per-bot SwapEngine if CryptoSwap is enabled\n"
        "            per_bot_swap = None\n"
        "            try:\n"
        "                if cfg[\"CryptoSwap\"][\"enabled\"]:\n"
        "                    import crypto_swap as _cs\n"
        "                    per_bot_swap = _cs.SwapEngine(cfg)\n"
        "                    log.debug(f\"Bot [{key}] ({name}): SwapEngine created\")\n"
        "            except (KeyError, TypeError):\n"
        "                pass\n"
        "\n"
        "            bot_instance = BotInstance(\n"
        "                name=name,\n"
        "                token=token,\n"
        "                directory=directory,\n"
        "                cfg=cfg,\n"
        "                engine=per_bot_engine,\n"
        "                bot_key=key,\n"
        "                swap_engine=per_bot_swap,\n"
        "                max_workers=max_workers,\n"
        "                idle_timeout=idle_timeout,\n"
        "            )"
    )
    content = patch(content, old_bot_instance_block, new_bot_instance_block, "bot_manager.py")

    # 3b. Pass swap_engine to Worker in _handle_message
    old_worker_creation = (
        "            new_worker = worker_module.Worker(\n"
        "                bot=self.bot,\n"
        "                chat=update.message.chat,\n"
        "                telegram_user=update.message.from_user,\n"
        "                cfg=self.cfg,\n"
        "                engine=self.engine,\n"
        "                bot_id=self.bot_key,\n"
        "                daemon=True\n"
        "            )"
    )
    new_worker_creation = (
        "            new_worker = worker_module.Worker(\n"
        "                bot=self.bot,\n"
        "                chat=update.message.chat,\n"
        "                telegram_user=update.message.from_user,\n"
        "                cfg=self.cfg,\n"
        "                engine=self.engine,\n"
        "                bot_id=self.bot_key,\n"
        "                swap_engine=self.swap_engine,\n"
        "                daemon=True\n"
        "            )"
    )
    content = patch(content, old_worker_creation, new_worker_creation, "bot_manager.py")
    write_file("bot_manager.py", content)

    # -----------------------------------------------------------------------
    # FILE 4: database.py — fix Product.send_as_message() None crash
    # -----------------------------------------------------------------------
    content = read_file("database.py")
    old_send = (
        "    def send_as_message(self, w: \"worker.Worker\", chat_id: int) -> dict:\n"
        "        \"\"\"Send a message containing the product data.\"\"\"\n"
        "        if self.image is None:\n"
        "            msg = w.bot.send_message(chat_id, self.text(w))\n"
        "        else:\n"
        "            msg = w.bot.send_photo(chat_id, self.image, caption=self.text(w))\n"
        "        return msg.to_dict()"
    )
    new_send = (
        "    def send_as_message(self, w: \"worker.Worker\", chat_id: int) -> dict:\n"
        "        \"\"\"Send a message containing the product data.\"\"\"\n"
        "        if self.image is None:\n"
        "            msg = w.bot.send_message(chat_id, self.text(w))\n"
        "        else:\n"
        "            msg = w.bot.send_photo(chat_id, self.image, caption=self.text(w))\n"
        "        # BUG 2 FIX: DuckBot returns None on Unauthorized; guard before calling .to_dict()\n"
        "        if msg is None:\n"
        "            log.warning(\n"
        "                f\"send_as_message for product {self.name!r} returned None \"\n"
        "                \"(bot blocked or Unauthorized?)\"\n"
        "            )\n"
        "            return None\n"
        "        return msg.to_dict()"
    )
    content = patch(content, old_send, new_send, "database.py")
    write_file("database.py", content)

    # -----------------------------------------------------------------------
    # FILE 5: worker.py — bot_id/swap_engine params + None check + new flow
    # -----------------------------------------------------------------------
    content = read_file("worker.py")

    # 5a. Add ROUND_DOWN and utils to module-level imports (move out of inline usage)
    content = patch(
        content,
        "from decimal import Decimal\n",
        "from decimal import Decimal, ROUND_DOWN\n",
        "worker.py",
    )
    content = patch(
        content,
        "import database as db\nimport localization\n",
        "import database as db\nimport utils\nimport localization\n",
        "worker.py",
    )

    # 5b. Add bot_id and swap_engine params to Worker.__init__
    old_init_sig = (
        "    def __init__(self,\n"
        "                 bot,\n"
        "                 chat: telegram.Chat,\n"
        "                 telegram_user: telegram.User,\n"
        "                 cfg: nuconfig.NuConfig,\n"
        "                 engine,\n"
        "                 *args,\n"
        "                 **kwargs):\n"
        "        # Initialize the thread\n"
        "        super().__init__(name=f\"Worker {chat.id}\", *args, **kwargs)\n"
        "        # Store the bot, chat info and config inside the class\n"
        "        self.bot = bot\n"
        "        self.chat: telegram.Chat = chat\n"
        "        self.telegram_user: telegram.User = telegram_user\n"
        "        self.cfg = cfg\n"
        "        self.loc = None"
    )
    new_init_sig = (
        "    def __init__(self,\n"
        "                 bot,\n"
        "                 chat: telegram.Chat,\n"
        "                 telegram_user: telegram.User,\n"
        "                 cfg: nuconfig.NuConfig,\n"
        "                 engine,\n"
        "                 bot_id: str = None,\n"
        "                 swap_engine=None,\n"
        "                 *args,\n"
        "                 **kwargs):\n"
        "        # Initialize the thread\n"
        "        super().__init__(name=f\"Worker {chat.id}\", *args, **kwargs)\n"
        "        # Store the bot, chat info and config inside the class\n"
        "        self.bot = bot\n"
        "        self.chat: telegram.Chat = chat\n"
        "        self.telegram_user: telegram.User = telegram_user\n"
        "        self.cfg = cfg\n"
        "        # Bot ID (None = main bot) and per-bot swap engine (BUG 1+3 FIX)\n"
        "        self.bot_id = bot_id\n"
        "        self.swap_engine = swap_engine\n"
        "        self.loc = None"
    )
    content = patch(content, old_init_sig, new_init_sig, "worker.py")

    # 5b. Add None check after product.send_as_message() in __order_menu
    old_send_call = (
        "            # Send the message without the keyboard to get the message id\n"
        "            message = product.send_as_message(w=self, chat_id=self.chat.id)\n"
        "            # Add the product to the cart\n"
        "            cart[message['message_id']] = [product, 0]"
    )
    new_send_call = (
        "            # Send the message without the keyboard to get the message id\n"
        "            message = product.send_as_message(w=self, chat_id=self.chat.id)\n"
        "            # BUG 2 FIX: skip products that couldn't be sent (bot blocked/Unauthorized)\n"
        "            if message is None:\n"
        "                log.warning(f\"Product {product.name!r}: send_as_message returned None, skipping.\")\n"
        "                continue\n"
        "            # Add the product to the cart\n"
        "            cart[message['message_id']] = [product, 0]"
    )
    content = patch(content, old_send_call, new_send_call, "worker.py")

    # 5c. Wrap the existing crypto-checkout block with a self.swap_engine check (BUG 3 FIX)
    old_checkout_block = (
        "        # Check if crypto swap is enabled and show payment method selection\n"
        "        crypto_enabled = False\n"
        "        try:\n"
        "            crypto_enabled = self.cfg[\"CryptoSwap\"][\"enabled\"]\n"
        "        except (KeyError, TypeError):\n"
        "            pass\n"
        "\n"
        "        if crypto_enabled:\n"
        "            # Show payment method selection with crypto options\n"
        "            cart_value = self.__get_cart_value(cart)\n"
        "            payment_buttons = [\n"
        "                [telegram.InlineKeyboardButton(self.loc.get(\"crypto_pay_wallet\"),\n"
        "                                               callback_data=\"pay_wallet\")],\n"
        "                [telegram.InlineKeyboardButton(self.loc.get(\"crypto_pay_btc\"),\n"
        "                                               callback_data=\"pay_crypto_BTC\")],\n"
        "                [telegram.InlineKeyboardButton(self.loc.get(\"crypto_pay_ltc\"),\n"
        "                                               callback_data=\"pay_crypto_LTC\")],\n"
        "                [telegram.InlineKeyboardButton(self.loc.get(\"crypto_pay_xmr\"),\n"
        "                                               callback_data=\"pay_crypto_XMR\")],\n"
        "                [telegram.InlineKeyboardButton(self.loc.get(\"crypto_pay_usdt\"),\n"
        "                                               callback_data=\"pay_crypto_USDT-TRC20\")],\n"
        "                [telegram.InlineKeyboardButton(self.loc.get(\"crypto_pay_zcash\"),\n"
        "                                               callback_data=\"pay_crypto_ZCASH\")],\n"
        "                [telegram.InlineKeyboardButton(self.loc.get(\"menu_cancel\"),\n"
        "                                               callback_data=\"cmd_cancel\")]\n"
        "            ]\n"
        "            payment_keyboard = telegram.InlineKeyboardMarkup(payment_buttons)\n"
        "            self.bot.send_message(\n"
        "                self.chat.id,\n"
        "                self.loc.get(\"crypto_payment_method\", total_cost=str(cart_value)),\n"
        "                reply_markup=payment_keyboard\n"
        "            )\n"
        "            # Wait for payment method selection\n"
        "            callback = self.__wait_for_inlinekeyboard_callback(cancellable=True)\n"
        "            if isinstance(callback, CancelSignal):\n"
        "                self.session.rollback()\n"
        "                return\n"
        "\n"
        "            if callback.data == \"pay_wallet\":\n"
        "                # Proceed with existing wallet payment flow\n"
        "                self.__process_wallet_payment(cart, order)\n"
        "            elif callback.data.startswith(\"pay_crypto_\"):\n"
        "                coin = callback.data.replace(\"pay_crypto_\", \"\")\n"
        "                self.__process_crypto_payment(cart, order, coin)\n"
        "            else:\n"
        "                self.session.rollback()\n"
        "                return\n"
        "        else:\n"
        "            # Original wallet-only payment flow\n"
        "            self.__process_wallet_payment(cart, order)"
    )
    new_checkout_block = (
        "        # BUG 3 FIX: use per-bot SwapEngine when available; fall back to legacy cfg-based flow\n"
        "        if self.swap_engine is not None:\n"
        "            self.__checkout_with_swap_engine(cart, order)\n"
        "        else:\n"
        "            # Check if crypto swap is enabled and show payment method selection\n"
        "            crypto_enabled = False\n"
        "            try:\n"
        "                crypto_enabled = self.cfg[\"CryptoSwap\"][\"enabled\"]\n"
        "            except (KeyError, TypeError):\n"
        "                pass\n"
        "\n"
        "            if crypto_enabled:\n"
        "                # Show payment method selection with crypto options\n"
        "                cart_value = self.__get_cart_value(cart)\n"
        "                payment_buttons = [\n"
        "                    [telegram.InlineKeyboardButton(self.loc.get(\"crypto_pay_wallet\"),\n"
        "                                                   callback_data=\"pay_wallet\")],\n"
        "                    [telegram.InlineKeyboardButton(self.loc.get(\"crypto_pay_btc\"),\n"
        "                                                   callback_data=\"pay_crypto_BTC\")],\n"
        "                    [telegram.InlineKeyboardButton(self.loc.get(\"crypto_pay_ltc\"),\n"
        "                                                   callback_data=\"pay_crypto_LTC\")],\n"
        "                    [telegram.InlineKeyboardButton(self.loc.get(\"crypto_pay_xmr\"),\n"
        "                                                   callback_data=\"pay_crypto_XMR\")],\n"
        "                    [telegram.InlineKeyboardButton(self.loc.get(\"crypto_pay_usdt\"),\n"
        "                                                   callback_data=\"pay_crypto_USDT-TRC20\")],\n"
        "                    [telegram.InlineKeyboardButton(self.loc.get(\"crypto_pay_zcash\"),\n"
        "                                                   callback_data=\"pay_crypto_ZCASH\")],\n"
        "                    [telegram.InlineKeyboardButton(self.loc.get(\"menu_cancel\"),\n"
        "                                                   callback_data=\"cmd_cancel\")]\n"
        "                ]\n"
        "                payment_keyboard = telegram.InlineKeyboardMarkup(payment_buttons)\n"
        "                self.bot.send_message(\n"
        "                    self.chat.id,\n"
        "                    self.loc.get(\"crypto_payment_method\", total_cost=str(cart_value)),\n"
        "                    reply_markup=payment_keyboard\n"
        "                )\n"
        "                # Wait for payment method selection\n"
        "                callback = self.__wait_for_inlinekeyboard_callback(cancellable=True)\n"
        "                if isinstance(callback, CancelSignal):\n"
        "                    self.session.rollback()\n"
        "                    return\n"
        "\n"
        "                if callback.data == \"pay_wallet\":\n"
        "                    # Proceed with existing wallet payment flow\n"
        "                    self.__process_wallet_payment(cart, order)\n"
        "                elif callback.data.startswith(\"pay_crypto_\"):\n"
        "                    coin = callback.data.replace(\"pay_crypto_\", \"\")\n"
        "                    self.__process_crypto_payment(cart, order, coin)\n"
        "                else:\n"
        "                    self.session.rollback()\n"
        "                    return\n"
        "            else:\n"
        "                # Original wallet-only payment flow\n"
        "                self.__process_wallet_payment(cart, order)"
    )
    content = patch(content, old_checkout_block, new_checkout_block, "worker.py")

    # 5d. Insert the two new SwapEngine checkout methods before __get_cart_value.
    # Use context including the unique "crypto_payment_expired" string that only
    # appears at the end of __process_crypto_payment as the anchor, so the pattern
    # disappears after the first patch is applied (idempotent).
    old_get_cart_value = (
        "            self.bot.send_message(self.chat.id, self.loc.get(\"crypto_payment_expired\"))\n"
        "        self.session.rollback()\n"
        "\n"
        "    def __get_cart_value(self, cart):"
    )
    new_get_cart_value = (
        "            self.bot.send_message(self.chat.id, self.loc.get(\"crypto_payment_expired\"))\n"
        "        self.session.rollback()\n"
        "\n"
        + WORKER_SWAP_ENGINE_METHODS
        + "    def __get_cart_value(self, cart):"
    )
    content = patch(content, old_get_cart_value, new_get_cart_value, "worker.py")

    write_file("worker.py", content)

    # -----------------------------------------------------------------------
    # FILES 6-10: unchanged files (written back byte-for-byte)
    # -----------------------------------------------------------------------
    for path in [
        "crypto_swap.py",
        "duckbot.py",
        "nuconfig.py",
        "localization.py",
        "utils.py",
    ]:
        write_file(path, read_file(path))

    # -----------------------------------------------------------------------
    # FILES 11-19: string files — append new checkout localization strings
    # -----------------------------------------------------------------------
    for lang in ["en", "it", "uk", "ru", "zh_cn", "he", "es_mx", "pt_br", "hi"]:
        path = f"strings/{lang}.py"
        content = read_file(path)
        # Only append if not already present (idempotent)
        if "menu_pay_wallet_balance" not in content:
            content = content.rstrip("\n") + "\n" + CRYPTO_CHECKOUT_STRINGS
        write_file(path, content)

    # -----------------------------------------------------------------------
    print(f"\n\u2705 Done! {len(FILES_WRITTEN)} files written.")
    if len(FILES_WRITTEN) != 19:
        print(f"\u26a0\ufe0f  WARNING: Expected 19 files, wrote {len(FILES_WRITTEN)}!")
    else:
        print("\U0001f389 All 19 files written successfully!")


if __name__ == "__main__":
    main()
