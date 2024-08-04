
from typing import Any, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from entities import Class
from storage.tables import ChatTable, AdministratorTable
from exceptions import ValueNotFoundError
from utils.states import SetClassState

def get_class(chat_id, username) -> Class | list[Class] | None:
    try: 
        class_ = ChatTable.get_by_unique_column(chat_id).values.classID
        return Class.from_table_value(class_)
    except ValueNotFoundError:
        if classes := AdministratorTable(username).get_classes():
            return [Class.from_table_value(i) for i in classes]


class GetClassMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable,
        message_or_callback: Message | CallbackQuery,
        data: dict[str: Any]
    ):
        _message = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
        got_class = get_class(_message.chat.id, message_or_callback.from_user.username)
        if isinstance(got_class, Class):
            data['class_'] = got_class
        elif isinstance(got_class, list):
            await data['state'].set_state(SetClassState.choosing_class)
            await _message.answer('Сначала выберите класс', reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=class_.name, callback_data=f'choosedclassforchat_{class_.connected_table_value.id_}'
                )] for class_ in got_class
            ]))
            return
        elif got_class is None:
            await _message.answer('Для данного чата не выбран класс. Пусть создатель напишет /setclass')
            return 
        return await handler(message_or_callback, data)

