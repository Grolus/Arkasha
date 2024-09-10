from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command


router = Router(name='cancel')

@router.message(Command('cancel'))
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    return await message.reply('Отменил')
