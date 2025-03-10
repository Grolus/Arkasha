
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from enum import Enum

from ..filters import ChatTypeFilter
from ..public import get_prompt_from_file
from ..parsing.timetable import parse_timetable
from ..formating.timetable import format_timetable_full

from model import Timetable
import service.class_service as service
from exceptions import ParsingError

router = Router(name="create_class")

class States(StatesGroup):
    typing_classname = State()
    creating_timetable = State()
    
class DataPart(Enum):
    name: str = "name"
    timetable: str = "timetable"

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
    try:
        # parsing
        timetable: Timetable = parse_timetable(message.text)

        # saving new data
        await state.update_data({DataPart.timetable: timetable})

        # данные для ответа
        class_name = (await state.get_data())[DataPart.name]
        timetable_string = format_timetable_full(timetable)

        text = get_prompt_from_file(
            'create_class/confirm_class_creation.txt'
            ).format(
                class_name=class_name, 
                timetable_string=timetable_string
            )

        return await message.answer(text)
    except ParsingError:
        return await message.answer('не удалось')