
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
from utils import Weekday, allocate_values_to_nested_list, parse_subjects, parse_one_subject, get_now_week


router = Router()
router.message.middleware(GetClassMiddleware())
router.callback_query.middleware(GetClassMiddleware())

def _slot_to_string(slot: tuple[Weekday, int, bool]):
    weekday, position, is_for_next_week = slot
    return weekday.name.title() + (" следующей недели" if is_for_next_week else "") + f", {position} урок"

def _slot_to_callback(slot: tuple[Weekday, int, bool]):
    return f'choosedweekdaynewhw_{int(slot[0])}_{slot[1]}_{int(slot[2])}'

def _callback_to_slot(callback_data: str) -> tuple[Weekday, int, bool]:
    _, weekday, pos, is_next_week = callback_data.split('_')
    return int(weekday), int(pos), bool(int(is_next_week))


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
async def choose_subject_for_new_hw(callback_or_message: CallbackQuery | Message, state: FSMContext, class_: Class):

    if isinstance(callback_or_message, CallbackQuery):
        choosed_subject = Subject.decode(callback_or_message.data.split('_')[1])
        now_datetime = callback_or_message.message.date
    else:
        choosed_subject = parse_one_subject(callback_or_message.text, class_.subjects)
        now_datetime = callback_or_message.date
    now_weekday = now_datetime.weekday()
    awaible_subject_slots = class_.get_awaible_subject_slots(choosed_subject, now_weekday)
    await state.update_data({"subject": choosed_subject})
    await state.set_state(HomeworkSettingState.choosing_weekday)
    return await (
        callback_or_message.message.edit_text 
        if isinstance(callback_or_message, CallbackQuery) 
        else callback_or_message.reply
        )(
        f'На какой день сохранить задание по <i>{choosed_subject.name}</i>?',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=allocate_values_to_nested_list([
            InlineKeyboardButton(text=_slot_to_string(slot), callback_data=_slot_to_callback(slot))
            for slot in awaible_subject_slots
        ], 1))
    )
    
@router.callback_query(HomeworkSettingState.choosing_weekday, F.data.startswith('choosedweekdaynewhw_'))
async def choosed_weekday_handler(callback: CallbackQuery, state: FSMContext, class_: Class):
    weekday, position, is_for_next_week = _callback_to_slot(callback.data)
    datetime_of_message = callback.message.date
    now_week = get_now_week(datetime_of_message)
    collected_data = await state.get_data()
    collected_homework = Homework(
        collected_data['subject'],
        class_,
        collected_data['text'],
        Weekday(weekday),
        now_week + is_for_next_week,
        position,
        datetime_of_message.year
    )
    HomeworkTable.save_new_homework(collected_homework)
    await state.clear()
    return await callback.message.edit_text(
        f'Сохранил задание по предмету {collected_homework.subject} на '
        f'{collected_homework.weekday.accusative}{" следующей недели" if is_for_next_week else ""}.'
    )


