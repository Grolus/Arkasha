from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from enum import Enum

from filters import ChatTypeFilter
from entities import Subject, TimetableBuilder
from entities.subject import DEFAULT_SUBJECTS
from storage.tables import AdministratorTable, ClassTable
from parsers import parse_weekdays
from utils.states import ConfigureState
from utils.keyboards import ConfigureInlineKeyboardMarkup as InlineMarkup
from utils.strings import (format_answer_changed_subject_list, 
                           format_answer_start_configure,
                           format_answer_timtable_making)
from utils.handler_factory import ChangingSubjectListHandlerFactory


__all__ = ('router')


ENTER = '\n'

router = Router(name='create_configuration')
router.message.filter(ChatTypeFilter('private'))



# TODO cancel button

# TODO /configure [args] (ex. another username)


def _get_user_classes(username: str):
    return AdministratorTable(username).get_classes()

def _save_new_class(data: dict):
    ClassTable.save_new_configuration(
        data[_StateData.classname],
        data[_StateData.creator],
        data[_StateData.subjects],
        data[_StateData.timetable_builder].to_dict()
    )

class _StateData(Enum):
    classname = 'classname'
    creator = 'creator'
    weekdays = 'weekdays'
    subjects = 'subjects'
    subject_groups = 'subject_groups'
    lessons_amount = 'lessons_amount'
    timetable_builder = 'timetable_builder'
    



@router.message(Command('configure'), StateFilter(None))
async def start_configure(message: Message, state: FSMContext):
    if existed_users_classes := _get_user_classes(message.from_user.username):
        await state.set_state(ConfigureState.edit_or_new_class_choosing)
        return await message.answer(
            format_answer_start_configure(len(existed_users_classes)),
            reply_markup=InlineMarkup.get_edit_or_new_cfg_choosing_markup(existed_users_classes)
        )
    else:
        await state.set_state(ConfigureState.typing_class_name)
        return await message.answer(
            'Вы начали конфигурацию нового класса! Для начала придумайте '
            'уникальное имя для вашего нового класса. Например, "1А 1 школа"'
        )
        
@router.callback_query(F.data == 'newcfgbegin', ConfigureState.edit_or_new_class_choosing)
async def start_new_class(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ConfigureState.typing_class_name)
    return await callback.message.edit_text(
        'Вы начали конфигурацию нового класса! '
        'Для начала придумайте уникальное имя для вашего нового класса. Например, "1А 1 школа"'
    )

@router.message(ConfigureState.typing_class_name, F.text)
async def typed_class_name(message: Message, state: FSMContext):
    classname = message.text
    if ClassTable.is_valid_name(classname):
        await state.set_data({
            _StateData.classname: classname,
            _StateData.creator: message.from_user.username,
            _StateData.subjects: DEFAULT_SUBJECTS.copy(),
            _StateData.subject_groups: {}
        })
        await state.set_state(ConfigureState.choosing_days_of_study)
        return await message.answer(
            f'Отлично, я запомнил ваш класс под именем <b>{classname}</b>. {ENTER}'
            'Теперь напишите, в какие дни вы учитесь '
            '<i>(Например, [понедельник, вторник, ...] или [понедельник-пятница] или [пн-пт])</i>'
            )
    else:
        return await message.answer(f'Класс с названием {classname} уже существует. Попробуйте другое имя')

@router.message(ConfigureState.choosing_days_of_study)
async def choosen_study_type(message: Message, state: FSMContext):
    weekdays = parse_weekdays(message.text)
    await state.update_data({
        _StateData.weekdays: weekdays
    })
    weekdays_enumerating_string = ", ".join([wd.accusative for wd in weekdays]) # понедельник, среду, ...
    subjects = await state.get_data()[_StateData.subjects] # default subjects for a while
    await state.set_state(ConfigureState.changing_subjects_list)
    return await message.answer(format_answer_changed_subject_list(
        f'Вы учитесь в {weekdays_enumerating_string}. ' + 
        '\nТеперь разберемся с предметами.', subjects
        ),
        reply_markup=InlineMarkup.subjects_list_changing
    )
    
