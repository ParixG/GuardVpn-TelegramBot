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

from db.plans import create_plan, delete_plan, get_plan, get_plans, update_plan
from guard.api import get_services
from utils.decorators import admin_only
from utils.formatters import format_price
from utils.telegram import btn_regex, normalize_digits
from admin_bot import texts
from admin_bot.handlers.start import start
from admin_bot.keyboards import (
    CANCEL_MENU,
    MAIN_MENU,
    confirm_keyboard,
    plan_detail_keyboard,
    plan_manager_menu_keyboard,
    services_select_keyboard,
)

logger = logging.getLogger(__name__)

(
    MENU,
    VIEW,
    EDIT_VALUE,
    EDIT_SERVICES,
    DELETE_CONFIRM,
    ADD_NAME,
    ADD_DATA,
    ADD_DAYS,
    ADD_PRICE,
    ADD_SERVICES,
    ADD_CONFIRM,
) = range(11)


def _parse_name(text: str) -> Optional[str]:
    text = text.strip()
    return text or None


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
    "name": ("name", texts.PM_FIELD_NAME, _parse_name, texts.PM_INVALID_NAME),
    "data": ("data_limit_gb", texts.PM_FIELD_DATA, _parse_gb, texts.PM_INVALID_GB),
    "days": ("duration_days", texts.PM_FIELD_DAYS, _parse_positive_int, texts.INVALID_NUMBER),
    "price": ("price_toman", texts.PM_FIELD_PRICE, _parse_positive_int, texts.INVALID_NUMBER),
    "services": (
        "guard_service_ids",
        texts.PM_FIELD_SERVICES,
        _parse_services,
        texts.PM_INVALID_SERVICES,
    ),
}


def _service_ids(plan: dict) -> list[int]:
    raw = plan["guard_service_ids"]
    return json.loads(raw) if isinstance(raw, str) else raw


def _detail_text(plan: dict) -> str:
    return texts.PM_PLAN_DETAIL.format(
        id=plan["id"],
        name=plan["name"],
        data_limit_gb=plan["data_limit_gb"],
        duration_days=plan["duration_days"],
        price=format_price(plan["price_toman"]),
        service_ids=", ".join(str(i) for i in _service_ids(plan)) or "-",
    )


def _new_plan_detail_text(data: dict) -> str:
    return texts.PM_PLAN_DETAIL.format(
        id="جدید",
        name=data["name"],
        data_limit_gb=data["data_limit_gb"],
        duration_days=data["duration_days"],
        price=format_price(data["price_toman"]),
        service_ids=", ".join(str(i) for i in data["guard_service_ids"]),
    )


@admin_only
async def open_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["plan_manager"] = {}
    plans = await get_plans()
    text = texts.PM_MENU if plans else texts.PM_NO_PLANS
    await update.effective_message.reply_text(
        text, reply_markup=plan_manager_menu_keyboard(plans)
    )
    return MENU


async def _show_menu_via_edit(update: Update) -> int:
    plans = await get_plans()
    text = texts.PM_MENU if plans else texts.PM_NO_PLANS
    await update.callback_query.edit_message_text(
        text, reply_markup=plan_manager_menu_keyboard(plans)
    )
    return MENU


async def _show_detail(update: Update, plan: dict, via_edit: bool) -> int:
    text = _detail_text(plan)
    if via_edit:
        await update.callback_query.edit_message_text(
            text, reply_markup=plan_detail_keyboard()
        )
    else:
        await update.effective_message.reply_text(
            text, reply_markup=plan_detail_keyboard()
        )
    return VIEW


async def menu_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "pm_close":
        context.user_data.pop("plan_manager", None)
        await query.edit_message_reply_markup(reply_markup=None)
        await update.effective_chat.send_message(texts.BACK_TO_MENU, reply_markup=MAIN_MENU)
        return ConversationHandler.END

    if query.data == "pm_add":
        context.user_data["plan_manager"] = {"new_plan": {}}
        await query.edit_message_reply_markup(reply_markup=None)
        await update.effective_chat.send_message(texts.PM_ASK_NAME, reply_markup=CANCEL_MENU)
        return ADD_NAME

    if query.data.startswith("pm_view_"):
        plan_id = int(query.data.removeprefix("pm_view_"))
        plan = await get_plan(plan_id)
        if not plan:
            await query.edit_message_text(texts.PLAN_NOT_FOUND)
            return await _show_menu_via_edit(update)
        context.user_data["plan_manager"] = {"plan_id": plan_id}
        return await _show_detail(update, plan, via_edit=True)

    return MENU


