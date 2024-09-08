
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from ..middlewares import GetClassMiddleware
from entities import Class, Subject, Homework
from utils import allocate_values_to_nested_list, Weekday, get_now_week
from utils.states import GetHomeworkState
from utils.strings import slot_to_callback, slot_to_string, callback_to_slot
from parsers import parse_one_subject
from exceptions import ValueNotFoundError


# TODO inline kb include allk subjects (via pages)

router = Router(name='get_homework')
router.message.middleware(GetClassMiddleware())
router.callback_query.middleware(GetClassMiddleware())


@router.message(Command('get_homework'))
async def get_homework_start(message: Message, state: FSMContext, class_: Class):
    probably_subjects = list(class_.timetables[Weekday(message.date.weekday())])
    await state.set_state(GetHomeworkState.choosing_subject)
    return await message.reply(
        'Выберте предмет, по которому хотите получить дз, или напишите его название',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=allocate_values_to_nested_list([
            InlineKeyboardButton(text=sj.name, callback_data=f'choosedsubjectgethw_{sj.encode()}') 
            for sj in probably_subjects
            ], 3
        ))
    )

@router.callback_query(GetHomeworkState.choosing_subject, F.data.startswith('choosedsubjectgethw_'))
@router.message(GetHomeworkState.choosing_subject)
async def choosed_subject_handler(message_or_callback: Message | CallbackQuery, state: FSMContext, class_: Class):
    if isinstance(message_or_callback, Message):
        choosed_subject = parse_one_subject(message_or_callback.text, class_.subjects)
        now_weekday = message_or_callback.date.weekday()
    else:
        choosed_subject = Subject.decode(message_or_callback.data.split('_')[1])
        now_weekday = message_or_callback.message.date.weekday()
    awaible_slots = class_.get_awaible_subject_slots(choosed_subject, now_weekday)
    await state.set_state(GetHomeworkState.choosing_slot)
    await state.set_data({'subject': choosed_subject})
    return await (
        message_or_callback.reply 
        if isinstance(message_or_callback, Message) 
        else message_or_callback.message.edit_text
        )(
            'Выберите день',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=slot_to_string(slot), callback_data=slot_to_callback(slot, 'choosedslotgethw'))]
                for slot in awaible_slots
            ])
        )

@router.callback_query(GetHomeworkState.choosing_slot, F.data.startswith('choosedslotgethw_'))
async def send_homework_handler(callback: CallbackQuery, state: FSMContext, class_: Class):
    weekday, position, is_for_next_week = callback_to_slot(callback.data)
    now_week = get_now_week(callback.message.date)
    subject = (await state.get_data())['subject']
    await state.clear()
    try:
        got_homework = Homework.get(class_, subject, weekday, now_week+is_for_next_week, position, callback.message.date.year)
        return await callback.message.edit_text(
            str(got_homework)
        )
    except ValueNotFoundError:
        recent_homeworks = Homework.get_recent(subject, class_)
        await state.set_data({'recent_homeworks': recent_homeworks})
        if recent_homeworks:
            return await callback.message.edit_text(
                f'К сожалению, задание по <i>{subject.name}</i> не было сохранено на '
                f'{weekday.accusative}{" следующей недели" if is_for_next_week else ""}. '
                'Вот другие задания по этому предмету (если нужно)',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=slot_to_string(hw.slot(now_week)), 
                        callback_data=f'extragethwchoosedhw_{i}' # TODO !!
                    )]
                    for i, hw in enumerate(recent_homeworks)
                ])
            )
        else:
            return await callback.message.edit_text(
                f'К сожалению, задание по <i>{subject.name}</i> не было сохранено на '
                f'{weekday.accusative}{" следующей недели" if is_for_next_week else ""}. '
            )

@extra_router.callback_query(F.data.startswith('extragethwchoosedhw_'))
async def extra_homework_handler(callback: CallbackQuery, state: FSMContext):
    hw_index = int(callback.data.split('_')[1])
    homework = (await state.get_data())['recent_homeworks'][hw_index]
    await state.clear()
    text = str(homework)
    print(text)
    return await callback.message.edit_text(text)


