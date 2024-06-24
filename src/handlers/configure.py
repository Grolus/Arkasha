from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State


from filters import ChatTypeFilter
from homework import Subject
from utils import Bot_configuration
from logers import handle as loger


ENTER = '\n'
router = Router()
router.message.filter(ChatTypeFilter('private'))

def _format_answer_changed_subject_list(pretext: str, subjects_list: list[Subject]):
    '''Compiling answer via sample:\n "`{pretext}`\n\n subject1 \nsubject2 \n ...\n\nХотите добавить/убрать предмет?"'''
    result = pretext + '\n\n' + _subject_list_to_str(subjects_list, 'b') + '\n\nХотите добавить/убрать предмет?'
    loger.debug(result)
    return result

def _foramat_html_tags(html_tags: str, text: str):
    """Decorating html-tags to right format (e. g. `html_tags='bu'` => `'<b><u>{text}</u></b>)'`"""
    begin = ''.join([f'<{tag}>' for tag in html_tags])
    end = ''.join([f'</{tag}>' for tag in html_tags[::-1]])
    return begin + text + end

def _subject_list_to_str(subject_list: list[Subject], html_tags: str='', separator: str='\n'):
    """Converts list of subjects to string (subjects names separated by '\\n')\n
    :param subject_list: list of subjects to print
    :param html_tags: (Optional) html-tags to decorate final string (e. g. `tags='bu'` => `'<b><u>{subjects_to_print}</u></b>)'`"""
    subjects_to_print = separator.join([subject.name for subject in subject_list])
    return _foramat_html_tags(html_tags, subjects_to_print)

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


class ConfigureState(StatesGroup):
    typing_class_name = State()
    choosing_days_of_study = State()
    changing_subjects_list = State()
    waiting_for_new_subject = State()
    waiting_for_removed_subject = State()


@router.message(Command('configure'), StateFilter(None))
async def start_configure(message: Message, state: FSMContext):
    Bot_configuration(message.from_user.username)
    await message.answer('Вы начали настройку бота! Для начала напишите мне имя вашего класса...')
    await state.set_state(ConfigureState.typing_class_name)

@router.message(ConfigureState.typing_class_name, F.text)
async def typed_class_name(message: Message, state: FSMContext):
    classname = message.text
    Bot_configuration(message.from_user.username).classname(classname)
    await message.answer(f'Отлично, я запомнил ваш класс под именем <b>{classname}</b>. {ENTER}Теперь выберите вашу систему обучения...', 
                         reply_markup=InlineMarkup.choosing_studytype)
    await state.set_state(ConfigureState.choosing_days_of_study)

@router.callback_query(ConfigureState.choosing_days_of_study, F.data.startswith('studytype_'))
async def choosen_study_type(callback: CallbackQuery, state: FSMContext):
    days = int(callback.data.split('_')[1]) # 5 or 6
    cfg = Bot_configuration(callback.from_user.username)
    cfg.is_5_days_studytype(days == 5)
    await callback.message.edit_text(_format_answer_changed_subject_list(
        f'Понял, у вас {"пяти" if days == 5 else "шести"}дневка. ' + 
        '\nТеперь разберемся с предметами.', cfg._subjects_list),
        reply_markup=InlineMarkup.subjects_list_changing)
    await state.set_state(ConfigureState.changing_subjects_list)

@router.callback_query(ConfigureState.changing_subjects_list, F.data.startswith('subjectlistchange_'))
async def change_subject_list(callback: CallbackQuery, state: FSMContext): 
    action = callback.data.split('_')[1]
    cfg = Bot_configuration(callback.from_user.username)
    match action:
        case 'add':
            
            await callback.message.answer('Введите название нового предмета ' +
                                          '(только буквы, можно перечислить несколько предметов через запятую)...')
            await state.set_state(ConfigureState.waiting_for_new_subject)
            await callback.answer()
        case 'remove':
            if subjects_list := Bot_configuration(callback.from_user.username)._subjects_list:
                await callback.message.edit_text('Выберите предмет для удаления:', 
                                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                                [InlineKeyboardButton(text=subject.name, callback_data=f'removedsubject_{subject.encode()}')]
                                                for subject in subjects_list
                                            ]))
                await state.set_state(ConfigureState.waiting_for_removed_subject)
                
            else: 
                await callback.message.edit_text('Список предметов пуст!',
                                              reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                                                  InlineKeyboardButton(text='Добавить', callback_data='subjectlistchange_add')
                                                  ]])
                                                  )
                await state.set_state(ConfigureState.changing_subjects_list)
            await callback.answer()
        case 'finish':
            await callback.message.edit_text('Отлично, вот итоговый список предметов:\n\n' +
                                     _subject_list_to_str(cfg._subjects_list, 'b') +
                                     '\n\nТеперь займемся расписанием... (пока пусто)')
            await state.set_state(None)
            await callback.answer()

@router.message(ConfigureState.waiting_for_new_subject, F.text)
async def add_subject(message: Message, state: FSMContext):
    new_subjects_names = list(map(str.strip, message.text.split(',')))
    for i in range(len(new_subjects_names)):
        new_subjects_names[i] = new_subjects_names[i][0].upper() + new_subjects_names[i][1:]
    cfg = Bot_configuration(message.from_user.username)
    subjects_to_add, already_exists_subjects = _new_subjects_master(new_subjects_names, cfg._subjects_list)
    for subject in subjects_to_add:
        cfg.new_subject(subject)
    answer = _format_answer_changed_subject_list((
        ('Добавлены предметы' if len(subjects_to_add) > 1
        else 'Добавлен предмет') + f' <i>{", ".join(subjects_to_add)}</i>') if subjects_to_add else '' +
        ((f'\n(Предмет{"ы" if len(already_exists_subjects) > 1 else ""} ' +
         f'<i>{", ".join(map(str, already_exists_subjects))}</i> уже есть в списке)') if already_exists_subjects else ''),
        cfg._subjects_list)
    
    await message.answer(answer, reply_markup=InlineMarkup.subjects_list_changing)
    await state.set_state(ConfigureState.changing_subjects_list)

@router.callback_query(ConfigureState.waiting_for_removed_subject, F.data.startswith('removedsubject_'))
async def remove_subject(callback: CallbackQuery, state: FSMContext):
    removed_subject_code = callback.data.split('_')[1]
    removed_subject = Subject.decode(removed_subject_code)
    cfg = Bot_configuration(callback.from_user.username)
    cfg.remove_subject(removed_subject)
    await callback.message.edit_text(_format_answer_changed_subject_list(
        f'Удалён предмет {removed_subject}.', cfg._subjects_list
    ), reply_markup=InlineMarkup.subjects_list_changing)
    await state.set_state(ConfigureState.changing_subjects_list)

# TODO придумать формат получения расписания и реализовать
