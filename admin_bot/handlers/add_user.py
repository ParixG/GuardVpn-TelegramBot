import json
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

from bridge import notify_user
from db.plans import get_plan, get_plans
from db.subscriptions import insert as insert_subscription
from db.users import upsert_user
from guard.api import create_subscription, make_guard_username
from utils.decorators import admin_only
from utils.formatters import format_plan_line
from utils.telegram import btn_regex, normalize_digits
from admin_bot import texts
from admin_bot.handlers.start import start
from admin_bot.keyboards import (
    CANCEL_MENU,
    MAIN_MENU,
    confirm_keyboard,
    plans_keyboard,
    skip_keyboard,
)
from user_bot import texts as user_texts

logger = logging.getLogger(__name__)

ENTER_TID, ENTER_USERNAME, SELECT_PLAN, CONFIRM_ADD = range(4)


@admin_only
async def start_add_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["add_user"] = {}
    await update.effective_message.reply_text(texts.ASK_TID, reply_markup=CANCEL_MENU)
    return ENTER_TID


async def enter_tid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = normalize_digits(update.effective_message.text)
    if not text.isdigit():
        await update.effective_message.reply_text(texts.INVALID_NUMBER)
        return ENTER_TID
    context.user_data["add_user"]["telegram_id"] = int(text)
    await update.effective_message.reply_text(
        texts.ASK_GUARD_USERNAME, reply_markup=skip_keyboard()
    )
    return ENTER_USERNAME


async def skip_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["add_user"]["username_prefix"] = None
    return await _show_plans(update, context)


async def enter_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.effective_message.text.strip()
    context.user_data["add_user"]["username_prefix"] = text
    return await _show_plans(update, context)


async def _show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    plans = await get_plans()
    if not plans:
        await update.effective_message.reply_text(texts.NO_PLANS, reply_markup=MAIN_MENU)
        return ConversationHandler.END

    await update.effective_message.reply_text(
        texts.CHOOSE_PLAN, reply_markup=plans_keyboard(plans)
    )
    return SELECT_PLAN


async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "acancel":
        return await _cancel_from_callback(update, context)

    plan_id = int(query.data.removeprefix("aplan_"))
    plan = await get_plan(plan_id)
    if not plan:
        await query.edit_message_text(texts.PLAN_NOT_FOUND)
        return ConversationHandler.END

    context.user_data["add_user"]["plan_id"] = plan_id
    data = context.user_data["add_user"]
    text = texts.CONFIRM_ADD_USER.format(
        telegram_id=data["telegram_id"],
        username_prefix=data["username_prefix"] or "(پیش‌فرض)",
        plan_line=format_plan_line(plan),
    )
    await query.edit_message_text(text, reply_markup=confirm_keyboard())
    return CONFIRM_ADD


async def confirm_add(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    data = context.user_data.pop("add_user", None)
    if query.data == "acancel" or not data:
        return await _cancel_from_callback(update, context)

    telegram_id = data["telegram_id"]
    plan_id = data["plan_id"]
    plan = await get_plan(plan_id)
    if not plan:
        await query.edit_message_text(texts.PLAN_NOT_FOUND)
        return ConversationHandler.END

    await upsert_user(telegram_id, None, data["username_prefix"] or str(telegram_id))

    guard_username = make_guard_username(telegram_id, plan_id)
    raw_service_ids = plan["guard_service_ids"]
    service_ids = (
        json.loads(raw_service_ids) if isinstance(raw_service_ids, str) else raw_service_ids
    )

    try:
        sub = await create_subscription(
            guard_username, plan["data_limit_gb"], plan["duration_days"], service_ids
        )
    except Exception:
        logger.exception("Failed to create Guard subscription for %s", guard_username)
        await query.edit_message_text(texts.GUARD_CREATE_FAILED)
        return ConversationHandler.END

    await insert_subscription(telegram_id, guard_username, plan_id)

    await query.edit_message_reply_markup(reply_markup=None)
    await update.effective_chat.send_message(
        texts.ADD_USER_SUCCESS.format(link=sub.link), reply_markup=MAIN_MENU
    )

    notified = await notify_user(
        telegram_id, user_texts.SUBSCRIPTION_ACTIVATED.format(link=sub.link)
    )
    if not notified:
        await update.effective_chat.send_message(texts.USER_NOTIFY_FAILED)

    return ConversationHandler.END


async def _cancel_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("add_user", None)
    await update.callback_query.edit_message_reply_markup(reply_markup=None)
    await update.effective_chat.send_message(
        texts.OPERATION_CANCELED, reply_markup=MAIN_MENU
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("add_user", None)
    await update.effective_message.reply_text(
        texts.OPERATION_CANCELED, reply_markup=MAIN_MENU
    )
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("add_user", None)
    await start(update, context)
    return ConversationHandler.END


def build_add_user_conversation_handler() -> ConversationHandler:
    cancel_handler = MessageHandler(filters.Regex(btn_regex(texts.BTN_CANCEL)), cancel)
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(btn_regex(texts.BTN_ADD_USER)), start_add_user)
        ],
        states={
            ENTER_TID: [cancel_handler, MessageHandler(filters.TEXT & ~filters.COMMAND, enter_tid)],
            ENTER_USERNAME: [
                cancel_handler,
                CallbackQueryHandler(skip_username, pattern="^askip$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_username),
            ],
            SELECT_PLAN: [CallbackQueryHandler(select_plan)],
            CONFIRM_ADD: [CallbackQueryHandler(confirm_add)],
        },
        fallbacks=[cancel_handler, CommandHandler("start", restart)],
    )
