from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes, MessageHandler, filters

from admin_bot import texts
from admin_bot.keyboards import pagination_keyboard, user_row_keyboard
from db.subscriptions import PAGE_SIZE, delete as delete_subscription_row, get_all_paged
from guard.api import delete_subscription, disable_subscription, enable_subscription
from utils.decorators import admin_only
from utils.telegram import btn_regex


def _format_row(row: dict) -> str:
    plan = row.get("plans") or {}
    user = row.get("users") or {}
    return (
        f"👤 {user.get('first_name', '-')} (@{user.get('username') or '-'})\n"
        f"🆔 آیدی: {row['user_telegram_id']}\n"
        f"🔑 نام کاربری Guard: {row['guard_username']}\n"
        f"📋 پلن: {plan.get('name', '-')}"
    )


async def _send_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int) -> None:
    rows, total = await get_all_paged(page)
    if not rows:
        message = update.effective_message
        if update.callback_query:
            await update.callback_query.edit_message_text(texts.UM_NO_USERS)
        else:
            await message.reply_text(texts.UM_NO_USERS)
        return

    has_next = (page + 1) * PAGE_SIZE < total

    for i, row in enumerate(rows):
        text = _format_row(row)
        if update.callback_query and i == 0:
            await update.callback_query.edit_message_text(
                text, reply_markup=user_row_keyboard(row["guard_username"])
            )
        else:
            await update.effective_chat.send_message(
                text, reply_markup=user_row_keyboard(row["guard_username"])
            )

    await update.effective_chat.send_message(
        texts.UM_PAGE.format(page=page + 1),
        reply_markup=pagination_keyboard(page, has_next),
    )


@admin_only
async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send_page(update, context, 0)


@admin_only
async def paginate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    page = int(query.data.removeprefix("page_"))
    await _send_page(update, context, page)


@admin_only
async def enable_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    guard_username = query.data.removeprefix("enable_")
    await query.answer()
    try:
        await enable_subscription(guard_username)
        await query.edit_message_text(texts.UM_ENABLED.format(guard_username=guard_username))
    except Exception:
        await query.edit_message_text(texts.UM_ENABLE_FAILED.format(guard_username=guard_username))


@admin_only
async def disable_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    guard_username = query.data.removeprefix("disable_")
    await query.answer()
    try:
        await disable_subscription(guard_username)
        await query.edit_message_text(texts.UM_DISABLED.format(guard_username=guard_username))
    except Exception:
        await query.edit_message_text(texts.UM_DISABLE_FAILED.format(guard_username=guard_username))


@admin_only
async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    guard_username = query.data.removeprefix("delete_")
    await query.answer()
    try:
        await delete_subscription(guard_username)
    except Exception:
        await query.edit_message_text(texts.UM_DELETE_FAILED.format(guard_username=guard_username))
        return
    await delete_subscription_row(guard_username)
    await query.edit_message_text(texts.UM_DELETED.format(guard_username=guard_username))


def register_user_manager_handlers(app) -> None:
    app.add_handler(MessageHandler(filters.Regex(btn_regex(texts.BTN_USER_MANAGER)), list_users))
    app.add_handler(CallbackQueryHandler(paginate, pattern="^page_"))
    app.add_handler(CallbackQueryHandler(enable_user, pattern="^enable_"))
    app.add_handler(CallbackQueryHandler(disable_user, pattern="^disable_"))
    app.add_handler(CallbackQueryHandler(delete_user, pattern="^delete_"))
