
import asyncio
import time
import datetime
import logging
from typing import Any, Callable
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import routers
from logers import handle as loger
import config

class MessageLogerMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable,
            event: TelegramObject,
            data: dict[str: Any]):
        if event.message:
            loger.info(f' [MESSAGE] {event.message.from_user.full_name} ({event.message.from_user.username}) >>> {event.message.text}')
        elif event.callback_query:
            loger.info(f' [CALLBACK] {event.callback_query.from_user.full_name} ({event.callback_query.from_user.username}) => {event.callback_query.data}')
        return await handler(event, data)


async def main() -> None:
    # Initialize Bot instance with a default parse mode which will be passed to all API calls
    session = AiohttpSession(proxy="http://proxy.server:3128")
    bot = Bot(token=config.TOKEN, session=session if config.IS_ON_SERVER else None,
                           default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.update.outer_middleware(MessageLogerMiddleware())
    
    dp.include_routers(*routers)
    
    # And the run events dispatching
    await bot.send_message(1122505805, f'Я запустился ({time.ctime()})')
    print('Bot runned!')
    await dp.start_polling(bot)

# run long-polling
if __name__ == "__main__":
    
    date_string = datetime.datetime.now().strftime(r'%Y-%m-%d_%H-%M-%S')
    log_file_name = f'logs/log-{date_string}.txt'
    logging.basicConfig(
        filename=log_file_name, 
        filemode='w', 
        level=logging.DEBUG if config.DEBUGMODE else logging.INFO,
        encoding='utf-8'
        )

    asyncio.run(main())