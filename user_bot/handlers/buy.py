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

from db.plans import get_plan, get_plans
from db.subscriptions import insert as insert_subscription
from db.transactions import insert_transaction
from db.users import add_wallet, deduct_wallet, get_user
from guard.api import create_subscription, make_guard_username
from utils.decorators import registered_only
from utils.formatters import format_plan_line, format_price
from utils.telegram import btn_regex
from user_bot import texts
from user_bot.handlers.start import start
from user_bot.keyboards import MAIN_MENU, confirm_keyboard, plans_keyboard

logger = logging.getLogger(__name__)

SELECTING_PLAN, CONFIRMING = range(2)


@registered_only
async def start_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    plans = await get_plans()
    if not plans:
        await update.effective_message.reply_text(texts.NO_PLANS)
        return ConversationHandler.END
    await update.effective_message.reply_text(
        texts.CHOOSE_PLAN, reply_markup=plans_keyboard(plans)
    )
    return SELECTING_PLAN


async def select_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text(texts.PURCHASE_CANCELED)
        return ConversationHandler.END

    plan_id = int(query.data.removeprefix("plan_"))
    plan = await get_plan(plan_id)
    if not plan:
        await query.edit_message_text(texts.PLAN_NOT_FOUND)
        return ConversationHandler.END

    context.user_data["buy_plan_id"] = plan_id
    user = await get_user(update.effective_user.id)
    text = texts.CONFIRM_PURCHASE.format(
        plan_line=format_plan_line(plan),
        balance=format_price(int(user["wallet_balance"])),
    )
    await query.edit_message_text(text, reply_markup=confirm_keyboard())
    return CONFIRMING


async def confirm_purchase(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "cancel":
        await query.edit_message_text(texts.PURCHASE_CANCELED)
        context.user_data.pop("buy_plan_id", None)
        return ConversationHandler.END

    plan_id = context.user_data.pop("buy_plan_id", None)
    plan = await get_plan(plan_id) if plan_id else None
    if not plan:
        await query.edit_message_text(texts.PLAN_NOT_FOUND)
        return ConversationHandler.END

    telegram_id = update.effective_user.id
    price = plan["price_toman"]

    if not await deduct_wallet(telegram_id, price):
        await query.edit_message_text(texts.INSUFFICIENT_BALANCE)
        return ConversationHandler.END

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
        await add_wallet(telegram_id, price)  # refund
        await query.edit_message_text(texts.PROVISION_FAILED)
        return ConversationHandler.END

    await insert_subscription(telegram_id, guard_username, plan_id)
    await insert_transaction(telegram_id, price, "purchase", note=plan["name"])

    await query.edit_message_text(texts.PURCHASE_SUCCESS.format(link=sub.link))
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("buy_plan_id", None)
    await update.effective_message.reply_text(
        texts.OPERATION_CANCELED, reply_markup=MAIN_MENU
    )
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("buy_plan_id", None)
    await start(update, context)
    return ConversationHandler.END


def build_buy_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(btn_regex(texts.BTN_BUY)), start_buy)],
        states={
            SELECTING_PLAN: [
                CallbackQueryHandler(select_plan, pattern=r"^(plan_\d+|cancel)$")
            ],
            CONFIRMING: [
                CallbackQueryHandler(confirm_purchase, pattern=r"^(confirm|cancel)$")
            ],
        },
        fallbacks=[
            MessageHandler(filters.Regex(btn_regex(texts.BTN_CANCEL)), cancel),
            CommandHandler("start", restart),
        ],
    )
