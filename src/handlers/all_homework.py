
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from .middlewares import GetClassMiddleware
from entities import Class, Homework
from utils.states import GetAllHomeworkState
from utils import Weekday, get_now_week

router = Router(name='all_homework')
router.message.middleware(GetClassMiddleware())
router.callback_query.middleware(GetClassMiddleware())

@router.message(Command('all_homework'))
async def all_homwork_request_start(message: Message, state: FSMContext, class_: Class):
    await state.set_state(GetAllHomeworkState.choosing_day)
    return await message.reply(
        'Выберите день, на который хотите получить полное дз',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=wd_string, callback_data=f'chooseddayallhw_{int(wd)}')]
            for wd, wd_string in class_.get_awaible_weekdays_strings(message.date.weekday())
        ])
    )

@router.callback_query(GetAllHomeworkState.choosing_day, F.data.startswith('chooseddayallhw_'))
async def send_homeworks_handler(callback: CallbackQuery, state: FSMContext, class_: Class):
    weekday = Weekday(int(callback.data.split('_')[1]))
    week = get_now_week(callback.message.date)
    now_weekday = Weekday(callback.message.date.weekday())
    for_next_week = int(now_weekday) > int(weekday)
    homeworks = Homework.get_all_homeworks_for_day(class_, weekday, week + for_next_week)
    hw_dict = {(hw.subject, hw.position): hw for hw in homeworks}
    awaible_subjects = list(class_.timetables[weekday])
    strings = [
        f"{i+1}. <s>{s.name}</s>" 
        if hw_dict.get((s, i+1)) is None or hw_dict[(s, i+1)].position != i+1 else hw_dict[(s, i+1)].get_small_string() 
        for i, s in enumerate(awaible_subjects)
    ]
    await state.clear()
    return await callback.message.edit_text(
        f'Задание на {weekday.accusative}{" следующей недели"}:\n\n' +
        '\n'.join(strings)
    )

