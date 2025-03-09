
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from enum import Enum

from ..filters import ChatTypeFilter
from ..public import get_prompt_from_file

from model import Timetable
import service.class_service as service

router = Router(name="create_class")

class States(StatesGroup):
    typing_classname = State()
    creating_timetable = State()
    
class DataPart(Enum):
    name: str = "name"
    subjects: str = "subjects"

@router.message(Command("create_class"), ChatTypeFilter('private')) # а если не private ?
async def start_create_class(message: Message, state: FSMContext):
    await state.set_state(States.typing_classname)
    text = get_prompt_from_file('create_class/start_create_class.txt')
    return await message.answer(text)

@router.message(States.typing_classname)
async def creating_subject_list(message: Message, state: FSMContext):
    
    class_name = message.text
    if service.validate_class_name(class_name):
        await state.update_data({DataPart.name: class_name})
        await state.set_state(States.creating_timetable)
        text = get_prompt_from_file('create_class/create_timetable.txt')
        return await message.answer(text)
    else:
        text = get_prompt_from_file('create_class/error_class_exitst.txt')
        await state.clear()
        return await message.answer(text)

@router.message(States.creating_timetable)
async def typed_timetable(message: Message, state: FSMContext):
    await state.clear()
    try:
        timetable: Timetable = Timetable.parse(message.text)
        return await message.answer(repr(timetable))
    except:
        return await message.answer('не удалось')