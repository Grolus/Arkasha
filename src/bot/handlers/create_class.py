
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup, any_state
from aiogram.fsm.context import FSMContext

from enum import Enum

from ..filters import ChatTypeFilter
from ..public import get_prompt_from_file
from ..parsing.timetable import parse_timetable
from ..formating.timetable import format_timetable_full
from ..keyboards import create_class as keyboards

from model import Timetable
import service.class_service as service
from exceptions import ParsingError

router = Router(name="create_class")


class CreateClassStates(StatesGroup):
    typing_classname = State()
    creating_timetable = State()
    confirming = State()
    editing_class_name = State()
    editing_timetable = State()

class DataPart(Enum):
    name: str = "name"
    timetable: str = "timetable"

@router.callback_query(*CreateClassStates.__all_states__, F.data == "cancel_class_creation")
async def cancel_class_creation(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    text = get_prompt_from_file("create_class/cancel_class_creation.txt")
    return await callback.message.edit_text(text)

@router.message(Command("create_class"), ChatTypeFilter('private')) # а если не private ?
async def start_create_class(message: Message, state: FSMContext):
    await state.set_state(CreateClassStates.typing_classname)
    text = get_prompt_from_file('create_class/start_create_class.txt')
    return await message.answer(text)

@router.message(CreateClassStates.typing_classname)
async def creating_timetable(message: Message, state: FSMContext):
    
    class_name = message.text
    if service.validate_class_name(class_name):
        await state.update_data({DataPart.name: class_name})
        await state.set_state(CreateClassStates.creating_timetable)
        text = get_prompt_from_file('create_class/create_timetable.txt')
        return await message.answer(text, reply_markup=keyboards.class_name_typed)
    else:
        text = get_prompt_from_file('create_class/error_class_exitst.txt')
        await state.clear()
        return await message.answer(text)

@router.message(CreateClassStates.creating_timetable)
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
        await state.set_state(CreateClassStates.confirming)
        return await message.answer(
            text,
            reply_markup=keyboards.confirming_created_class
        )
    except ParsingError:
        text = get_prompt_from_file('create_class/error_parsing_timetable.txt')
        return await message.answer(text)

@router.callback_query(CreateClassStates.confirming, F.data == 'edit_class_name')
async def edit_class_name(callback: CallbackQuery, state: FSMContext):
    text = get_prompt_from_file("create_class/edit_class_name.txt")
    await state.set_state(CreateClassStates.editing_class_name)
    return await callback.message.edit_text(text)

@router.callback_query(CreateClassStates.confirming, F.data == "edit_class_timetable")
async def edit_class_timetable(callback: CallbackQuery, state: FSMContext):
    text = get_prompt_from_file('create_class/edit_timetable_prompt.txt')
    await state.set_state(CreateClassStates.creating_timetable)
    return await callback.message.edit_text(text)

@router.message(CreateClassStates.editing_class_name)
async def class_name_edited(message: Message, state: FSMContext):
    class_name = message.text
    if service.validate_class_name(class_name):
        await state.update_data({DataPart.name: class_name})
        
        timetable = (await state.get_data())[DataPart.timetable]
        timetable_string = format_timetable_full(timetable)
        text = get_prompt_from_file(
            'create_class/confirm_class_creation.txt'
            ).format(
                class_name=class_name, 
                timetable_string=timetable_string
            )
        await state.set_state(CreateClassStates.confirming)
        return await message.answer(
            text,
            reply_markup=keyboards.confirming_created_class
        )
    else:
        text = get_prompt_from_file("create_class/edited_class_name_not_valid.txt")
        return await message.answer(text)

@router.callback_query(CreateClassStates.confirming, F.data == 'confirmed_class')
async def confirm_class_creation(callback: CallbackQuery, state: FSMContext):
    
    # save new class
    data = await state.get_data()
    name = data[DataPart.name]
    creator_username = callback.from_user.username
    creator_fullname = callback.from_user.full_name
    timetable = data[DataPart.timetable]
    service.save_new_class(name, creator_username, creator_fullname, timetable)
    
    text = get_prompt_from_file(
        "create_class/class_confirmed.txt"
    ).format(
        class_name=name,
        creator_username=creator_username
    )
    return await callback.message.edit_text(
        text
    )