from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bridge import notify_user
from db.transactions import insert_transaction
from db.users import add_wallet, get_user
from utils.decorators import admin_only
from utils.formatters import format_price
from utils.telegram import btn_regex, normalize_digits
from admin_bot import texts
from admin_bot.handlers.start import start
from admin_bot.keyboards import CANCEL_MENU, MAIN_MENU, confirm_keyboard
from user_bot import texts as user_texts

ASK_TID, ASK_AMOUNT, CONFIRM = range(3)


@admin_only
async def start_add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["add_balance"] = {}
    await update.effective_message.reply_text(texts.AB_ASK_TID, reply_markup=CANCEL_MENU)
    return ASK_TID


async def enter_tid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = normalize_digits(update.effective_message.text)
    if not text.isdigit():
        await update.effective_message.reply_text(texts.INVALID_NUMBER)
        return ASK_TID

    user = await get_user(int(text))
    if not user:
        await update.effective_message.reply_text(texts.AB_USER_NOT_FOUND)
        return ASK_TID

    context.user_data["add_balance"] = {"telegram_id": int(text), "user": user}
    await update.effective_message.reply_text(texts.AB_ASK_AMOUNT)
    return ASK_AMOUNT


async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = normalize_digits(update.effective_message.text)
    if not text.isdigit() or int(text) <= 0:
        await update.effective_message.reply_text(texts.AB_INVALID_AMOUNT)
        return ASK_AMOUNT

    data = context.user_data["add_balance"]
    data["amount"] = int(text)
    user = data["user"]
    await update.effective_message.reply_text(
        texts.AB_CONFIRM.format(
            name=user.get("first_name", "-"),
            username=user.get("username") or "-",
            telegram_id=data["telegram_id"],
            amount=format_price(data["amount"]),
        ),
        reply_markup=confirm_keyboard("ab_confirm", "ab_cancel"),
    )
    return CONFIRM


async def confirm_add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    data = context.user_data.pop("add_balance", None)
    if query.data == "ab_cancel" or not data:
        await query.edit_message_reply_markup(reply_markup=None)
        await update.effective_chat.send_message(
            texts.OPERATION_CANCELED, reply_markup=MAIN_MENU
        )
        return ConversationHandler.END

    telegram_id = data["telegram_id"]
    amount = data["amount"]

    await add_wallet(telegram_id, amount)
    await insert_transaction(telegram_id, amount, "deposit")

    await query.edit_message_reply_markup(reply_markup=None)
    await update.effective_chat.send_message(texts.AB_SUCCESS, reply_markup=MAIN_MENU)

    notified = await notify_user(
        telegram_id,
        user_texts.WALLET_CHARGED_BY_ADMIN.format(amount=format_price(amount)),
    )
    if not notified:
        await update.effective_chat.send_message(texts.USER_NOTIFY_FAILED)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("add_balance", None)
    await update.effective_message.reply_text(
        texts.OPERATION_CANCELED, reply_markup=MAIN_MENU
    )
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("add_balance", None)
    await start(update, context)
    return ConversationHandler.END


def build_add_balance_conversation_handler() -> ConversationHandler:
    cancel_handler = MessageHandler(filters.Regex(btn_regex(texts.BTN_CANCEL)), cancel)
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(btn_regex(texts.BTN_ADD_BALANCE)), start_add_balance)
        ],
        states={
            ASK_TID: [cancel_handler, MessageHandler(filters.TEXT & ~filters.COMMAND, enter_tid)],
            ASK_AMOUNT: [cancel_handler, MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)],
            CONFIRM: [CallbackQueryHandler(confirm_add_balance, pattern="^ab_")],
        },
        fallbacks=[cancel_handler, CommandHandler("start", restart)],
    )
