from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from admin_bot import texts

MAIN_MENU = ReplyKeyboardMarkup(
    [
        [texts.BTN_ADD_USER, texts.BTN_CHECK_USER],
        [texts.BTN_ADD_BALANCE, texts.BTN_USER_MANAGER],
        [texts.BTN_PLAN_MANAGER],
    ],
    resize_keyboard=True,
)

CANCEL_MENU = ReplyKeyboardMarkup(
    [[texts.BTN_CANCEL]],
    resize_keyboard=True,
)


def plans_keyboard(plans: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(f"💎 {plan['name']}", callback_data=f"aplan_{plan['id']}")]
        for plan in plans
    ]
    buttons.append([InlineKeyboardButton(texts.BTN_CANCEL_INLINE, callback_data="acancel")])
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard(
    confirm_data: str = "aconfirm", cancel_data: str = "acancel"
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(texts.BTN_CONFIRM, callback_data=confirm_data),
                InlineKeyboardButton(texts.BTN_CANCEL_INLINE, callback_data=cancel_data),
            ]
        ]
    )


def skip_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(texts.BTN_SKIP, callback_data="askip")]]
    )


def user_row_keyboard(guard_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(texts.BTN_UM_ENABLE, callback_data=f"enable_{guard_username}"),
                InlineKeyboardButton(texts.BTN_UM_DISABLE, callback_data=f"disable_{guard_username}"),
                InlineKeyboardButton(texts.BTN_UM_DELETE, callback_data=f"delete_{guard_username}"),
            ]
        ]
    )


def pagination_keyboard(page: int, has_next: bool) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    if page > 0:
        row.append(InlineKeyboardButton(texts.BTN_UM_PREV, callback_data=f"page_{page - 1}"))
    if has_next:
        row.append(InlineKeyboardButton(texts.BTN_UM_NEXT, callback_data=f"page_{page + 1}"))
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def plan_manager_menu_keyboard(plans: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(f"💎 {plan['name']}", callback_data=f"pm_view_{plan['id']}")]
        for plan in plans
    ]
    buttons.append([InlineKeyboardButton(texts.BTN_PM_ADD, callback_data="pm_add")])
    buttons.append([InlineKeyboardButton(texts.BTN_PM_CLOSE, callback_data="pm_close")])
    return InlineKeyboardMarkup(buttons)


def plan_detail_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(texts.BTN_PM_EDIT_NAME, callback_data="pm_edit_name"),
                InlineKeyboardButton(texts.BTN_PM_EDIT_DATA, callback_data="pm_edit_data"),
            ],
            [
                InlineKeyboardButton(texts.BTN_PM_EDIT_DAYS, callback_data="pm_edit_days"),
                InlineKeyboardButton(texts.BTN_PM_EDIT_PRICE, callback_data="pm_edit_price"),
            ],
            [InlineKeyboardButton(texts.BTN_PM_EDIT_SERVICES, callback_data="pm_edit_services")],
            [
                InlineKeyboardButton(texts.BTN_PM_DELETE, callback_data="pm_delete"),
                InlineKeyboardButton(texts.BTN_PM_BACK, callback_data="pm_back"),
            ],
        ]
    )


def services_select_keyboard(
    services: list[dict], selected: set[int]
) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                f"{'✅' if svc['id'] in selected else '▫️'} {svc['remark']} (#{svc['id']})",
                callback_data=f"pm_svc_{svc['id']}",
            )
        ]
        for svc in services
    ]
    buttons.append(
        [
            InlineKeyboardButton(texts.BTN_PM_SVC_DONE, callback_data="pm_svc_done"),
            InlineKeyboardButton(texts.BTN_CANCEL_INLINE, callback_data="pm_svc_cancel"),
        ]
    )
    return InlineKeyboardMarkup(buttons)


def topup_review_keyboard(request_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(texts.BTN_APPROVE, callback_data=f"topup_ok_{request_id}"),
                InlineKeyboardButton(texts.BTN_REJECT, callback_data=f"topup_no_{request_id}"),
            ]
        ]
    )
