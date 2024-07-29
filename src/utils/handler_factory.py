
from typing import Callable, Literal
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .strings import subject_list_to_str, format_answer_changed_subject_list
from .keyboards import ConfigureInlineKeyboardMarkup as InlineMarkup
from entities import Subject


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


class ChangingSubjectListHandlerFactory:
    def __init__(
            self, router: Router, changing_state: FSMContext, 
            next_state: FSMContext, 
            subject_list_getter: Callable[[str], list[Subject]],
            *,
            subject_list_add_func: Callable[[str, Subject], None]=..., 
            subject_list_remove_func: Callable[[str, Subject], None]=...,
            after_message_text: str=None,
            after_message_reply_markup: InlineKeyboardMarkup=None, 
            after_message_kwargs_getter: Callable[[CallbackQuery | Message | None], 
                                                  dict[Literal['text']: str, 
                                                       Literal['reply_markup']: InlineKeyboardMarkup | None]]=None
            ):
        """Handler generator for changing subject list.\n
            :param router: `Router` object to register handlers
            :param changig_state: `FSMContext` object. Bot will be in this state while user changing subject list
            :param next_state: `FSMContext` object. Bot will be in this state *after* changing subject list
            :param subject_list_getter: Function to get `list` to be changed (*Mutable*). Will be used as `subject_list_getter(username)`
            :param subject_list_add_func: [Optional] function to add new subject to `dynamic_subject_list` that require username and subject
                Default: `subject_list_getter(username).append`
            :param subject_list_remove_func: [Optional] function to remove existing subject 
                from `dynamic_subject_list` that require username and subject. Default: `subject_list_getter(username).remove`
            :params after_*: this params describe message to be sent after changing subject list. Fill only "kwargs" or dont fill it.
            
            NOTE: 'text' in after message will be formated with string-formated subject list"""
        if (after_message_text is None or after_message_reply_markup is None) == after_message_kwargs_getter is None:
            raise AttributeError(
                f'{self.__class__.__name__!r}: you should give '+
                '`after_message_text` or/and `after_message_reply_markup` *OR* `after_message_kwargs_getter`'
                )
        if after_message_kwargs_getter is None:
            after_message_kwargs_getter = lambda x: {'text': after_message_text, 'reply_markup': after_message_reply_markup}
        if subject_list_add_func is ...:
            subject_list_add_func = lambda username, subject: subject_list_getter(username).append(subject)
        if subject_list_remove_func is ...:
            subject_list_remove_func = lambda username, subject: subject_list_getter(username).remove(subject)

        def get_kwargs(callback_or_message, sj_string: str):
            kwargs = after_message_kwargs_getter(callback_or_message)
            kwargs['text'] = kwargs['text'].format(sj_string)
            return kwargs
        @router.callback_query(changing_state, F.data.startswith('subjectlistchange_'))
        async def change_subject_list(callback: CallbackQuery, state: FSMContext): 
            action = callback.data.split('_')[1]
            match action:
                case 'add':
                    await callback.message.answer(
                        'Введите название нового предмета ' +
                        '(только буквы, можно перечислить несколько предметов через запятую)...'
                        )
                    await callback.answer()
                case 'remove':
                    if subject_list_getter(callback.from_user.username):
                        await callback.message.edit_text(
                            'Выберите предмет для удаления:', 
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                    [InlineKeyboardButton(text=subject.name, callback_data=f'removedsubject_{subject.encode()}')]
                                    for subject in subject_list_getter(callback.from_user.username)
                                ]))
                    else: 
                        await callback.message.edit_text(
                            'Список предметов пуст!',
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                                    InlineKeyboardButton(text='Добавить', callback_data='subjectlistchange_add')]]))
                    await callback.answer()
                case 'finish':
                    await callback.message.edit_text(
                        **get_kwargs(callback, subject_list_to_str(subject_list_getter(callback.from_user.username), html_tags='b'))
                        )
                    await state.set_state(next_state)
                    await callback.answer()

        @router.message(changing_state, F.text)
        async def add_subject(message: Message, state: FSMContext): # TODO validate (only letters)
            new_subjects_names = list(map(str.strip, message.text.split(',')))
            new_subjects_names = [i for i in new_subjects_names if i]
            for i in range(len(new_subjects_names)):
                new_subjects_names[i] = new_subjects_names[i][0].upper() + new_subjects_names[i][1:]
            subjects_to_add, already_exists_subjects = _new_subjects_master(new_subjects_names, subject_list_getter(message.from_user.username))
            for subject in subjects_to_add:
                subject_list_add_func(message.from_user.username, subject)
            answer = format_answer_changed_subject_list((
                ('Добавлены предметы' if len(subjects_to_add) > 1
                else 'Добавлен предмет') + f' <i>{", ".join(map(str, subjects_to_add))}</i>') if subjects_to_add else '' +
                ((f'\n(Предмет{"ы" if len(already_exists_subjects) > 1 else ""} ' +
                f'<i>{", ".join(map(str, already_exists_subjects))}</i> уже есть в списке)') if already_exists_subjects else ''),
                subject_list_getter(message.from_user.username))
            
            await message.answer(answer, reply_markup=InlineMarkup.subjects_list_changing)

        @router.callback_query(changing_state, F.data.startswith('removedsubject_'))
        async def remove_subject(callback: CallbackQuery, state: FSMContext): # TODO cancel button
            removed_subject_code = callback.data.split('_')[1]
            removed_subject = Subject.decode(removed_subject_code)
            subject_list_remove_func(callback.from_user.username, removed_subject)
            await callback.message.edit_text(
                format_answer_changed_subject_list(
                    f'Удалён предмет {removed_subject}.', subject_list_getter(callback.from_user.username)
                ), 
                reply_markup=InlineMarkup.subjects_list_changing
                )
            