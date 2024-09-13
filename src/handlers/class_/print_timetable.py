from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message


from ..middlewares import GetClassMiddleware

router = Router(name='print_timetable')
router.message.middleware(GetClassMiddleware())

@router.message(Command('print_timetable'))
async def timetable_printing(message: Message, state, class_):
    timetables_string = class_.print_timetables()
    await message.answer(
        timetables_string
    )
