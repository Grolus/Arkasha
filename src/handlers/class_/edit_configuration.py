
from enum import Enum

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from filters import ChatTypeFilter
from utils import Weekday
from utils.states import ConfigureState, EditConfigureState
from utils.keyboards import EditConfigureInlineKeyboardMarkup, ConfigureInlineKeyboardMarkup
from utils.strings import subject_list_to_str, format_answer_start_configure, format_answer_timtable_making
from utils.handler_factory import ChangingSubjectListHandlerFactory
from utils.tools import allocate_values_to_nested_list
from entities import Class, Subject, Timetable
from storage.tables import ClassTable, AdministratorTable

router = Router(name='edit_configuretion')
router.message.filter(ChatTypeFilter('private'))


# TODO чтобы нельзя было удалить главного админа
# TODO кнопка отмены при удалении админа

class OneDayTimetaleBuilder():
    def __init__(self, timetable: Timetable, weekday: Weekday):
        self.timetable = timetable
        self.weekday = weekday
        self._lesson_cursor = 0
    def get_current_lesson(self) -> Subject | list:
        return self.timetable[self._lesson_cursor]
    def up_subject(self):
        self._lesson_cursor += 1
        if self._lesson_cursor == len(self.timetable):
            self._lesson_cursor -= 1
            raise IndexError(f'{self!r} out of range')


def IKM(x):
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=i[0], callback_data=i[1]) for i in x1] for x1 in x])

def _choosing_value_to_edit_kwargs(class_: Class):
    kwargs = {
        'text': class_.get_information_string(),
        'reply_markup': EditConfigureInlineKeyboardMarkup.choose_value_to_edit
    }
    return kwargs

def _administrators_to_str(administrators: list[str], creator: str) -> str:
    string = '\n'.join([
        (f'@{admin}' + 
            (' <i>(создатель)</i>' if admin == creator else '')) 
        for admin in administrators
    ])
    return string

def timetable_changing_kwargs(weekday_to_change: Weekday, tt_to_change: Timetable, subjects: list, subject_cursor: int):
    kwargs = {'text': format_answer_timtable_making(
            weekday_to_change, list(tt_to_change), 
            f'Выберите новый предмет под номером {subject_cursor+1} или пропустите его',
            cursor=subject_cursor
        ),
        'reply_markup': InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Пропустить', callback_data=f'ttchangingsubject_{tt_to_change[subject_cursor].encode()}')]
            ] + allocate_values_to_nested_list(
                [
                    InlineKeyboardButton(text=sj.name, callback_data=f'ttchangingsubject_{sj.encode()}')
                    for sj in subjects
                ], 3
            )
        )}
    return kwargs


class _StateData(Enum):
    class_ = 'class'
    timetble_builder = 'timetable_builder'


@router.callback_query(ConfigureState.edit_or_new_class_choosing, F.data.startswith('editcfgbegin_'))
async def begin_cfg_edit(callback: CallbackQuery, state: FSMContext):
    class_id = int(callback.data.split('_')[1])
    class_ = Class.from_table_value(ClassTable(_class_id=class_id))
    await state.set_data({_StateData.class_: class_})
    await state.set_state(EditConfigureState.choosing_value_to_edit)
    return await callback.message.edit_text(**_choosing_value_to_edit_kwargs(class_))

@router.callback_query(EditConfigureState.classname_edited, F.data == 'classnameedited')
@router.callback_query(EditConfigureState.adminlist_change_denied, F.data == 'adminlistchange_denied')
@router.callback_query(EditConfigureState.adminlist_changed, F.data == 'adminlist_changed')
@router.callback_query(EditConfigureState.timetable_changing_end, F.data == 'ttchangingend')
async def intermediate_begin(callback: CallbackQuery, state: FSMContext):
    class_ = (await state.get_data())[_StateData.class_]
    await state.set_state(EditConfigureState.choosing_value_to_edit)
    return await callback.message.edit_text(**_choosing_value_to_edit_kwargs(class_))

