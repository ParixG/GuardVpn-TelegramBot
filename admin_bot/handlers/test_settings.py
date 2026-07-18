import json
import logging
from typing import Optional

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from db.settings import get_test_settings, update_test_settings
from guard.api import get_services
from utils.decorators import admin_only
from utils.telegram import btn_regex, normalize_digits
from admin_bot import texts
from admin_bot.handlers.start import start
from admin_bot.keyboards import (
    CANCEL_MENU,
    MAIN_MENU,
    services_select_keyboard,
    test_settings_keyboard,
)

logger = logging.getLogger(__name__)

MENU, EDIT_VALUE, EDIT_SERVICES = range(3)

SVC_PREFIX = "ts_svc_"


def _parse_gb(text: str) -> Optional[float]:
    try:
        value = float(normalize_digits(text))
    except ValueError:
        return None
    return value if value > 0 else None


def _parse_positive_int(text: str) -> Optional[int]:
    text = normalize_digits(text)
    if not text.isdigit() or int(text) <= 0:
        return None
    return int(text)


def _parse_services(text: str) -> Optional[list[int]]:
    parts = [p.strip() for p in normalize_digits(text).split(",")]
    if not parts or not all(p.isdigit() for p in parts):
        return None
    return [int(p) for p in parts]


# callback field key -> (db column, label, parser, invalid-input message)
FIELD_SPECS = {
    "data": ("data_limit_gb", texts.PM_FIELD_DATA, _parse_gb, texts.PM_INVALID_GB),
    "days": ("duration_days", texts.PM_FIELD_DAYS, _parse_positive_int, texts.INVALID_NUMBER),
    "services": (
        "guard_service_ids",
        texts.PM_FIELD_SERVICES,
        _parse_services,
        texts.PM_INVALID_SERVICES,
    ),
}


def _service_ids(settings: dict) -> list[int]:
    raw = settings["guard_service_ids"]
    return json.loads(raw) if isinstance(raw, str) else raw


def _detail_text(settings: dict) -> str:
    status = texts.TS_STATUS_ON if settings["enabled"] else texts.TS_STATUS_OFF
    return texts.TS_DETAIL.format(
        status=status,
        data_limit_gb=settings["data_limit_gb"],
        duration_days=settings["duration_days"],
        service_ids=", ".join(str(i) for i in _service_ids(settings)) or "-",
    )


async def _show_detail(update: Update, settings: dict, via_edit: bool) -> int:
    text = _detail_text(settings)
    markup = test_settings_keyboard(settings["enabled"])
    if via_edit:
        await update.callback_query.edit_message_text(text, reply_markup=markup)
    else:
        await update.effective_message.reply_text(text, reply_markup=markup)
    return MENU


@admin_only
async def open_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["test_settings"] = {}
    settings = await get_test_settings()
    if not settings:
        await update.effective_message.reply_text(texts.TS_NOT_FOUND, reply_markup=MAIN_MENU)
        return ConversationHandler.END
    return await _show_detail(update, settings, via_edit=False)


async def menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    data = context.user_data.setdefault("test_settings", {})

    if query.data == "ts_close":
        await query.answer()
        context.user_data.pop("test_settings", None)
        await query.edit_message_reply_markup(reply_markup=None)
        await update.effective_chat.send_message(texts.BACK_TO_MENU, reply_markup=MAIN_MENU)
        return ConversationHandler.END

    settings = await get_test_settings()
    if not settings:
        await query.answer()
        await query.edit_message_text(texts.TS_NOT_FOUND)
        return ConversationHandler.END

    if query.data == "ts_toggle":
        enabling = not settings["enabled"]
        if enabling and not _service_ids(settings):
            await query.answer(texts.TS_NO_SERVICES_WARNING, show_alert=True)
            return MENU
        await query.answer()
        try:
            updated = await update_test_settings({"enabled": enabling})
        except Exception:
            logger.exception("Failed to toggle test settings")
            updated = None
        if not updated:
            await query.edit_message_text(texts.TS_ERROR)
            return ConversationHandler.END
        return await _show_detail(update, updated, via_edit=True)

    if query.data == "ts_edit_services":
        await query.answer()
        services = await _fetch_services()
        if not services:
            # Panel unreachable (or empty) — fall back to manual ID entry.
            data["edit_field"] = "services"
            await query.edit_message_reply_markup(reply_markup=None)
            await update.effective_chat.send_message(
                texts.PM_SERVICES_FETCH_FAILED, reply_markup=CANCEL_MENU
            )
            return EDIT_VALUE
        data["services"] = services
        data["selected"] = set(_service_ids(settings))
        await query.edit_message_text(
            texts.PM_CHOOSE_SERVICES,
            reply_markup=services_select_keyboard(services, data["selected"], SVC_PREFIX),
        )
        return EDIT_SERVICES

    if query.data.startswith("ts_edit_"):
        await query.answer()
        field_key = query.data.removeprefix("ts_edit_")
        spec = FIELD_SPECS.get(field_key)
        if not spec:
            return MENU
        data["edit_field"] = field_key
        await query.edit_message_reply_markup(reply_markup=None)
        await update.effective_chat.send_message(
            texts.PM_ASK_NEW_VALUE.format(field=spec[1]), reply_markup=CANCEL_MENU
        )
        return EDIT_VALUE

    await query.answer()
    return MENU