async def view_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = context.user_data.setdefault("plan_manager", {})
    plan_id = data.get("plan_id")

    if query.data == "pm_back" or plan_id is None:
        return await _show_menu_via_edit(update)

    if query.data == "pm_delete":
        plan = await get_plan(plan_id)
        if not plan:
            await query.edit_message_text(texts.PLAN_NOT_FOUND)
            return await _show_menu_via_edit(update)
        await query.edit_message_text(
            texts.PM_DELETE_CONFIRM.format(name=plan["name"]),
            reply_markup=confirm_keyboard("pm_del_yes", "pm_del_no"),
        )
        return DELETE_CONFIRM

    if query.data == "pm_edit_services":
        plan = await get_plan(plan_id)
        if not plan:
            await query.edit_message_text(texts.PLAN_NOT_FOUND)
            return await _show_menu_via_edit(update)
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
        data["selected"] = set(_service_ids(plan))
        await query.edit_message_text(
            texts.PM_CHOOSE_SERVICES,
            reply_markup=services_select_keyboard(services, data["selected"]),
        )
        return EDIT_SERVICES

    if query.data.startswith("pm_edit_"):
        field_key = query.data.removeprefix("pm_edit_")
        spec = FIELD_SPECS.get(field_key)
        if not spec:
            return VIEW
        data["edit_field"] = field_key
        await query.edit_message_reply_markup(reply_markup=None)
        await update.effective_chat.send_message(
            texts.PM_ASK_NEW_VALUE.format(field=spec[1]), reply_markup=CANCEL_MENU
        )
        return EDIT_VALUE

    return VIEW


async def _fetch_services() -> Optional[list[dict]]:
    try:
        return await get_services()
    except Exception:
        logger.exception("Failed to fetch Guard services")
        return None


