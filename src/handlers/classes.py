from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

router = Router()



@router.message(Command('classes'))
def show_classes(message: Message):
    ...
