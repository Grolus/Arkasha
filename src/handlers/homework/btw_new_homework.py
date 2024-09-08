from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from ..middlewares import GetClassMiddleware
from parsers import is_subject_word
from entities import Class, Homework, Subject
from entities.homework import is_position_needed
from utils import Weekday
from utils.strings import slot_to_string
from utils.states import BtwNewHomeworkState

router = Router(name='btw_new_homework')
router.message.middleware(GetClassMiddleware)

def get_closest_slot(class_: Class, subject: Subject, now_weekday: Weekday):
    weekday_to_expect = class_.weekday_delta(now_weekday, 1)
    while weekday_to_expect != now_weekday:
        if subject in class_.timetables[weekday_to_expect]:
            closest_weekday = weekday_to_expect
            break
        weekday_to_expect = class_.weekday_delta(weekday_to_expect, 1)
    else:
        closest_weekday = now_weekday
    closest_pos = class_.timetables[closest_weekday].position(subject)
    is_for_next_week = now_weekday >= closest_weekday
    closest_slot = (closest_weekday, closest_pos, is_for_next_week)
    return closest_slot
    
# По биологии читать параграф 2, рис. 5, творческая работа

@router.message(F.text.regexp(r'(?i)по /w* .*'))
async def btw_new_homework_found(message: Message, state: FSMContext, class_: Class, week: int, weekday: Weekday):
    expected_subject_word = message.text.split()[1]
    if subject := is_subject_word(expected_subject_word, class_.subjects):
        hw_text = ' '.join(message.text.split()[2:])
        position_needed = is_position_needed(class_, subject, weekday)
        if not position_needed:
            collected_homework = Homework(subject, class_, hw_text, weekday, week)
            slot = get_closest_slot(class_, subject, weekday)
            state.set_data({'collected_homework': collected_homework})
            state.set_state(BtwNewHomeworkState.choosing_another_slot)
            return await message.reply(
                f'Получено задание по предмету <b>{subject}</b>:\n<i>{hw_text}</i>\n\nСохранить на {slot_to_string(slot)}?',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text='Сохранить', callback_data='btwnewhw_confirmed')],
                    [InlineKeyboardButton(text='Выбрать другой урок ➡️', callback_data='btwnewhw_another')]
                ]))
        else:

            return await message.reply('Выберите')
    ...


