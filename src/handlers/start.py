from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from filters import ChatTypeFilter

router = Router()

@router.message(
    CommandStart(), 
    ChatTypeFilter('private')
)
async def start(message: Message):
    await message.answer(
'''Привет, я <b>Аркаша</b> - бот для <u>облегчения</u> вашей школьной жизни.

Я умею: 
    сохранять и рассказывать домашнее задание

Для начала работы вам следует настроить бота под свой класс (/configure)
                         '''
)