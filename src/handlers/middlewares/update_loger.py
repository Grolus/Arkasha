
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, InlineKeyboardMarkup, Update

from logers import handle as loger

DEFAULT_SEPARATOR = ' > '
SEPARATORS = {
    'message': '>>>',
    'callback_query': '=>',
    'inline_query': '...'
}

def get_information(update: Update):
    match update.event_type:
        case 'message':
            return update.message.text
        case 'callback_query':
            return update.callback_query.data
        case 'inline_query':
            return update.inline_query.query
        case _:
            return update.model_dump_json()

class UpdateLogerMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable,
            event: Update,
            data: dict[str: Any]):
        event_type = event.event_type
        separator = SEPARATORS.get(event_type, DEFAULT_SEPARATOR)
        information = get_information(event)
        user_string = '<no user>'
        if event.from_user:
            user_string = f'{event.message.from_user.full_name} (@{event.message.from_user.username})'
        loger.info(f' [{event_type.capitalize()}] {user_string} {separator} {information}')
        result = await handler(event, data)
        if isinstance(result, Message):
            loger.info(f' <<< {result.text}' + (' <with keyboard>' if isinstance(result.reply_markup, InlineKeyboardMarkup) else ''))
        return result