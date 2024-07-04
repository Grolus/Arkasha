from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from filters import ChatTypeFilter
from entities import Subject
from storage.tables import AdministratorTable, ClassTable
from utils import Weekday
from bot_configuration import Bot_configurator
from utils.states import ConfigureState
from utils.keyboards import ConfigureInlineKeyboardMarkup as InlineMarkup
from utils.strings import (format_answer_changed_subject_list, 
                           format_answer_start_configure,
                           format_answer_timtable_making, 
                           subject_list_to_str,
                           foramat_html_tags)
from logers import handle as loger


ENTER = '\n'

router = Router()
router.message.filter(ChatTypeFilter('private'))

# TODO class OnAnyMessageMiddleware()
# TODO edit configuration


def _new_subjects_master(new_subjects_names: list[str], existing_subjects: list[Subject]) -> tuple[list[Subject], list[Subject]]:
    """Resolves wich subjects will be added to `existing_subjects` and wich no"""
    # delete repetition, but save order
    subjects_names = []
    for sjname in new_subjects_names:
        if not sjname in subjects_names:
            subjects_names.append(sjname)
    to_add = []
    already_exists = []
    for subject_name in subjects_names:
        if (sj := Subject(subject_name)) in existing_subjects:
            already_exists.append(sj)
        else:
            to_add.append(sj)
    return to_add, already_exists


@router.message(Command('configure'), StateFilter(None))
async def start_configure(message: Message, state: FSMContext):
    if existed_users_classes := AdministratorTable(message.from_user.username).get_classes():
        await message.answer(
            format_answer_start_configure(len(existed_users_classes)),
            reply_markup=InlineMarkup.get_edit_or_new_cfg_choosing_markup(existed_users_classes)
        )
        await state.set_state(ConfigureState.edit_or_new_class_choosing)

@router.callback_query(F.data == 'newcfgbegin', ConfigureState.edit_or_new_class_choosing)
async def start_new_class(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text('Вы начали конфигурацию нового класса! Для начала придумайте уникальное имя для вашего нового класса. Например, "1А 1 школа"')
    await state.set_state(ConfigureState.typing_class_name)


@router.message(ConfigureState.typing_class_name, F.text)
async def typed_class_name(message: Message, state: FSMContext):
    classname = message.text
    if not classname in ClassTable.get_all_names():
        Bot_configurator(message.from_user.username, classname)
        await message.answer(f'Отлично, я запомнил ваш класс под именем <b>{classname}</b>. {ENTER}Теперь выберите вашу систему обучения...', 
                            reply_markup=InlineMarkup.choosing_studytype)
        await state.set_state(ConfigureState.choosing_days_of_study)
    else:
        await message.answer(f'Класс с названием {classname} уже существует. Попробуйте другое имя')

@router.callback_query(ConfigureState.choosing_days_of_study, F.data.startswith('studytype_'))
async def choosen_study_type(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.split('_')[1]) # 5 or 6
    cfg = Bot_configurator.get(callback.from_user.username)
    cfg.set_is_5_days_studytype(days == 5)
    await callback.message.edit_text(format_answer_changed_subject_list(
        f'Понял, у вас {"пяти" if days == 5 else "шести"}дневка. ' + 
        '\nТеперь разберемся с предметами.', cfg._subjects_list),
        reply_markup=InlineMarkup.subjects_list_changing)
    await state.set_state(ConfigureState.changing_subjects_list)

@router.callback_query(ConfigureState.changing_subjects_list, F.data.startswith('subjectlistchange_'))
async def change_subject_list(callback: CallbackQuery, state: FSMContext): 
    action = callback.data.split('_')[1]
    cfg = Bot_configurator.get(callback.from_user.username)
    match action:
        case 'add':
            await callback.message.answer('Введите название нового предмета ' +
                                          '(только буквы, можно перечислить несколько предметов через запятую)...')
            await state.set_state(ConfigureState.waiting_for_new_subject)
            await callback.answer()
        case 'remove':
            if subjects_list := cfg._subjects_list:
                await callback.message.edit_text(
                    'Выберите предмет для удаления:', 
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text=subject.name, callback_data=f'removedsubject_{subject.encode()}')]
                            for subject in subjects_list
                        ]))
                await state.set_state(ConfigureState.waiting_for_removed_subject)
            else: 
                await callback.message.edit_text(
                    'Список предметов пуст!',
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                            InlineKeyboardButton(text='Добавить', callback_data='subjectlistchange_add')]]))
                await state.set_state(ConfigureState.changing_subjects_list)
            await callback.answer()
        case 'finish':
            await callback.message.edit_text(
                'Отлично, вот итоговый список предметов:\n\n' +
                    subject_list_to_str(cfg._subjects_list, html_tags='b') +
                    '\n\nТеперь займемся расписанием. Вы можете написать его вручную или '+
                    'составить вместе со мной, нажимая на кнопки (рекомендовано)',
                reply_markup=InlineMarkup.choosing_timetable_way)
            await state.set_state(ConfigureState.choosing_timetable_way)
            await callback.answer()

@router.message(ConfigureState.waiting_for_new_subject, F.text)
async def add_subject(message: Message, state: FSMContext):
    new_subjects_names = list(map(str.strip, message.text.split(',')))
    new_subjects_names = [i for i in new_subjects_names if i]
    for i in range(len(new_subjects_names)):
        new_subjects_names[i] = new_subjects_names[i][0].upper() + new_subjects_names[i][1:]
    cfg = Bot_configurator.get(message.from_user.username)
    subjects_to_add, already_exists_subjects = _new_subjects_master(new_subjects_names, cfg._subjects_list)
    for subject in subjects_to_add:
        cfg.new_subject(subject)
    answer = format_answer_changed_subject_list((
        ('Добавлены предметы' if len(subjects_to_add) > 1
        else 'Добавлен предмет') + f' <i>{", ".join(map(str, subjects_to_add))}</i>') if subjects_to_add else '' +
        ((f'\n(Предмет{"ы" if len(already_exists_subjects) > 1 else ""} ' +
         f'<i>{", ".join(map(str, already_exists_subjects))}</i> уже есть в списке)') if already_exists_subjects else ''),
        cfg._subjects_list)
    
    await message.answer(answer, reply_markup=InlineMarkup.subjects_list_changing)
    await state.set_state(ConfigureState.changing_subjects_list)