ChangingSubjectListHandlerFactory(
    router,
    ConfigureState.changing_subjects_list, 
    ConfigureState.waiting_for_day_length,
    _StateData.subjects,
    _StateData.subject_groups,
    after_message_text='Отлично, вот итоговый список предметов:\n\n{}' +
        '\n\nТеперь займемся расписанием. Чтобы начать, '
        'напишите количество уроков в вашем самом долгом дне (число уроков)'
)

@router.message(ConfigureState.waiting_for_day_length, F.text.isnumeric())
async def start_timetable_making(message: Message, state: FSMContext):
    lessons_amount = int(message.text)
    weekdays = (await state.get_data())[_StateData.weekdays]
    builder = TimetableBuilder(lessons_amount, weekdays)
    await state.update_data({_StateData.timetable_builder: builder})
    await state.set_state(ConfigureState.making_timetable)
    return await message.answer(
        'Для настройки расписания нажимайте на кнопки с предметами '
        'или на "Ничего", если в этот момент нет урока.\n'
        'Для разделения на группы просто выберите урок первой группы, '
        'и я предложу вам выбрать предмет для второй\n'
        '<i>(оба предмета (или один и тот же) должны были быть выбраны, как разделённые на группы)</i>',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Понятно', callback_data='timetable_started')]
        ])
    )

@router.callback_query(ConfigureState.making_timetable, F.data == 'timetable_started' | F.data.startswith('ttsubject_'))
async def making_timetable(callback: CallbackQuery, state: FSMContext):
    
    data = await state.get_data()
    subjects = data[_StateData.subjects]
    subject_groups = data[_StateData.subject_groups]
    builder = data[_StateData.timetable_builder]

    if callback.data.startswith('ttsubject_'):
        new_subject = Subject.decode(callback.data.split('_')[1])
        result_code = builder.next_subject(new_subject, subject_groups[new_subject]) 

    subject_cursor = builder.subject_cursor
    weekday_cursor = builder.weekday_cursor

    match result_code:
        case 0: 
            answer = format_answer_timtable_making(
                weekday_cursor, builder.current_timetable, 
                f'Нажмите на предмет, который станет {subject_cursor+1}-м уроком в {weekday_cursor.accusative}',
                subject_cursor
            )
            kb = InlineMarkup.get_all_subjects_markup(subjects, 'ttsubject')
        case 1 | 2:
            is_last_day = result_code == 2
            answer = format_answer_timtable_making(
                weekday_cursor, builder.current_timetable,
                f'Перепроверьте расписание на {weekday_cursor.accusative} и выберите действие'
            )
            kb = InlineMarkup.get_timetable_ending_markup(weekday_cursor, builder.get_next_weekday(), is_last_day)
    await state.set_state(ConfigureState.ending_timetable)
    return await callback.message.edit_text(answer, reply_markup=kb)

@router.callback_query(ConfigureState.ending_timetable, F.data.startswith('ttend_'))
async def ending_timetable(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[1]
    data = await state.get_data()
    builder = data[_StateData.timetable_builder]
    subjects = data[_StateData.subjects]
    match action:
        case 'next' | 'again':
            if action == 'again':
                builder.weekday_again()
            answer = format_answer_timtable_making(
                builder.weekday_cursor, builder.current_timetable, 
                f'Нажмите на предмет, который станет {builder.subject_cursor+1}-м уроком в {builder.weekday_cursor.accusative}',
                builder.subject_cursor
            )
            kb = InlineMarkup.get_all_subjects_markup(subjects, 'ttsubject')
            await state.set_state(ConfigureState.making_timetable)
            return await callback.message.edit_text(answer, reply_markup=kb)
        case 'complete':
            _save_new_class(data)
            classname = data[_StateData.classname]
            await state.clear()
            return await callback.message.edit_text(f'Настройка завершена! Сохранил класс <b>{classname}</b>')

