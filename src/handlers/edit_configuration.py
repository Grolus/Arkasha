

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from filters import ChatTypeFilter
from utils import Weekday
from utils.states import ConfigureState, EditConfigureState
from utils.keyboards import EditConfigureInlineKeyboardMarkup, ConfigureInlineKeyboardMarkup
from utils.strings import subject_list_to_str, format_answer_start_configure
from entities import Class
from storage.tables import ClassTable, AdministratorTable

router = Router()
router.message.filter(ChatTypeFilter('private'))
EDITORS: dict[str: Class] = {}

@router.callback_query(ConfigureState.edit_or_new_class_choosing, F.data.startswith('editcfgbegin_'))
@router.callback_query(EditConfigureState.classname_edited, F.data == 'classnameedited')
async def begin_cfg_edit(callback: CallbackQuery, state: FSMContext):
    class_id = int(callback.data.split('_')[1])
    class_ = Class.from_table_value(ClassTable(_class_id=class_id))
    class_.editor = callback.from_user.username
    EDITORS[callback.from_user.username] = class_
    await callback.message.edit_text(
        class_.get_information_string(),
        reply_markup=EditConfigureInlineKeyboardMarkup.choose_value_to_edit)
    await state.set_state(EditConfigureState.choosing_value_to_edit)

@router.callback_query(
        EditConfigureState.choosing_value_to_edit, 
        EditConfigureState.classname_edited,
        F.data.startswith('editclass_')
        )
async def choose_value_to_edit_handler(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[1]
    class_ = EDITORS[callback.from_user.username]
    match action:
        case 'name':
            await callback.message.edit_text(f"Придумайте новое имя вашему классу")
            await state.set_state(EditConfigureState.setting_new_classname)
        case 'subjects':
            await callback.message.edit_text(
                f"Предметы <b>{class_.name}</b>:\n\n" +
                subject_list_to_str(class_.subjects, html_tags='i', numbered=True),
                reply_markup=ConfigureInlineKeyboardMarkup.subjects_list_changing
                )
            await state.set_state(EditConfigureState.changing_subject_list)
        case 'administrators':
            await callback.message.edit_text(
                f'Администраторы <b>{class_.name}</b>:\n\n' + 
                '\n'.join(
                    [(f'@{username}' + 
                        (' <i>(создатель)</i>' if username == class_.creator else '')) 
                    for username in class_.administrators]
                    ),
                reply_markup=EditConfigureInlineKeyboardMarkup.administrators_list_changing
            )
            await state.set_state()
        case 'timetable':
            await callback.message.edit_text(
                f"Какой день вы хотите изменить?",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=Weekday(wd).name, callback_data=f'ttchangingday_{wd}') for wd in weekdays_for_row]
                    for weekdays_for_row in (((0, 1), (2, 3), (4)) if len(class_.timetables) == 5 else ((0, 1), (2, 3), (4, 5)))
                ]))
            await state.set_state(EditConfigureState.choosing_day_for_timetable_change)
        case 'cancel':
            classes = AdministratorTable(class_.creator).get_classes()
            await callback.message.edit_text(
                format_answer_start_configure(len(classes)),
                reply_markup=ConfigureInlineKeyboardMarkup.get_edit_or_new_cfg_choosing_markup(classes)
            )
            await state.set_state(ConfigureState.edit_or_new_class_choosing)

@router.message(EditConfigureState.setting_new_classname, F.from_user.in_(EDITORS.keys()), F.text)
async def get_new_classname(message: Message, state: FSMContext):
    new_classname = message.text
    class_: Class = EDITORS[message.from_user.username]
    old_name = class_.name
    if not new_classname in ClassTable.get_all_names():
        class_.name = new_classname
        await message.answer(
            f'Изменил имя вашего класса "<b>{old_name}</b>" -> "<b>{new_classname}</b>"',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Готово', callback_data='classnameedited'),
                 InlineKeyboardButton(text='Изменить', callback_data='editclass_name')]
            ]))
        await state.set_state(EditConfigureState.classname_edited)
        return
    elif new_classname == old_name:
        await message.answer(
            f"Это то же самое название. Вы хотите его изменить?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Оставить', callback_data='classnameedited'),
                 InlineKeyboardButton(text='Изменить', callback_data='editclass_name')]
            ]))
        await state.set_state(EditConfigureState.classname_edited)
    else:
        await message.answer(
            f'Класс с таким названием уже существует. Попробуйте еще раз'
        )
        await state.set_state(EditConfigureState.setting_new_classname)

@router.callback_query(EditConfigureState.changing_subject_list, F.data.startswith('subjectlistchange_'))
async def changing_subject_list(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[1]
    class_ = EDITORS[callback.from_user.username]
    match action:
        case 'add':
            await callback.message.answer('Введите название нового предмета ' +
                                          '(только буквы, можно перечислить несколько предметов через запятую)...')
            await state.set_state(EditConfigureState.waiting_for_new_subject)
            await callback.answer()
        case 'remove':
            if subjects_list := class_.subjects:
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

@router.message(EditConfigureState.waiting_for_new_subject, F.text)
async def get_new_subject(message: Message, state: FSMContext):
    subject_name = message.text
    class_ = EDITORS[message.from_user.username]
    