@router.callback_query(ConfigureState.waiting_for_removed_subject, F.data.startswith('removedsubject_'))
async def remove_subject(callback: CallbackQuery, state: FSMContext):
    removed_subject_code = callback.data.split('_')[1]
    removed_subject = Subject.decode(removed_subject_code)
    cfg = Bot_configurator.get(callback.from_user.username)
    cfg.remove_subject(removed_subject)
    await callback.message.edit_text(format_answer_changed_subject_list(
        f'Удалён предмет {removed_subject}.', cfg._subjects_list
    ), reply_markup=InlineMarkup.subjects_list_changing)
    await state.set_state(ConfigureState.changing_subjects_list)

@router.callback_query(ConfigureState.choosing_timetable_way, F.data.startswith('timetableway_'))
async def timetable_compiling(callback: CallbackQuery, state: FSMContext): 
    cfg = Bot_configurator.get(callback.from_user.username)
    way = callback.data.split('_')[1]
    match way:
        case 'manually':
            await callback.message.edit_text(
                'Чуть позже реализую, пока воспользуйтесь конструктором по кнопкам', 
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text='По кнопкам', callback_data='timetableway_smart')]]))
        case 'smart':
            await callback.message.edit_text(
                'Отлично. Для начала скажите мне, сколько уроков '
                'в вашем самом долгом дне (просто количество уроков)...'
                )
            await state.set_state(ConfigureState.waiting_for_day_length)

@router.message(ConfigureState.waiting_for_day_length, F.text.isnumeric())
async def start_smart_timetable(message: Message, state: FSMContext):
    cfg = Bot_configurator.get(message.from_user.username)
    cfg.set_lessons_count(int(message.text))
    weekday = cfg.weekday_cursor()
    await message.answer('Начинаем настройку расписания на %s' % weekday.genetive)
    await message.answer(
        format_answer_timtable_making(weekday, cfg.timetable(weekday)),
        reply_markup=InlineMarkup.get_all_subjects_markup(cfg.subjects())
    )
    await state.set_state(ConfigureState.making_timetable)

@router.callback_query(ConfigureState.making_timetable, F.data.startswith('ttsubject_'))
async def smart_timetable(callback: CallbackQuery, state: FSMContext=...):
    cfg = Bot_configurator.get(callback.from_user.username)
    weekday = cfg.weekday_cursor()
    choosed_subject = Subject.decode(callback.data.split('_')[1])
    is_subject_last = cfg.tt_next_subject(choosed_subject)

    if is_subject_last:
        await callback.message.edit_text(
            format_answer_timtable_making(
                weekday, cfg.timetable(weekday),
                f'Проверьте список предметов на {weekday.genetive} и выберите действие:'
                ),
            reply_markup=InlineMarkup.get_timetable_ending_markup(weekday, weekday == cfg._last_lerning_weekday)
        )
        await state.set_state(ConfigureState.ending_timetable)
        return
    await callback.message.edit_text(
        format_answer_timtable_making(weekday, cfg.timetable(weekday)),
        reply_markup=InlineMarkup.get_all_subjects_markup(cfg.subjects())
        )

@router.callback_query(ConfigureState.ending_timetable, F.data.startswith('ttend_'))
async def ending_tt(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[1]
    cfg = Bot_configurator.get(callback.from_user.username)
    match action:
        case 'again':
            weekday = cfg.weekday_cursor()
            cfg.clear_tt(weekday)
        case 'next':
            cfg.tt_next_weekday()
            weekday = cfg.weekday_cursor()
        case 'complete':
            ClassTable.save_new_configuration(cfg)
            await callback.message.edit_text(
                f'Настройка бота завершена! Сохранил "{cfg._classname}"'
            )
            await state.set_state(None)
            return
    await callback.message.edit_text(
        format_answer_timtable_making(weekday, cfg.timetable(weekday)),
        reply_markup=InlineMarkup.get_all_subjects_markup(cfg.subjects())
    )
    await state.set_state(ConfigureState.making_timetable)





@router.message(Command('timetable'))
async def timetable_show(message: Message):
    cfg = Bot_configurator.get(message.from_user.username)
    await message.answer(
        f'Расписание класса "{cfg._classname}" (администратор: @{cfg._username})\n\n' +
        '\n\n'.join([
            foramat_html_tags('bu', weekday.name_ru.title() + ':\n') + '-> ' + '\n-> '.join([
                f'{i+1}. {subject.name}' for i, subject in enumerate(timetable)
            ]) for weekday, timetable in enumerate(cfg.timetable_all())
        ])
    )


"""
@router.message(Command('buttons'))
async def many_buttons(message: Message):
    rows, columns = tuple(map(int, message.text.split()[1:]))
    await message.answer(
        'смотри куча кнопок',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f'Кнопка {i} {j}', callback_data=str(i+j))
             for j in range(columns)]
            for i in range(0, rows)
        ])
    )



@router.callback_query(F.data.isnumeric())
@router.message(Command('dif'))
async def dificult_handler(message_or_callback: Message | CallbackQuery, state: FSMContext=...):

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer('Это сообщение')
    elif isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer('Это колбек')
    else:
        print('?wow?')
"""
