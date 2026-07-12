import logging

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from bridge import notify_user
from db.topups import decide
from db.users import get_user
from utils.decorators import admin_only
from utils.formatters import format_price
from admin_bot import texts
from user_bot import texts as user_texts

logger = logging.getLogger(__name__)


async def _handle_decision(
    update: Update, context: ContextTypes.DEFAULT_TYPE, approve: bool
) -> None:
    query = update.callback_query
    prefix = "topup_ok_" if approve else "topup_no_"
    request_id = query.data.removeprefix(prefix)

    # Money moves only inside the decide_topup RPC (CAS on status +
    # wallet credit + ledger insert in one DB transaction), so repeat
    # clicks and racing admins can never double-credit.
    row = await decide(request_id, update.effective_user.id, approve)
    if row is None:
        await query.answer(texts.TOPUP_ALREADY_DECIDED, show_alert=True)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    await query.answer()

    amount = format_price(int(float(row["amount"])))
    if approve:
        user_message = user_texts.TOPUP_APPROVED.format(amount=amount)
        suffix = texts.TOPUP_APPROVED_SUFFIX.format(admin=update.effective_user.first_name)
    else:
        user_message = user_texts.TOPUP_REJECTED
        suffix = texts.TOPUP_REJECTED_SUFFIX.format(admin=update.effective_user.first_name)

    notified = await notify_user(row["user_telegram_id"], user_message)

    customer = await get_user(row["user_telegram_id"]) or {}
    caption = texts.TOPUP_CAPTION.format(
        name=customer.get("first_name", "-"),
        username=customer.get("username") or "-",
        telegram_id=row["user_telegram_id"],
        amount=amount,
        created_at=row["created_at"][:19].replace("T", " "),
        request_id=row["id"][:8],
    )

    # Update every admin's copy of the receipt so nobody acts on a
    # request that has already been decided.
    for ref in row.get("admin_messages") or []:
        try:
            await context.bot.edit_message_caption(
                chat_id=ref["chat_id"],
                message_id=ref["message_id"],
                caption=caption + suffix,
                reply_markup=None,
            )
        except Exception:
            logger.exception(
                "Failed to update admin copy %s for topup %s", ref, request_id
            )

    if not notified:
        try:
            await update.effective_chat.send_message(texts.USER_NOTIFY_FAILED)
        except Exception:
            pass


@admin_only
async def approve_topup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_decision(update, context, approve=True)


@admin_only
async def reject_topup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _handle_decision(update, context, approve=False)


def register_topup_review_handlers(app) -> None:
    app.add_handler(CallbackQueryHandler(approve_topup, pattern="^topup_ok_"))
    app.add_handler(CallbackQueryHandler(reject_topup, pattern="^topup_no_"))
