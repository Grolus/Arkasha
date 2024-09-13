
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from ..middlewares import GetClassMiddleware
from entities import Class, Homework
from utils.states import GetAllHomeworkState
from utils import Weekday, get_now_week

router = Router(name='all_homework')
router.message.middleware(GetClassMiddleware())
router.callback_query.middleware(GetClassMiddleware())


def homeworks_to_string(homeworks: list[Homework]):
    final_string = ''
    homeworks.sort(key=lambda x: x.position * 10 + x.group_number)
    handled_positions = []
    for hw in homeworks:
        if hw.position in handled_positions:
            final_string += f'    <b>{hw.subject}</b>: <i>{hw.text}</i>' + '\n'
        else:
            final_string += f'{hw.position}. <b>{hw.subject}</b>: <i>{hw.text}</i>' + '\n'
            handled_positions.append(hw.position)
    return final_string


@router.message(Command('all_homework'))
async def all_homwork_request_start(message: Message, state: FSMContext, class_: Class, weekday: Weekday):
    await state.set_state(GetAllHomeworkState.choosing_day)
    return await message.reply(
        'Выберите день, на который хотите получить полное дз',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=wd_string, callback_data=f'chooseddayallhw_{int(wd)}')]
            for wd, wd_string in class_.get_awaible_weekdays_strings(weekday)
        ])
    )

@router.callback_query(GetAllHomeworkState.choosing_day, F.data.startswith('chooseddayallhw_'))
async def send_homeworks_handler(callback: CallbackQuery, state: FSMContext, class_: Class, week: int, weekday: Weekday):
    weekday_to_load = Weekday(int(callback.data.split('_')[1]))
    for_next_week = int(weekday) > int(weekday_to_load)
    homeworks = Homework.get_all_homeworks_for_day(class_, weekday, week + for_next_week)
    homeworks_string = homeworks_to_string(homeworks)
    await state.clear()
    return await callback.message.edit_text(
        f'Задания на {weekday.accusative}{" следующей недели"}:\n\n' +
        homeworks_string
    )

