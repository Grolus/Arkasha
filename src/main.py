from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import logging
import sys
import asyncio
import time

from config.settings import settings
from config.constants import DEBUG_TELEGRAM_CHAT_ID
from bot.handlers import routers



async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.include_routers(*routers)
    await bot.send_message(DEBUG_TELEGRAM_CHAT_ID, f'Я запустился ({time.ctime()})')
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, 
        format="%(asctime)s [%(levelname)s] %(message)s", 
        stream=sys.stdout
    )
    asyncio.run(main())

