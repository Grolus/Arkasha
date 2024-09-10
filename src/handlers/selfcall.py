
from aiogram import Router, F
from aiogram.types import Message


router = Router(name='selfcall')

@router.message( F.text.lower() == 'аркаша?')
async def selfcall(message: Message):
    await message.reply(f'Я на месте, {message.from_user.full_name}')
