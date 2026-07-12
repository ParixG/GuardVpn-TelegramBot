import asyncio
import logging

import bridge
from admin_bot.bot import build_admin_app
from user_bot.bot import build_user_app

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main() -> None:
    user_app = build_user_app()
    admin_app = build_admin_app()

    bridge.user_bot = user_app.bot
    bridge.admin_bot = admin_app.bot

    await user_app.initialize()
    await user_app.start()
    await admin_app.initialize()
    await admin_app.start()

    try:
        await asyncio.gather(
            user_app.updater.start_polling(drop_pending_updates=True),
            admin_app.updater.start_polling(drop_pending_updates=True),
        )
        logger.info("Both bots are polling.")
        await asyncio.Event().wait()
    finally:
        await user_app.updater.stop()
        await admin_app.updater.stop()
        await user_app.stop()
        await admin_app.stop()
        await user_app.shutdown()
        await admin_app.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutting down.")