@router.callback_query(EditConfigureState.choosing_value_to_edit, F.data.startswith('editclass_'))
@router.callback_query(EditConfigureState.classname_edited, F.data == 'editclass_name')
async def choosed_value_to_edit_handler(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[1]
    class_ = (await state.get_data())[_StateData.class_]
    match action:
        case 'name':
            await state.set_state(EditConfigureState.setting_new_classname)
            return await callback.message.edit_text(f"Придумайте новое имя вашему классу")
        case 'subjects':
            await state.update_data({'subjects': class_.subjects, 'subject_groups': class_.get_groups_dict()})
            await state.set_state(EditConfigureState.changing_subject_list)
            return await callback.message.edit_text(
                f"Предметы <b>{class_.name}</b>:\n\n" +
                subject_list_to_str(class_.subjects, html_tags='i', numbered=True),
                reply_markup=ConfigureInlineKeyboardMarkup.subjects_list_changing
            )
        case 'administrators':
            await state.set_state(EditConfigureState.changing_admin_list)
            return await callback.message.edit_text(
                f'Администраторы <b>{class_.name}</b>:\n\n' + 
                _administrators_to_str(class_.administrators, class_.creator),
                reply_markup=EditConfigureInlineKeyboardMarkup.administrators_list_changing
            )
        case 'timetable':
            await state.set_state(EditConfigureState.choosing_day_for_timetable_change)
            return await callback.message.edit_text(
                f"Какой день вы хотите изменить?",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=wd.accusative.title(), callback_data=f'ttchangingday_{int(wd)}') for wd in weekdays_for_row]
                    for weekdays_for_row in allocate_values_to_nested_list(class_.weekdays, 2)
            ]))
        case 'cancel':
            classes = AdministratorTable(class_.creator).get_classes()
            await state.set_state(ConfigureState.edit_or_new_class_choosing)
            return await callback.message.edit_text(
                format_answer_start_configure(len(classes)),
                reply_markup=ConfigureInlineKeyboardMarkup.get_edit_or_new_cfg_choosing_markup(classes, 'editcfgbegin', 'newcfgbegin')
            )

@router.message(EditConfigureState.setting_new_classname, F.text)
async def get_new_classname(message: Message, state: FSMContext):
    new_classname = message.text
    class_: Class = (await state.get_data())[_StateData.class_]
    old_name = class_.name
    if ClassTable.validate_name(new_classname):
        class_.update_name(new_classname)
        await state.set_state(EditConfigureState.classname_edited)
        return await message.answer(
            f'Изменил имя вашего класса "<b>{old_name}</b>" -> "<b>{new_classname}</b>"',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Готово', callback_data='classnameedited'),
                 InlineKeyboardButton(text='Изменить', callback_data='editclass_name')]
            ]))
    elif new_classname == old_name:
        await state.set_state(EditConfigureState.classname_edited)
        return await message.answer(
            f"Это то же самое название. Вы хотите его изменить?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Оставить', callback_data='classnameedited'),
                 InlineKeyboardButton(text='Изменить', callback_data='editclass_name')]
            ]))
    else:
        await state.set_state(EditConfigureState.setting_new_classname)
        return await message.answer(
            f'Класс с таким названием уже существует. Попробуйте еще раз'
        )

ChangingSubjectListHandlerFactory(
    router,
    EditConfigureState.changing_subject_list,
    EditConfigureState.choosing_value_to_edit,
    'subjects',
    'subject_groups',
    lambda d: d[_StateData.class_].save_subject_list_changes(),
    after_message_kwargs_getter=lambda state_data: _choosing_value_to_edit_kwargs(state_data[_StateData.class_]),
    after_message_by_state_data=True
)

@router.callback_query(EditConfigureState.changing_admin_list, F.data.startswith('adminlistchange'))
@router.callback_query(EditConfigureState.adminlist_changed, F.data == 'adminlistchange_add' | F.data == 'adminlistchange_remove')
async def changed_admin_list(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[1]
    class_ = (await state.get_data())[_StateData.class_]
    if callback.from_user.username == class_.creator:
        match action:
            case 'add':
                await state.set_state(EditConfigureState.waiting_for_new_admin_username)
                await callback.answer()
                return await callback.message.edit_text(
                    'Введите имя пользователя нового админа (начиная с @)'
                )
            case 'remove':
                await state.set_state(EditConfigureState.waiting_for_removed_admin)
                return await callback.message.edit_text(
                    'Выберите администратора для удаления',
                    reply_markup=EditConfigureInlineKeyboardMarkup.get_all_administrators_markup(class_.administrators)
                )
            case 'finish':
                await state.set_state(EditConfigureState.adminlist_changed)
                return await callback.message.edit_text(
                    'Итоговый список администраторов: \n\n' + _administrators_to_str(class_.administrators, class_.creator),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text='Добавить', callback_data='adminlistchange_add'),
                        InlineKeyboardButton(text='Удалить', callback_data='adminlistchange_remove')],
                        [InlineKeyboardButton(text='Готово', callback_data='adminlist_changed')]
                    ])
                )
    else:
        await state.set_state(EditConfigureState.adminlist_change_denied)
        return await callback.message.edit_text(
            f'Только создатель класса {class_.creator} может изменять список администраторов',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Назад', callback_data='adminlistchange_denied')]])
        )

