from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

import logging
import sys
import asyncio
import time

from config.settings import settings
from config.constants import DEBUG_TELEGRAM_CHAT_ID
from bot.handlers import routers
from bot.middlewares import UpdateLogerMiddleware, GetWeekAndWeekdayMiddleware


async def main():
    bot = Bot(
        token=settings.BOT_TOKEN,
        session=AiohttpSession(proxy="http://proxy.server:3128") if settings.USE_PROXY else None,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.include_routers(*routers)
    dp.update.outer_middleware(UpdateLogerMiddleware())
    dp.update.outer_middleware(GetWeekAndWeekdayMiddleware())
    await bot.send_message(DEBUG_TELEGRAM_CHAT_ID, f'Я запустился ({time.ctime()})')
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, 
        format="[%(levelname)s:%(name)s] %(asctime)s %(message)s", 
        datefmt="%y-%m-%d %H:%M:%S",
        stream=sys.stdout
    )
    asyncio.run(main())

