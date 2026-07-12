from telegram import Update
from telegram.ext import ContextTypes

from db.users import get_user
from utils.decorators import registered_only
from utils.formatters import format_wallet
from user_bot.keyboards import wallet_keyboard


@registered_only
async def show_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = await get_user(update.effective_user.id)
    await update.effective_message.reply_text(
        format_wallet(user["wallet_balance"]), reply_markup=wallet_keyboard()
    )
