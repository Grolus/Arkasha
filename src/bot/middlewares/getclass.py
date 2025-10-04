
from typing import Any, Callable
from typing_extensions import Self

from aiogram import BaseMiddleware
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import State, StatesGroup

from ..public import get_prompt_from_file

from config.constants import DEFAULT_CALLBACK_DATA_SEPARATOR
from service import class_service as service
from model import Class


def get_text(name: str) -> str:
    return get_prompt_from_file(f'get_class/{name}.txt')

# service.get_class_for_chat_id: Callable[[int], Class]
# service.get_user_classes: Callable[[User], list[Class]]
CLASSES = {}


class SetClassState(StatesGroup):
    choosing_class = State()
    
class ChoosedClassCallback(CallbackData, prefix="choosedclassforchat", sep=DEFAULT_CALLBACK_DATA_SEPARATOR):
    class_id: int
    
    @classmethod
    def from_class(cls, class_: Class) -> Self:
        class_id = hash(class_.name)
        CLASSES[class_id] = class_
        return cls(class_id=class_id)

    def get_class(self) -> Class:
        return CLASSES.pop(self.class_id)    


class GetClassMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable,
        message_or_callback: Message | CallbackQuery,
        data: dict[str: Any]
    ):
        message = message_or_callback if isinstance(message_or_callback, Message) else message_or_callback.message
        chat_id = message.chat.id
        username = message_or_callback.from_user.username

        if class_ := await service.get_class_for_chat_id(chat_id):
            data["class_"] = class_
            return await handler(message_or_callback, data)
        elif user_classes := await service.get_user_classes(username):
            await data['state'].set_state(SetClassState.choosing_class)
            return await message.answer(get_text('choose_class'), reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=class_.name, callback_data=ChoosedClassCallback.from_class(class_).pack()
                )] for class_ in user_classes
            ]))
        else:
            return await message.answer(get_text('class_not_found'))
            

