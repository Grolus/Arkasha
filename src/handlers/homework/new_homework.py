
from typing import Callable, Any
import datetime

from aiogram import Router, F, BaseMiddleware
from aiogram.types import Message, TelegramObject, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendMessage

from .middlewares import GetClassMiddleware
from exceptions import ValueNotFoundError
from storage.tables import ChatTable, AdministratorTable, HomeworkTable
from entities import Class, Subject, Homework
from utils.states import HomeworkSettingState
from utils import Weekday, allocate_values_to_nested_list, get_now_week
from parsers import parse_subjects, parse_one_subject
from utils.strings import slot_to_callback, slot_to_string, callback_to_slot


# TODO inline kb include allk subjects (via pages)


router = Router()
router.message.middleware(GetClassMiddleware())
router.callback_query.middleware(GetClassMiddleware())

@router.message(Command('new_homework'))
async def start_new_homework(message: Message, state: FSMContext, class_: Class):
    await state.set_state(HomeworkSettingState.typing_homework)
    return await message.reply(
        f'Введите дз, которое хотите сохранить, не забыв указать предмет (где угодно в сообщении)'
    )

@router.message(HomeworkSettingState.typing_homework)
async def handle_homework_text(message: Message, state: FSMContext, class_: Class):
    raw_text = message.text
    subjects = parse_subjects(raw_text, class_.subjects)
    hw_text = raw_text
    await state.set_data({"text": hw_text})
    await state.set_state(HomeworkSettingState.choosing_subject)
    return await message.reply(
        f'<b>{message.from_user.full_name}</b>, выберите предмет для сохранения задания\n<i>{hw_text}</i>\n'
        '\nЕсли предмета нет в списке, напишите его название',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=allocate_values_to_nested_list([
            InlineKeyboardButton(text=sj.name, callback_data=f'choosedsubjectnewhw_{sj.encode()}')
            for sj in subjects
        ], 3))
    )

@router.message(HomeworkSettingState.choosing_subject)
@router.callback_query(HomeworkSettingState.choosing_subject, F.data.startswith('choosedsubjectnewhw_'))
async def choose_subject_for_new_hw(callback_or_message: CallbackQuery | Message, state: FSMContext, class_: Class, weekday: Weekday):

    if isinstance(callback_or_message, CallbackQuery):
        choosed_subject = Subject.decode(callback_or_message.data.split('_')[1])
    else:
        choosed_subject = parse_one_subject(callback_or_message.text, class_.subjects)
    awaible_subject_slots = class_.get_awaible_subject_slots(choosed_subject, weekday)
    await state.update_data({"subject": choosed_subject})
    await state.set_state(HomeworkSettingState.choosing_weekday)
    return await (
        callback_or_message.message.edit_text 
        if isinstance(callback_or_message, CallbackQuery) 
        else callback_or_message.reply
        )(
        f'На какой день сохранить задание по <i>{choosed_subject.name}</i>?',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=allocate_values_to_nested_list([
            InlineKeyboardButton(text=slot_to_string(slot), callback_data=slot_to_callback(slot, 'choosedweekdaynewhw'))
            for slot in awaible_subject_slots
        ], 1))
    )
    
@router.callback_query(HomeworkSettingState.choosing_weekday, F.data.startswith('choosedweekdaynewhw_'))
async def choosed_weekday_handler(callback: CallbackQuery, state: FSMContext, class_: Class, week: int):
    weekday, position, is_for_next_week = callback_to_slot(callback.data)
    collected_data = await state.get_data()
    collected_homework = Homework(
        collected_data['subject'],
        class_,
        collected_data['text'],
        weekday,
        week + is_for_next_week,
        position,
        callback.message.date.year
    )
    HomeworkTable.save_new_homework(collected_homework)
    await state.clear()
    return await callback.message.edit_text(
        f'Сохранил задание по предмету {collected_homework.subject} на '
        f'{collected_homework.weekday.accusative}{" следующей недели" if is_for_next_week else ""}.'
    )


