
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, InlineKeyboardMarkup

from logers import handle as loger

class UpdateLogerMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable,
            event: TelegramObject,
            data: dict[str: Any]):
        if event.message:
            loger.info(f' [MESSAGE] {event.message.from_user.full_name} ({event.message.from_user.username}) >>> {event.message.text}')
        elif event.callback_query:
            loger.info(f' [CALLBACK] {event.callback_query.from_user.full_name} ({event.callback_query.from_user.username}) => {event.callback_query.data}')
        elif event.inline_query:
            loger.info(f' [INLINE] {event.inline_query.from_user.full_name} ({event.inline_query.from_user.username})... {event.inline_query.query}')
        else:
            loger.info(f' [UPDATE] {event.model_dump_json()}')
        result = await handler(event, data)
        if isinstance(result, Message):
            loger.info(f' <<< {result.text}' + (' <with keyboard>' if isinstance(result.reply_markup, InlineKeyboardMarkup) else ''))
        return result