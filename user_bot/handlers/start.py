from telegram import Update
from telegram.ext import ContextTypes

from db.users import upsert_user
from user_bot import texts
from user_bot.keyboards import MAIN_MENU


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await upsert_user(user.id, user.username, user.first_name)
    await update.effective_message.reply_text(texts.WELCOME, reply_markup=MAIN_MENU)
