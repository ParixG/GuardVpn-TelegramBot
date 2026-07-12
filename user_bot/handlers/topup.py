import logging

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import bridge
import config
from admin_bot import texts as admin_texts
from admin_bot.keyboards import topup_review_keyboard
from db.topups import create_request, set_admin_messages
from utils.decorators import registered_only
from utils.formatters import format_price
from utils.telegram import btn_regex, normalize_digits
from user_bot import texts
from user_bot.handlers.start import start
from user_bot.keyboards import MAIN_MENU, amounts_keyboard, topup_cancel_keyboard

logger = logging.getLogger(__name__)

CHOOSING_AMOUNT, ENTERING_CUSTOM_AMOUNT, AWAITING_RECEIPT = range(3)

MIN_TOPUP = 10_000

def _parse_amount(text: str) -> int | None:
    cleaned = normalize_digits(text)
    if not cleaned.isdigit():
        return None
    amount = int(cleaned)
    return amount if amount >= MIN_TOPUP else None


def _card_info_text(amount: int) -> str:
    return texts.TOPUP_CARD_INFO.format(
        amount=format_price(amount),
        card_number=config.CARD_NUMBER,
        card_holder=config.CARD_HOLDER,
    )


@registered_only
async def start_topup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        texts.TOPUP_CHOOSE_AMOUNT, reply_markup=amounts_keyboard()
    )
    return CHOOSING_AMOUNT


async def pick_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "amt_cancel":
        await query.edit_message_text(texts.OPERATION_CANCELED)
        return ConversationHandler.END

    if query.data == "amt_custom":
        await query.edit_message_text(
            texts.TOPUP_ENTER_CUSTOM, reply_markup=topup_cancel_keyboard()
        )
        return ENTERING_CUSTOM_AMOUNT

    amount = int(query.data.removeprefix("amt_"))
    context.user_data["topup_amount"] = amount
    await query.edit_message_text(
        _card_info_text(amount),
        reply_markup=topup_cancel_keyboard(),
        parse_mode="HTML",
    )
    return AWAITING_RECEIPT


async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    amount = _parse_amount(update.effective_message.text)
    if amount is None:
        await update.effective_message.reply_text(
            texts.TOPUP_INVALID_AMOUNT.format(min_amount=f"{MIN_TOPUP:,}")
        )
        return ENTERING_CUSTOM_AMOUNT

    context.user_data["topup_amount"] = amount
    await update.effective_message.reply_text(
        _card_info_text(amount),
        reply_markup=topup_cancel_keyboard(),
        parse_mode="HTML",
    )
    return AWAITING_RECEIPT


async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    amount = context.user_data.pop("topup_amount", None)
    if amount is None:
        await update.effective_message.reply_text(texts.TOPUP_SEND_FAILED)
        return ConversationHandler.END

    message = update.effective_message
    attachment = message.photo[-1] if message.photo else message.document
    user = update.effective_user

    row = await create_request(user.id, amount, attachment.file_id)

    # file_ids are bot-scoped: download the receipt with the user bot's
    # token, upload once via the admin bot, then reuse the admin-bot
    # file_id for the remaining admins.
    try:
        file = await attachment.get_file()
        photo_bytes = bytes(await file.download_as_bytearray())
    except Exception:
        logger.exception("Failed to download receipt for topup %s", row["id"])
        await message.reply_text(texts.TOPUP_SEND_FAILED)
        return ConversationHandler.END

    caption = admin_texts.TOPUP_CAPTION.format(
        name=user.first_name,
        username=user.username or "-",
        telegram_id=user.id,
        amount=format_price(amount),
        created_at=row["created_at"][:19].replace("T", " "),
        request_id=row["id"][:8],
    )
    keyboard = topup_review_keyboard(row["id"])

    sent_messages: list[dict] = []
    admin_file_id: str | None = None
    for admin_id in config.ADMIN_IDS:
        try:
            msg = await bridge.admin_bot.send_photo(
                admin_id,
                photo=admin_file_id or photo_bytes,
                caption=caption,
                reply_markup=keyboard,
            )
        except Exception:
            logger.exception("Failed to deliver topup %s to admin %s", row["id"], admin_id)
            continue
        admin_file_id = admin_file_id or msg.photo[-1].file_id
        sent_messages.append({"chat_id": msg.chat_id, "message_id": msg.message_id})

    if not sent_messages:
        await message.reply_text(texts.TOPUP_SEND_FAILED)
        return ConversationHandler.END

    await set_admin_messages(row["id"], sent_messages)
    await message.reply_text(texts.TOPUP_RECEIVED, reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def not_a_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.effective_message.reply_text(texts.TOPUP_NOT_A_PHOTO)
    return AWAITING_RECEIPT


async def cancel_inline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("topup_amount", None)
    await query.edit_message_text(texts.OPERATION_CANCELED)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("topup_amount", None)
    await update.effective_message.reply_text(
        texts.OPERATION_CANCELED, reply_markup=MAIN_MENU
    )
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("topup_amount", None)
    await start(update, context)
    return ConversationHandler.END


def build_topup_conversation_handler() -> ConversationHandler:
    cancel_button = CallbackQueryHandler(cancel_inline, pattern="^topup_cancel$")
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_topup, pattern="^topup_start$")],
        states={
            CHOOSING_AMOUNT: [CallbackQueryHandler(pick_amount, pattern="^amt_")],
            ENTERING_CUSTOM_AMOUNT: [
                cancel_button,
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount),
            ],
            AWAITING_RECEIPT: [
                cancel_button,
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, receive_receipt),
                MessageHandler(filters.TEXT & ~filters.COMMAND, not_a_photo),
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex(btn_regex(texts.BTN_CANCEL)), cancel),
            CommandHandler("start", restart),
        ],
    )
