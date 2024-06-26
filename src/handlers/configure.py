from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State


from filters import ChatTypeFilter
from homework import Subject, EmptySubject
from utils import Bot_configurator, weekday_up
from utils.constants import WEEKDAYS_GENETIVE, WEEKDAYS_DATIV, WEEKDAY_NAMES_RU
from logers import handle as loger


ENTER = '\n'

router = Router()
router.message.filter(ChatTypeFilter('private'))

def _format_answer_changed_subject_list(pretext: str, subjects_list: list[Subject]) -> str:
    '''Compiling answer via sample:\n "`{pretext}`\n\n subject1 \nsubject2 \n ...\n\nХотите добавить/убрать предмет?"'''
    result = pretext + '\n\n' + _subject_list_to_str(subjects_list, html_tags='b') + '\n\nХотите добавить/убрать предмет?'
    loger.debug(result)
    return result

def _foramat_html_tags(html_tags: str, text: str) -> str:
    """Decorating html-tags to right format (e. g. `html_tags='bu'` => `'<b><u>{text}</u></b>)'`"""
    begin = ''.join([f'<{tag}>' for tag in html_tags])
    end = ''.join([f'</{tag}>' for tag in html_tags[::-1]])
    return begin + text + end

def _subject_list_to_str(subject_list: list[Subject], *,
                         html_tags: str='', separator: str='\n', 
                         numbered: bool=False, decorate_numbers: bool=False, start_numbers: int=1):
    """Converts list of subjects to string (subjects names separated by '\\n')\n
    :param subject_list: list of subjects to print
    :param html_tags: (Optional) html-tags to decorate final string (e. g. `tags='bu'` => `'<b><u>{subjects_to_print}</u></b>)'`"""
    subjects_to_print = separator.join(
        [(f'{start_numbers+i}. ' if numbered and not decorate_numbers else '') + _foramat_html_tags(
            html_tags, 
            (f'{start_numbers+i}. ' if numbered and decorate_numbers else '') + subject.name if not subject is None else '...')
         for i, subject in enumerate(subject_list)]
        )
    return subjects_to_print

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

def _inline_buttons_master(buttons_as_tuple: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    """Converts buttons as tuple to `InlineKeyboardMarkup` object\n
    with buttons `InlineKeyboardButton(text=tuple[0], callback_data=tuple[1])`"""
    keyboard = [
        [InlineKeyboardButton(text=text, callback_data=callback_data) for text, callback_data in row]
        for row in buttons_as_tuple
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def _format_answer_timtable_making(weekday: int, timetable: list[Subject], posttext: str='') -> str:
    answer = f'Составляем расписание на <b><u>{WEEKDAYS_GENETIVE[weekday]}</u></b>. \n\n' + \
    _subject_list_to_str(timetable, html_tags='i', numbered=True) + '\n\n' + \
    (posttext or f'Нажимайте на предметы в нужном порядке или на "{EmptySubject.name}", если в этот момент нет урока.')
    return answer
    

def _subject_to_button(subject: Subject | EmptySubject, callback_data_prefix: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=str(subject), callback_data=f'{callback_data_prefix}_{subject.encode()}')

def _get_all_subjects_markup(subjects: list[Subject]) -> InlineKeyboardMarkup:
    keyboard = []
    callback_prefix = 'ttsubject'
    for i, subject in enumerate(subjects):
        if i % 3 == 0:
            keyboard.append([_subject_to_button(subject, callback_prefix), None, None])
        else:
            keyboard[i // 3][i % 3] = _subject_to_button(subject, callback_prefix)
    keyboard.append([_subject_to_button(EmptySubject(), callback_prefix)])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def _get_tt_end_markup(now_weekday: int, is_last_day: bool=False) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Ещё раз', callback_data='ttend_again'),
         InlineKeyboardButton(text=f'Перейти к {WEEKDAYS_DATIV[weekday_up(now_weekday)]}' 
                              if not is_last_day else 'Завершить', 
                              callback_data='ttend_next'
                              if not is_last_day else 'ttend_complete')]
    ])

