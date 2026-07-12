from telegram import Update
from telegram.ext import ContextTypes

from db.subscriptions import get_user_subscriptions
from guard.api import get_subscription
from utils.decorators import registered_only
from utils.formatters import format_subscription
from user_bot import texts


@registered_only
async def my_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    rows = await get_user_subscriptions(user.id)
    if not rows:
        await update.effective_message.reply_text(texts.NO_SUBSCRIPTIONS)
        return

    for row in rows:
        try:
            sub = await get_subscription(row["guard_username"])
        except Exception:
            await update.effective_message.reply_text(
                texts.SUBSCRIPTION_FETCH_ERROR.format(name=row["guard_username"])
            )
            continue
        await update.effective_message.reply_text(format_subscription(sub))
