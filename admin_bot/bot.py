from telegram.ext import Application, CommandHandler

import config
from admin_bot.handlers.add_balance import build_add_balance_conversation_handler
from admin_bot.handlers.add_user import build_add_user_conversation_handler
from admin_bot.handlers.check_user import build_check_user_conversation_handler
from admin_bot.handlers.plan_manager import build_plan_manager_conversation_handler
from admin_bot.handlers.start import start
from admin_bot.handlers.topup_review import register_topup_review_handlers
from admin_bot.handlers.user_manager import register_user_manager_handlers


def build_admin_app() -> Application:
    app = Application.builder().token(config.ADMIN_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(build_add_user_conversation_handler())
    app.add_handler(build_add_balance_conversation_handler())
    app.add_handler(build_check_user_conversation_handler())
    app.add_handler(build_plan_manager_conversation_handler())
    register_topup_review_handlers(app)
    register_user_manager_handlers(app)

    return app
