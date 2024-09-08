
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

def get_information_and_user(update: Update) -> tuple[str, str, str]:
    match update.event_type:
        case 'message':
            return update.message.text, update.message.from_user.full_name, update.message.from_user.username
        case 'callback_query':
            return update.callback_query.data, update.callback_query.from_user.full_name, update.callback_query.from_user.username
        case 'inline_query':
            return update.inline_query.query, update.inline_query.from_user.fullname, update.inline_query.from_user.username
        case _:
            return update.model_dump_json(), '<no name>', '<no username>'

class UpdateLogerMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable,
            event: Update,
            data: dict[str: Any]):
        event_type = event.event_type
        separator = SEPARATORS.get(event_type, DEFAULT_SEPARATOR)
        information, full_name, username = get_information_and_user(event)
        user_string = f'{full_name} (@{username})'
        loger.info(f' [{event_type.upper()}] {user_string} {separator} {information}')
        result = await handler(event, data)
        if isinstance(result, Message):
            loger.info(f' {user_string} <<< {result.text}' + (' <with keyboard>' if isinstance(result.reply_markup, InlineKeyboardMarkup) else ''))
        return result