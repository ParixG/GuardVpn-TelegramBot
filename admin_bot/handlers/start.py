from telegram import Update
from telegram.ext import ContextTypes

from admin_bot import texts
from admin_bot.keyboards import MAIN_MENU
from utils.decorators import admin_only


@admin_only
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(texts.WELCOME, reply_markup=MAIN_MENU)
