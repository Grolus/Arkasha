from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from ..public import load_file

router = Router(name="start")

@router.message(Command("start"))
async def start_handler(message: Message):
    text = load_file("start.txt")
    return await message.answer(text)

@router.message(Command("help"))
async def start_handler(message: Message):
    text = load_file("help.txt")
    return await message.answer(text)
