
import asyncio
import time
import datetime
import logging
import sys
from typing import Any, Callable
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import TelegramObject, InlineKeyboardMarkup, Message
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import routers
from handlers.middlewares import UpdateLogerMiddleware
from logers import handle as loger
import config


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    session = AiohttpSession(proxy="http://proxy.server:3128")
    bot = Bot(token=config.TOKEN, session=session if config.IS_ON_SERVER else None,
                           default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.update.outer_middleware(UpdateLogerMiddleware())
    
    dp.include_routers(*routers)
    
    # And the run events dispatching
    await bot.send_message(1122505805, f'Я запустился ({time.ctime()})')
    print('Bot runned!')
    await dp.start_polling(bot)

# run long-polling
if __name__ == "__main__":
    
    date_string = datetime.datetime.now().strftime(r'%Y-%m-%d_%H-%M-%S')
    log_file_name = f'logs/log-{date_string}.txt'
    if config.DEBUGMODE:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.DEBUG,
            encoding='utf-8',
        )
    else:
        logging.basicConfig(
            filename=log_file_name, 
            filemode='w', 
            level=logging.INFO,
            encoding='utf-8'
            )

    asyncio.run(main())