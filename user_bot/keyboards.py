from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from user_bot import texts

MAIN_MENU = ReplyKeyboardMarkup(
    [[texts.BTN_SUBS, texts.BTN_BUY], [texts.BTN_TEST, texts.BTN_WALLET]],
    resize_keyboard=True,
)

CANCEL_MENU = ReplyKeyboardMarkup(
    [[texts.BTN_CANCEL]],
    resize_keyboard=True,
)

TOPUP_PRESET_AMOUNTS = [100_000, 200_000, 500_000]


def plans_keyboard(plans: list[dict]) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(f"💎 {plan['name']}", callback_data=f"plan_{plan['id']}")]
        for plan in plans
    ]
    buttons.append([InlineKeyboardButton(texts.BTN_CANCEL_INLINE, callback_data="cancel")])
    return InlineKeyboardMarkup(buttons)


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(texts.BTN_CONFIRM_BUY, callback_data="confirm"),
                InlineKeyboardButton(texts.BTN_CANCEL_INLINE, callback_data="cancel"),
            ]
        ]
    )


def wallet_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(texts.BTN_TOPUP, callback_data="topup_start")]]
    )


def amounts_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                f"💰 {amount:,} تومان", callback_data=f"amt_{amount}"
            )
        ]
        for amount in TOPUP_PRESET_AMOUNTS
    ]
    buttons.append(
        [InlineKeyboardButton(texts.BTN_CUSTOM_AMOUNT, callback_data="amt_custom")]
    )
    buttons.append(
        [InlineKeyboardButton(texts.BTN_CANCEL_INLINE, callback_data="amt_cancel")]
    )
    return InlineKeyboardMarkup(buttons)


def topup_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(texts.BTN_CANCEL_INLINE, callback_data="topup_cancel")]]
    )