async def _fetch_services() -> Optional[list[dict]]:
    try:
        return await get_services()
    except Exception:
        logger.exception("Failed to fetch Guard services")
        return None


async def enter_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("test_settings", {})
    spec = FIELD_SPECS.get(data.get("edit_field", ""))
    if spec is None:
        await update.effective_message.reply_text(texts.TS_ERROR, reply_markup=MAIN_MENU)
        return ConversationHandler.END

    column, _label, parser, invalid_msg = spec
    value = parser(update.effective_message.text)
    if value is None:
        await update.effective_message.reply_text(invalid_msg)
        return EDIT_VALUE

    try:
        settings = await update_test_settings({column: value})
    except Exception:
        logger.exception("Failed to update test settings field %s", column)
        settings = None
    if not settings:
        await update.effective_message.reply_text(texts.TS_ERROR, reply_markup=MAIN_MENU)
        return ConversationHandler.END

    await update.effective_message.reply_text(texts.TS_UPDATED, reply_markup=MAIN_MENU)
    return await _show_detail(update, settings, via_edit=False)


async def toggle_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = context.user_data.setdefault("test_settings", {})
    services = data.get("services") or []
    selected = data.setdefault("selected", set())

    service_id = int(query.data.removeprefix(SVC_PREFIX))
    if service_id in selected:
        selected.discard(service_id)
    else:
        selected.add(service_id)
    await query.edit_message_reply_markup(
        reply_markup=services_select_keyboard(services, selected, SVC_PREFIX)
    )
    return None  # keep the current conversation state


async def edit_services_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    query = update.callback_query
    data = context.user_data.get("test_settings", {})
    selected = data.get("selected") or set()

    if not selected:
        await query.answer(texts.PM_SVC_NEED_ONE, show_alert=True)
        return None
    await query.answer()

    try:
        settings = await update_test_settings({"guard_service_ids": sorted(selected)})
    except Exception:
        logger.exception("Failed to update test settings services")
        settings = None
    if not settings:
        await query.edit_message_text(texts.TS_ERROR)
        await update.effective_chat.send_message(texts.BACK_TO_MENU, reply_markup=MAIN_MENU)
        return ConversationHandler.END

    await query.edit_message_text(texts.TS_UPDATED)
    return await _show_detail(update, settings, via_edit=False)


async def edit_services_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    settings = await get_test_settings()
    if not settings:
        await query.edit_message_text(texts.TS_NOT_FOUND)
        return ConversationHandler.END
    return await _show_detail(update, settings, via_edit=True)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("test_settings", None)
    await update.effective_message.reply_text(
        texts.OPERATION_CANCELED, reply_markup=MAIN_MENU
    )
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("test_settings", None)
    await start(update, context)
    return ConversationHandler.END


def build_test_settings_conversation_handler() -> ConversationHandler:
    cancel_handler = MessageHandler(filters.Regex(btn_regex(texts.BTN_CANCEL)), cancel)
    text_input = filters.TEXT & ~filters.COMMAND
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(btn_regex(texts.BTN_TEST_SETTINGS)), open_menu)
        ],
        states={
            MENU: [CallbackQueryHandler(menu_click, pattern="^ts_")],
            EDIT_VALUE: [cancel_handler, MessageHandler(text_input, enter_new_value)],
            EDIT_SERVICES: [
                cancel_handler,
                CallbackQueryHandler(edit_services_done, pattern="^ts_svc_done$"),
                CallbackQueryHandler(edit_services_back, pattern="^ts_svc_cancel$"),
                CallbackQueryHandler(toggle_service, pattern="^ts_svc_\\d+$"),
            ],
        },
        fallbacks=[cancel_handler, CommandHandler("start", restart)],
    )
