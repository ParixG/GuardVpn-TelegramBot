import functools

from telegram import Update
from telegram.ext import ContextTypes

import config
from db.users import get_user


def admin_only(handler):
    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_user is None or update.effective_user.id not in config.ADMIN_IDS:
            if update.effective_message:
                await update.effective_message.reply_text("دسترسی ندارید")
            return None
        return await handler(update, context, *args, **kwargs)

    return wrapper


def registered_only(handler):
    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user is None or await get_user(user.id) is None:
            if update.effective_message:
                await update.effective_message.reply_text("ابتدا /start را بزنید")
            return None
        return await handler(update, context, *args, **kwargs)

    return wrapper
