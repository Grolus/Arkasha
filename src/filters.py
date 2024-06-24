

from aiogram.filters import BaseFilter
from aiogram.types import Message

class ChatTypeFilter(BaseFilter):
    def __init__(self, *chat_types: str):
        self.chat_types = chat_types
    async def __call__(self, message: Message):
        return message.chat.type in self.chat_types
            
