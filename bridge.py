"""Two-way bridge between the user bot and the admin bot.

main.py wires `user_bot` and `admin_bot` after both Applications are built.
The admin bot DMs customers through `user_bot`; the user bot delivers
top-up receipts to admins through `admin_bot` (file_ids are bot-scoped,
so each side must send with its own token).
"""
from telegram import Bot
from telegram.error import TelegramError

user_bot: Bot | None = None
admin_bot: Bot | None = None


async def notify_user(telegram_id: int, text: str) -> bool:
    if user_bot is None:
        return False
    try:
        await user_bot.send_message(telegram_id, text)
        return True
    except TelegramError:
        return False
