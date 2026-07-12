from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from db.subscriptions import get_user_subscriptions
from guard.api import get_subscription
from utils.decorators import admin_only
from utils.formatters import format_subscription
from utils.telegram import btn_regex, normalize_digits
from admin_bot import texts
from admin_bot.handlers.start import start
from admin_bot.keyboards import CANCEL_MENU, MAIN_MENU

ASK_QUERY = 0


@admin_only
async def start_check_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_message.reply_text(texts.CU_ASK_QUERY, reply_markup=CANCEL_MENU)
    return ASK_QUERY


async def run_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.effective_message.text.strip()
    normalized = normalize_digits(query)

    if normalized.isdigit():
        rows = await get_user_subscriptions(int(normalized))
        if not rows:
            await update.effective_message.reply_text(
                texts.CU_NO_SUBSCRIPTIONS, reply_markup=MAIN_MENU
            )
            return ConversationHandler.END
        for row in rows:
            await _reply_subscription(update, row["guard_username"])
    else:
        await _reply_subscription(update, query)

    await update.effective_message.reply_text(texts.BACK_TO_MENU, reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def _reply_subscription(update: Update, guard_username: str) -> None:
    try:
        sub = await get_subscription(guard_username)
    except Exception:
        await update.effective_message.reply_text(
            texts.CU_GUARD_NOT_FOUND.format(guard_username=guard_username)
        )
        return
    await update.effective_message.reply_text(format_subscription(sub))


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_message.reply_text(
        texts.OPERATION_CANCELED, reply_markup=MAIN_MENU
    )
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await start(update, context)
    return ConversationHandler.END


def build_check_user_conversation_handler() -> ConversationHandler:
    cancel_handler = MessageHandler(filters.Regex(btn_regex(texts.BTN_CANCEL)), cancel)
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(btn_regex(texts.BTN_CHECK_USER)), start_check_user)
        ],
        states={
            ASK_QUERY: [cancel_handler, MessageHandler(filters.TEXT & ~filters.COMMAND, run_query)],
        },
        fallbacks=[cancel_handler, CommandHandler("start", restart)],
    )
