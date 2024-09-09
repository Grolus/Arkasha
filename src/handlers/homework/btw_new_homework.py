from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from ..middlewares import GetClassMiddleware
from parsers import is_subject_word
from entities import Class, Homework, Subject
from entities.homework import is_position_needed
from utils import Weekday
from utils.strings import slot_to_string, slot_to_callback, callback_to_slot
from utils.states import BtwNewHomeworkState

router = Router(name='btw_new_homework')
router.message.middleware(GetClassMiddleware())
router.callback_query.middleware(GetClassMiddleware())

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

def sort_slots(slots: list[tuple[Weekday, int, bool]]):
    slots.sort(key=lambda t: int(t[0])*10+t[1] + t[2]*100)
# По биологии читать параграф 2, рис. 5, творческая работа

def format_answer_got_homework(homework: Homework, posttext: str | None=None, slot_to_save: tuple | None=None) -> str:
    end_text = posttext or (f'Сохранить на {slot_to_string(slot_to_save, case="accusative", title=False)}?' if slot_to_save else '')
    return f'Получено задание по предмету <b>{homework.subject}</b>:\n<i>{homework.text}</i>\n\n{end_text}'

@router.message(F.text.regexp(r'[Пп][Оо] [А-Яа-я]* .*'))
async def btw_new_homework_found(message: Message, state: FSMContext, class_: Class, week: int, weekday: Weekday):
    expected_subject_word = message.text.split()[1]
    if subject := is_subject_word(expected_subject_word, class_.subjects):
        hw_text = ' '.join(message.text.split()[2:])
        slot = get_closest_slot(class_, subject, weekday)
        hw_weekday, hw_pos, is_for_next_week = slot
        collected_homework = Homework(subject, class_, hw_text, hw_weekday, week + is_for_next_week, hw_pos)
        await state.set_data({'collected_homework': collected_homework})
        await state.set_state(BtwNewHomeworkState.typed_homework)
        return await message.reply(
            format_answer_got_homework(collected_homework, slot_to_save=slot),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Сохранить', callback_data='btwnewhw_confirmed')],
                [InlineKeyboardButton(text='Выбрать другой день ➡️', callback_data='btwnewhw_another')]
            ])
        )

@router.callback_query(BtwNewHomeworkState.typed_homework, F.data == 'btwnewhw_confirmed')
async def save_new_homework(callback: CallbackQuery, state: FSMContext, class_: Class):
    collected_homework: Homework = (await state.get_data())['collected_homework']
    collected_homework.save()
    await state.clear()
    return await callback.message.edit_text(
        f'Сохранил задание по <b>{collected_homework.subject}</b>:\n<i>{collected_homework.text}</i>\n\nСпасибо, {callback.from_user.full_name}'
    )
    
@router.callback_query(BtwNewHomeworkState.typed_homework, F.data == 'btwnewhw_another')
async def choose_another_slot(callback: CallbackQuery, state: FSMContext, class_: Class, weekday: Weekday, week: int):
    collected_homework: Homework = (await state.get_data())['collected_homework']
    slots = class_.get_awaible_subject_slots(collected_homework.subject, weekday)
    sort_slots(slots)
    await state.set_state(BtwNewHomeworkState.choosing_slot)
    return await callback.message.edit_text(
        format_answer_got_homework(collected_homework, posttext='Выберите день для сохранения'),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=slot_to_string(slot), callback_data=slot_to_callback(slot, 'btwhwsetslotchoosed'))]
            for slot in slots
        ])
    )

@router.callback_query(BtwNewHomeworkState.choosing_slot, F.data.startswith('btwhwsetslotchoosed'))
async def slot_choosed(callback: CallbackQuery, state: FSMContext, class_: Class):
    slot = callback_to_slot(callback.data)
    hw_weekday, hw_pos, is_for_next_week = slot
    collected_homework: Homework = (await state.get_data())['collected_homework']
    collected_homework.change_slot(slot)
    await state.set_state(BtwNewHomeworkState.typed_homework)
    return await callback.message.edit_text(
        format_answer_got_homework(collected_homework, slot_to_save=slot),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Сохранить', callback_data='btwnewhw_confirmed')],
            [InlineKeyboardButton(text='Выбрать другой день ➡️', callback_data='btwnewhw_another')]
        ])
    )



