from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from typing import Any
from enum import Enum

from filters import ChatTypeFilter
from entities import Subject, TimetableBuilder, Timetable
from entities.subject import DEFAULT_SUBJECTS
from storage.tables import AdministratorTable, ClassTable
from utils.weekday import Weekday, parse_weekdays
from utils.states import ConfigureState
from utils.keyboards import ConfigureInlineKeyboardMarkup as InlineMarkup
from utils.strings import (format_answer_changed_subject_list, 
                           format_answer_start_configure,
                           format_answer_timtable_making, 
                           subject_list_to_str,
                           foramat_html_tags)
from utils.handler_factory import ChangingSubjectListHandlerFactory
from logers import handle as loger


ENTER = '\n'

router = Router()
router.message.filter(ChatTypeFilter('private'))


class DynamicCreator:
    subjects: list[Subject]
    name: str
    creator: str
    timetables: dict[Weekday: Timetable]
    _timetable_builder: TimetableBuilder
    def __init__(self, classname: str, creator_username: str, subjects: list[Subject]):
        self.name = classname
        self.creator = creator_username
        self.subjects = subjects
        self._timetable_builder = TimetableBuilder()
    


CREATORS: dict[str: DynamicCreator] = {}

# TODO class OnAnyMessageMiddleware()





@router.message(Command('configure'), StateFilter(None))
async def start_configure(message: Message, state: FSMContext):
    if existed_users_classes := AdministratorTable(message.from_user.username).get_classes():
        await message.answer(
            format_answer_start_configure(len(existed_users_classes)),
            reply_markup=InlineMarkup.get_edit_or_new_cfg_choosing_markup(existed_users_classes)
        )
        await state.set_state(ConfigureState.edit_or_new_class_choosing)
    else:
        await message.answer('Вы начали конфигурацию нового класса! Для начала придумайте уникальное имя для вашего нового класса. Например, "1А 1 школа"')
        await state.set_state(ConfigureState.typing_class_name)

@router.callback_query(F.data == 'newcfgbegin', ConfigureState.edit_or_new_class_choosing)
async def start_new_class(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Вы начали конфигурацию нового класса! Для начала придумайте уникальное имя для вашего нового класса. Например, "1А 1 школа"')
    await state.set_state(ConfigureState.typing_class_name)


@router.message(ConfigureState.typing_class_name, F.text)
async def typed_class_name(message: Message, state: FSMContext):
    classname = message.text
    if ClassTable.validate_name(classname):
        #Bot_configurator(message.from_user.username, classname)
        CREATORS[message.from_user.username] = DynamicCreator(
            classname, 
            message.from_user.username, 
            DEFAULT_SUBJECTS.copy()
        )
        await message.answer(
            f'Отлично, я запомнил ваш класс под именем <b>{classname}</b>. {ENTER}'
            'Теперь напишите, в какие дни вы учитесь '
            '<i>(Например, [понедельник, вторник, ...] или [понедельник-пятница] или [пн-пт])</i>'
            )
        await state.set_state(ConfigureState.choosing_days_of_study)
    else:
        await message.answer(f'Класс с названием {classname} уже существует. Попробуйте другое имя')

@router.message(ConfigureState.choosing_days_of_study)
async def choosen_study_type(message: Message, state: FSMContext):
    weekdays = parse_weekdays(message.text)
    CREATORS[message.from_user.username]._timetable_builder.set_weekdays(weekdays)
    await message.answer(format_answer_changed_subject_list(
        f'Вы учитесь в {", ".join([wd.accusative for wd in weekdays])}. ' + 
        '\nТеперь разберемся с предметами.', CREATORS[message.from_user.username].subjects),
        reply_markup=InlineMarkup.subjects_list_changing)
    await state.set_state(ConfigureState.changing_subjects_list)


ChangingSubjectListHandlerFactory(
    router, 
    ConfigureState.changing_subjects_list, 
    ConfigureState.choosing_timetable_way,
    lambda username: CREATORS[username].subjects,
    after_message_text='Отлично, вот итоговый список предметов:\n\n{}' +
        '\n\nТеперь займемся расписанием. Вы можете написать его вручную ' +
        'или составить вместе со мной, нажимая на кнопки (рекомендовано)',
    after_message_reply_markup=InlineMarkup.choosing_timetable_way
)


@router.callback_query(ConfigureState.choosing_timetable_way, F.data.startswith('timetableway_'))
async def timetable_compiling(callback: CallbackQuery, state: FSMContext): 
    #cfg = Bot_configurator.get(callback.from_user.username)
    way = callback.data.split('_')[1]
    match way:
        case 'smart':
            await callback.message.edit_text(
                'Отлично. Для начала скажите мне, сколько уроков '
                'в вашем самом долгом дне (просто количество уроков)...'
                )
            await state.set_state(ConfigureState.waiting_for_day_length)

@router.message(ConfigureState.waiting_for_day_length, F.text.isnumeric())
async def start_smart_timetable(message: Message, state: FSMContext):
    builder: TimetableBuilder = CREATORS[message.from_user.username]._timetable_builder
    builder.set_lessons_amount(int(message.text))
    weekday = builder.weekday_cursor
    await message.answer('Начинаем настройку расписания на %s' % weekday.genetive)
    await message.answer(
        format_answer_timtable_making(weekday, builder[weekday], cursor=0),
        reply_markup=InlineMarkup.get_all_subjects_markup(CREATORS[message.from_user.username].subjects)
    )
    await state.set_state(ConfigureState.making_timetable)

@router.callback_query(ConfigureState.making_timetable, F.data.startswith('ttsubject_'))
async def smart_timetable(callback: CallbackQuery, state: FSMContext=...):
    builder: TimetableBuilder = CREATORS[callback.from_user.username]._timetable_builder
    weekday = builder.weekday_cursor
    choosed_subject = Subject.decode(callback.data.split('_')[1])
    subject_inserted_code = builder.next_subject(choosed_subject)

    if subject_inserted_code > 0:
        await callback.message.edit_text(
            format_answer_timtable_making(
                weekday, builder[weekday],
                f'Проверьте список предметов на {weekday.genetive} и выберите действие:'
                ),
            reply_markup=InlineMarkup.get_timetable_ending_markup(weekday, subject_inserted_code == 2)
        )
        await state.set_state(ConfigureState.ending_timetable)
        return
    subject_cursor = builder.subject_cursor
    await callback.message.edit_text(
        format_answer_timtable_making(weekday, builder[weekday], cursor=subject_cursor),
        reply_markup=InlineMarkup.get_all_subjects_markup(CREATORS[callback.from_user.username].subjects)
        )

@router.callback_query(ConfigureState.ending_timetable, F.data.startswith('ttend_'))
async def ending_tt(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[1]
    builder: TimetableBuilder = CREATORS[callback.from_user.username]._timetable_builder
    match action:
        case 'again':
            weekday = builder.weekday_cursor
            del builder[weekday]
        case 'next':
            weekday = builder.weekday_cursor
        case 'complete':
            creator = CREATORS[callback.from_user.username]
            ClassTable.save_new_configuration(
                classname=creator.name,
                creator_username=creator.creator,
                subject_list=creator.subjects,
                timetables=creator._timetable_builder.to_dict()
            )
            await callback.message.edit_text(
                f'Настройка класса завершена! Сохранил "{creator.name}"'
            )
            await state.set_state(None)
            return
    await callback.message.edit_text(
        format_answer_timtable_making(weekday, builder[weekday]),
        reply_markup=InlineMarkup.get_all_subjects_markup(CREATORS[callback.from_user.username].subjects)
    )
    await state.set_state(ConfigureState.making_timetable)

