
from aiogram.filters import BaseFilter
from aiogram.types import Message

class ChatTypeFilter(BaseFilter):
    def __init__(self, *chat_types: str):
        """Принимает любые из строк: `'private'`, `'group'`, `'supergroup'`, `'channel'`"""
        self.chat_types = chat_types
    async def __call__(self, message: Message):
        return message.chat.type in self.chat_types