class InlineMarkup:
    subjects_list_changing = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Добавить', callback_data='subjectlistchange_add'),
             InlineKeyboardButton(text='Удалить', callback_data='subjectlistchange_remove')],
             [InlineKeyboardButton(text='Готово', callback_data='subjectlistchange_finish')]
        ]
    )
    choosing_studytype = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='5 дней', callback_data='studytype_5'),
          InlineKeyboardButton(text='6 дней', callback_data='studytype_6')]
          ]
    )
    choosing_timetable_way = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='По кнопкам (рекомендовано)', callback_data='timetableway_smart'),
         InlineKeyboardButton(text='Вручную', callback_data='timetableway_manually')]
    ])


class ConfigureState(StatesGroup):
    typing_class_name = State()
    choosing_days_of_study = State()
    changing_subjects_list = State()
    waiting_for_new_subject = State()
    waiting_for_removed_subject = State()
    choosing_timetable_way = State()
    waiting_for_day_length = State()
    making_timetable = State()
    ending_timetable = State()


@router.message(Command('configure'), StateFilter(None))
async def start_configure(message: Message, state: FSMContext):
    await message.answer('Вы начали настройку бота! Для начала напишите мне имя вашего класса...')
    await state.set_state(ConfigureState.typing_class_name)

@router.message(ConfigureState.typing_class_name, F.text)
async def typed_class_name(message: Message, state: FSMContext):
    classname = message.text
    Bot_configurator(message.from_user.username, classname)
    await message.answer(f'Отлично, я запомнил ваш класс под именем <b>{classname}</b>. {ENTER}Теперь выберите вашу систему обучения...', 
                         reply_markup=InlineMarkup.choosing_studytype)
    await state.set_state(ConfigureState.choosing_days_of_study)

@router.callback_query(ConfigureState.choosing_days_of_study, F.data.startswith('studytype_'))
async def choosen_study_type(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.split('_')[1]) # 5 or 6
    cfg = Bot_configurator.get(callback.from_user.username)
    cfg.set_is_5_days_studytype(days == 5)
    await callback.message.edit_text(_format_answer_changed_subject_list(
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
                    _subject_list_to_str(cfg._subjects_list, html_tags='b') +
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
    answer = _format_answer_changed_subject_list((
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
    await callback.message.edit_text(_format_answer_changed_subject_list(
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
    await message.answer('Начинаем настройку расписания на %s' % WEEKDAYS_GENETIVE[weekday])
    await message.answer(
        _format_answer_timtable_making(weekday, cfg.timetable(weekday)),
        reply_markup=_get_all_subjects_markup(cfg.subjects())
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
            _format_answer_timtable_making(
                weekday, cfg.timetable(weekday),
                f'Проверьте список предметов на {WEEKDAYS_GENETIVE[weekday]} и выберите действие:'
                ),
            reply_markup=_get_tt_end_markup(weekday, weekday == cfg._last_lerning_weekday)
        )
        await state.set_state(ConfigureState.ending_timetable)
        return
    await callback.message.edit_text(
        _format_answer_timtable_making(weekday, cfg.timetable(weekday)),
        reply_markup=_get_all_subjects_markup(cfg.subjects())
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
            await callback.message.edit_text(
                'Настройка расписания завершена! (Показать расписание - /timetable)'
            )
            await state.set_state(None)
    await callback.message.edit_text(
        _format_answer_timtable_making(weekday, cfg.timetable(weekday)),
        reply_markup=_get_all_subjects_markup(cfg.subjects())
    )
    await state.set_state(ConfigureState.making_timetable)

@router.message(Command('timetable'))
async def timetable_show(message: Message):
    cfg = Bot_configurator.get(message.from_user.username)
    await message.answer(
        f'Расписание класса "{cfg._classname}" (администратор: @{cfg._username})\n\n' +
        '\n\n'.join([
            _foramat_html_tags('bu', WEEKDAY_NAMES_RU[weekday].title() + ':\n') + '-> ' + '\n-> '.join([
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