async def toggle_service(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = context.user_data.setdefault("plan_manager", {})
    services = data.get("services") or []
    selected = data.setdefault("selected", set())

    service_id = int(query.data.removeprefix("pm_svc_"))
    if service_id in selected:
        selected.discard(service_id)
    else:
        selected.add(service_id)
    await query.edit_message_reply_markup(
        reply_markup=services_select_keyboard(services, selected)
    )
    return None  # keep the current conversation state


async def edit_services_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    query = update.callback_query
    data = context.user_data.get("plan_manager", {})
    selected = data.get("selected") or set()
    plan_id = data.get("plan_id")

    if not selected:
        await query.answer(texts.PM_SVC_NEED_ONE, show_alert=True)
        return None
    await query.answer()

    plan = None
    if plan_id is not None:
        try:
            plan = await update_plan(plan_id, {"guard_service_ids": sorted(selected)})
        except Exception:
            logger.exception("Failed to update services of plan %s", plan_id)
    if not plan:
        await query.edit_message_text(texts.PM_ERROR)
        await update.effective_chat.send_message(texts.BACK_TO_MENU, reply_markup=MAIN_MENU)
        return ConversationHandler.END

    await query.edit_message_text(texts.PM_UPDATED)
    return await _show_detail(update, plan, via_edit=False)


async def edit_services_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    plan_id = context.user_data.get("plan_manager", {}).get("plan_id")
    plan = await get_plan(plan_id) if plan_id is not None else None
    if plan:
        return await _show_detail(update, plan, via_edit=True)
    return await _show_menu_via_edit(update)


async def enter_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    data = context.user_data.get("plan_manager", {})
    plan_id = data.get("plan_id")
    spec = FIELD_SPECS.get(data.get("edit_field", ""))
    if plan_id is None or spec is None:
        await update.effective_message.reply_text(texts.PM_ERROR, reply_markup=MAIN_MENU)
        return ConversationHandler.END

    column, _label, parser, invalid_msg = spec
    value = parser(update.effective_message.text)
    if value is None:
        await update.effective_message.reply_text(invalid_msg)
        return EDIT_VALUE

    try:
        plan = await update_plan(plan_id, {column: value})
    except Exception:
        logger.exception("Failed to update plan %s", plan_id)
        plan = None
    if not plan:
        await update.effective_message.reply_text(texts.PM_ERROR, reply_markup=MAIN_MENU)
        return ConversationHandler.END

    await update.effective_message.reply_text(texts.PM_UPDATED, reply_markup=MAIN_MENU)
    return await _show_detail(update, plan, via_edit=False)


async def delete_confirm_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    data = context.user_data.get("plan_manager", {})
    plan_id = data.get("plan_id")

    if query.data != "pm_del_yes" or plan_id is None:
        plan = await get_plan(plan_id) if plan_id is not None else None
        if plan:
            return await _show_detail(update, plan, via_edit=True)
        return await _show_menu_via_edit(update)

    plan = await get_plan(plan_id)
    if not plan:
        await query.edit_message_text(texts.PLAN_NOT_FOUND)
        return await _show_menu_via_edit(update)

    try:
        await delete_plan(plan_id)
    except Exception as exc:
        logger.exception("Failed to delete plan %s", plan_id)
        # 23503 = foreign-key violation: subscriptions still reference this plan
        if getattr(exc, "code", None) == "23503":
            await query.edit_message_text(texts.PM_DELETE_HAS_SUBS)
        else:
            await query.edit_message_text(texts.PM_ERROR)
        return await _show_detail(update, plan, via_edit=False)

    await query.edit_message_text(texts.PM_DELETED.format(name=plan["name"]))
    plans = await get_plans()
    text = texts.PM_MENU if plans else texts.PM_NO_PLANS
    await update.effective_chat.send_message(
        text, reply_markup=plan_manager_menu_keyboard(plans)
    )
    return MENU


async def add_enter_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = _parse_name(update.effective_message.text)
    if name is None:
        await update.effective_message.reply_text(texts.PM_INVALID_NAME)
        return ADD_NAME
    context.user_data["plan_manager"]["new_plan"]["name"] = name
    await update.effective_message.reply_text(texts.PM_ASK_DATA)
    return ADD_DATA


async def add_enter_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = _parse_gb(update.effective_message.text)
    if value is None:
        await update.effective_message.reply_text(texts.PM_INVALID_GB)
        return ADD_DATA
    context.user_data["plan_manager"]["new_plan"]["data_limit_gb"] = value
    await update.effective_message.reply_text(texts.PM_ASK_DAYS)
    return ADD_DAYS


async def add_enter_days(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = _parse_positive_int(update.effective_message.text)
    if value is None:
        await update.effective_message.reply_text(texts.INVALID_NUMBER)
        return ADD_DAYS
    context.user_data["plan_manager"]["new_plan"]["duration_days"] = value
    await update.effective_message.reply_text(texts.PM_ASK_PRICE)
    return ADD_PRICE


async def add_enter_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = _parse_positive_int(update.effective_message.text)
    if value is None:
        await update.effective_message.reply_text(texts.INVALID_NUMBER)
        return ADD_PRICE
    data = context.user_data["plan_manager"]
    data["new_plan"]["price_toman"] = value

    services = await _fetch_services()
    if not services:
        # Panel unreachable (or empty) — fall back to manual ID entry.
        await update.effective_message.reply_text(texts.PM_SERVICES_FETCH_FAILED)
        return ADD_SERVICES
    data["services"] = services
    data["selected"] = set()
    await update.effective_message.reply_text(
        texts.PM_CHOOSE_SERVICES,
        reply_markup=services_select_keyboard(services, set()),
    )
    return ADD_SERVICES


async def add_enter_services(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    value = _parse_services(update.effective_message.text)
    if value is None:
        await update.effective_message.reply_text(texts.PM_INVALID_SERVICES)
        return ADD_SERVICES

    new_plan = context.user_data["plan_manager"]["new_plan"]
    new_plan["guard_service_ids"] = value
    await update.effective_message.reply_text(
        texts.PM_ADD_CONFIRM.format(detail=_new_plan_detail_text(new_plan)),
        reply_markup=confirm_keyboard("pm_add_ok", "pm_add_no"),
    )
    return ADD_CONFIRM


async def add_services_done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    query = update.callback_query
    data = context.user_data.get("plan_manager", {})
    selected = data.get("selected") or set()

    if not selected:
        await query.answer(texts.PM_SVC_NEED_ONE, show_alert=True)
        return None
    await query.answer()

    new_plan = data["new_plan"]
    new_plan["guard_service_ids"] = sorted(selected)
    await query.edit_message_text(
        texts.PM_ADD_CONFIRM.format(detail=_new_plan_detail_text(new_plan)),
        reply_markup=confirm_keyboard("pm_add_ok", "pm_add_no"),
    )
    return ADD_CONFIRM


async def add_services_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data.pop("plan_manager", None)
    await query.edit_message_reply_markup(reply_markup=None)
    await update.effective_chat.send_message(
        texts.OPERATION_CANCELED, reply_markup=MAIN_MENU
    )
    return ConversationHandler.END


async def add_confirm_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    data = context.user_data.pop("plan_manager", None) or {}
    new_plan = data.get("new_plan")
    if query.data != "pm_add_ok" or not new_plan:
        await query.edit_message_reply_markup(reply_markup=None)
        await update.effective_chat.send_message(
            texts.OPERATION_CANCELED, reply_markup=MAIN_MENU
        )
        return ConversationHandler.END

    try:
        await create_plan(
            new_plan["name"],
            new_plan["data_limit_gb"],
            new_plan["duration_days"],
            new_plan["price_toman"],
            new_plan["guard_service_ids"],
        )
    except Exception:
        logger.exception("Failed to create plan")
        await query.edit_message_text(texts.PM_ERROR)
        await update.effective_chat.send_message(texts.BACK_TO_MENU, reply_markup=MAIN_MENU)
        return ConversationHandler.END

    await query.edit_message_reply_markup(reply_markup=None)
    await update.effective_chat.send_message(texts.PM_CREATED, reply_markup=MAIN_MENU)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("plan_manager", None)
    await update.effective_message.reply_text(
        texts.OPERATION_CANCELED, reply_markup=MAIN_MENU
    )
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("plan_manager", None)
    await start(update, context)
    return ConversationHandler.END


def build_plan_manager_conversation_handler() -> ConversationHandler:
    cancel_handler = MessageHandler(filters.Regex(btn_regex(texts.BTN_CANCEL)), cancel)
    text_input = filters.TEXT & ~filters.COMMAND
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(btn_regex(texts.BTN_PLAN_MANAGER)), open_menu)
        ],
        states={
            MENU: [CallbackQueryHandler(menu_click, pattern="^pm_")],
            VIEW: [CallbackQueryHandler(view_click, pattern="^pm_")],
            EDIT_VALUE: [cancel_handler, MessageHandler(text_input, enter_new_value)],
            EDIT_SERVICES: [
                cancel_handler,
                CallbackQueryHandler(edit_services_done, pattern="^pm_svc_done$"),
                CallbackQueryHandler(edit_services_back, pattern="^pm_svc_cancel$"),
                CallbackQueryHandler(toggle_service, pattern="^pm_svc_\\d+$"),
            ],
            DELETE_CONFIRM: [CallbackQueryHandler(delete_confirm_click, pattern="^pm_del_")],
            ADD_NAME: [cancel_handler, MessageHandler(text_input, add_enter_name)],
            ADD_DATA: [cancel_handler, MessageHandler(text_input, add_enter_data)],
            ADD_DAYS: [cancel_handler, MessageHandler(text_input, add_enter_days)],
            ADD_PRICE: [cancel_handler, MessageHandler(text_input, add_enter_price)],
            ADD_SERVICES: [
                cancel_handler,
                CallbackQueryHandler(add_services_done, pattern="^pm_svc_done$"),
                CallbackQueryHandler(add_services_cancel, pattern="^pm_svc_cancel$"),
                CallbackQueryHandler(toggle_service, pattern="^pm_svc_\\d+$"),
                MessageHandler(text_input, add_enter_services),
            ],
            ADD_CONFIRM: [CallbackQueryHandler(add_confirm_click, pattern="^pm_add_")],
        },
        fallbacks=[cancel_handler, CommandHandler("start", restart)],
    )
