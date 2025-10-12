
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command

from ..middlewares import GetClassMiddleware
from ..public import get_prompt_from_file
from ..string import format_relative_weekday_string, format_all_homeworks_list_string
from ..callback_data.get_all_homework import WeekdayCallback

from model import Class, Homework, WWDate, DailyTimetable, Weekday, Subject, Lesson, WWDateDelta
from service import homework_service as service


class GetAllHomeworkState(StatesGroup):
    choosing_day = State()

router = Router(name='all_homework')
router.message.middleware(GetClassMiddleware())
router.callback_query.middleware(GetClassMiddleware())


def get_text(name: str) -> str:
    return get_prompt_from_file(f'all_homework/{name}.txt')


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



def associate_homeworks_with_timetable(homeworks: list[Homework], timetable: DailyTimetable) -> dict[tuple[int, Subject, int]: Homework | None]:
    result_dict = {}
    homework_by_pos_subject_and_group = {}
    for hw in homeworks:
        homework_by_pos_subject_and_group[(hw.position, hw.subject, hw.group_number)] = hw
    for position, lesson in enumerate(timetable):
        for group, subject in lesson.subjects.items():
            result_dict[(position, subject, group)] = homework_by_pos_subject_and_group.get((position, subject, group))
    return result_dict

def homeworks_dict_to_string(homeworks_dict: dict[tuple[int, Subject, int]: Homework | None]) -> str:
    sorted_keys = sorted(homeworks_dict.keys(), key=lambda x: x[0]*10 + x[2])
    string = ''
    for key in sorted_keys:
        if key[1] is None:
            string += Homework.get_small_string_for_empty_homework(*key, strike=False)
        
        if hw := homeworks_dict.get(key):
            string += hw.get_small_string()
        else:
            string += Homework.get_small_string_for_empty_homework(*key)
        
        string += '\n'
    return string



@router.message(Command('all_homework'))
async def all_homework_request_start(message: Message, state: FSMContext, class_: Class, wwdate: WWDate):
    await state.set_state(GetAllHomeworkState.choosing_day)
    return await message.reply(
        get_text('choose_day'),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=format_relative_weekday_string(weekday, wwdate.weekday).capitalize(), callback_data=WeekdayCallback(weekday_number=int(weekday)).pack())]
            for weekday in class_.timetable.timetable_dict.keys()
        ])
    )

@router.callback_query(GetAllHomeworkState.choosing_day, WeekdayCallback.filter())
async def send_homeworks_handler(callback: CallbackQuery, state: FSMContext, class_: Class, wwdate: WWDate):
    weekday_to_load = Weekday(WeekdayCallback.unpack(callback.data).weekday_number)
    for_next_week = int(wwdate.weekday) > int(weekday_to_load)
    if for_next_week:
        day_delta = 7 - int(wwdate.weekday) + int(weekday_to_load)
    else:
        day_delta = int(weekday_to_load) - int(wwdate.weekday)
    wwdate_to_load = wwdate.add_days(day_delta)
    homeworks: list[Homework] = await service.get_all_homeworks_for_day(class_, wwdate_to_load) 

    # timetable = class_.timetable.timetable_dict[weekday_to_load]
    # homeworks_dict = associate_homeworks_with_timetable(homeworks, timetable)
    # homeworks_string = homeworks_dict_to_string(homeworks_dict)
    await state.clear()
    return await callback.message.edit_text(
        f'Задания на {format_relative_weekday_string(weekday_to_load, wwdate.weekday, case="genetive")}:\n\n' +
        format_all_homeworks_list_string(homeworks)
    )

