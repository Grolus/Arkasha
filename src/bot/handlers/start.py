from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from ..public import get_prompt_from_file

router = Router(name="start")

@router.message(Command("start"))
async def start_handler(message: Message):
    text = get_prompt_from_file("start.txt")
    return await message.answer(text)

@router.message(Command("help"))
async def start_handler(message: Message):
    text = get_prompt_from_file("help.txt")
    return await message.answer(text)
