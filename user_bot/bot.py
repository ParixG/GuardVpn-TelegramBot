from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

import config
from user_bot import texts
from user_bot.handlers.buy import build_buy_conversation_handler
from user_bot.handlers.start import start
from user_bot.handlers.subscriptions import my_subscriptions
from user_bot.handlers.topup import build_topup_conversation_handler
from user_bot.handlers.wallet import show_wallet
from utils.telegram import btn_regex


def build_user_app() -> Application:
    app = Application.builder().token(config.USER_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(build_buy_conversation_handler())
    app.add_handler(build_topup_conversation_handler())
    app.add_handler(MessageHandler(filters.Regex(btn_regex(texts.BTN_SUBS)), my_subscriptions))
    app.add_handler(MessageHandler(filters.Regex(btn_regex(texts.BTN_WALLET)), show_wallet))

    return app
