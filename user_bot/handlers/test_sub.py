import json
import logging

from telegram import Update
from telegram.ext import ContextTypes

from db.settings import get_test_settings
from db.subscriptions import insert as insert_subscription
from db.users import claim_test, release_test
from guard.api import create_subscription, make_guard_username
from utils.decorators import registered_only
from user_bot import texts

logger = logging.getLogger(__name__)

TEST_PLAN_ID = 0  # sentinel used only for the guard username; not a real plan


@registered_only
async def get_test_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    settings = await get_test_settings()
    if not settings or not settings["enabled"]:
        await update.effective_message.reply_text(texts.TEST_DISABLED)
        return

    raw_service_ids = settings["guard_service_ids"]
    service_ids = (
        json.loads(raw_service_ids) if isinstance(raw_service_ids, str) else raw_service_ids
    )
    if not service_ids:
        logger.warning("Test subscription enabled but no guard services configured")
        await update.effective_message.reply_text(texts.TEST_DISABLED)
        return

    telegram_id = update.effective_user.id
    if not await claim_test(telegram_id):
        await update.effective_message.reply_text(texts.TEST_ALREADY_USED)
        return

    guard_username = make_guard_username(telegram_id, TEST_PLAN_ID)
    try:
        sub = await create_subscription(
            guard_username,
            float(settings["data_limit_gb"]),
            settings["duration_days"],
            service_ids,
        )
    except Exception:
        logger.exception("Failed to create test subscription for %s", guard_username)
        await release_test(telegram_id)  # let the user retry later
        await update.effective_message.reply_text(texts.TEST_FAILED)
        return

    await insert_subscription(telegram_id, guard_username, plan_id=None)
    await update.effective_message.reply_text(
        texts.TEST_SUCCESS.format(
            data_limit_gb=settings["data_limit_gb"],
            duration_days=settings["duration_days"],
            link=sub.link,
        )
    )