@router.message(EditConfigureState.waiting_for_new_admin_username, F.text.startswith('@'))
async def get_new_username(message: Message, state: FSMContext):
    new_admin = message.text[1:]
    class_ = (await state.get_data())[_StateData.class_]
    class_.add_administrator(new_admin)
    await state.set_state(EditConfigureState.changing_admin_list)
    return await message.answer(
        f'Добавил нового администратора @{new_admin} в класс {class_.name}',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Добавить', callback_data='adminlistchange_add'),
            InlineKeyboardButton(text='Готово', callback_data='adminlistchange_finish')]
        ])
    )

@router.callback_query(EditConfigureState.waiting_for_removed_admin)
async def remove_admin(callback: CallbackQuery, state: FSMContext):
    class_ = (await state.get_data())[_StateData.class_]
    removed_admin = callback.data.split('_')[1]
    class_.remove_administrator(removed_admin)
    await state.set_state(EditConfigureState.changing_admin_list)
    return await callback.message.edit_text(
        f'Удален администратор @{removed_admin}',
        reply_markup=IKM([[('Продолжить', 'adminlistchange_remove'), ('Готово', 'adminlistchange_finish')]])
    )

@router.callback_query(EditConfigureState.choosing_day_for_timetable_change, F.data.startswith('ttchangingday_'))
async def timetable_changing(callback: CallbackQuery, state: FSMContext):
    weekday_to_change = Weekday(int(callback.data.split('_')[1]))
    class_ = (await state.get_data())[_StateData.class_]
    tt_to_change = class_.timetables[weekday_to_change]
    update_builder = OneDayTimetaleBuilder(tt_to_change, weekday_to_change)
    await state.update_data({_StateData.timetble_builder: update_builder})

    subject_cursor = update_builder.lesson_cursor
    kb = [
        [InlineKeyboardButton(
            text='Пропустить',
            callback_data=f'ttchangingsubject_{tt_to_change[subject_cursor].encode()}'
        )],
        *allocate_values_to_nested_list([
            InlineKeyboardButton(text=sj.name, callback_data=f'ttchangingsubject_{sj.encode()}')
            for sj in class_.subjects
        ], 3)
    ]
    await state.set_state(EditConfigureState.choosing_subject_to_insert)
    return await callback.message.edit_text(
        format_answer_timtable_making(
            weekday_to_change, list(tt_to_change),
            f'Выберите новый предмет для {subject_cursor+1} урока или пропустите его',
            cursor=subject_cursor
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb)
    )

@router.callback_query(EditConfigureState.choosing_subject_to_insert, F.data.startswith('ttchangingsubject_'))
async def lesson_changed(callback: CallbackQuery, state: FSMContext):
    inserted_subject = Subject.decode(callback.data.split('_')[1])
    class_: Class = (await state.get_data())[_StateData.class_]
    weekday_to_change = class_._tt_updating_builder.weekday_cursor
    timetable = class_.timetables[weekday_to_change]
    inserting_result = class_.update_timetable(inserted_subject) # 0 or 2 because we build only one day
    if inserting_result == 0:
        await state.set_state(EditConfigureState.choosing_subject_to_insert)
        return await callback.message.edit_text(**timetable_changing_kwargs(
            weekday_to_change, timetable, class_.subjects,
            class_._tt_updating_builder.subject_cursor
        ))
    else:
        await state.set_state(EditConfigureState.timetable_changing_end)
        return await callback.message.edit_text(
            format_answer_timtable_making(weekday_to_change, list(timetable), ' '),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Завершить', callback_data='ttchangingend')]])
        )


