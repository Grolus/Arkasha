
from typing import Callable, Literal
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from .strings import subject_list_to_str, format_answer_changed_subject_list, format_html_tags
from .keyboards import ConfigureInlineKeyboardMarkup as InlineMarkup
from .tools import allocate_values_to_nested_list
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

def _subject_to_callback(subject: Subject, callback_data_prefix: str) -> str:
    "'{callback_data_prefix}_{subject.name}'"
    return f"{callback_data_prefix}_{subject.name}"

def _parse_new_subjects(text: str, existing_subjects: list[Subject]) -> tuple[list[Subject], list[Subject]]:
    new_subjects_names = [i.capitalize() for i in map(str.strip, text.split(',')) if i] # not-empty-string words
    subjects_to_add, already_exists_subjects = _new_subjects_master(new_subjects_names, existing_subjects)
    return subjects_to_add, already_exists_subjects

def _enumerate_subjects(subjects: list[Subject], tags: str='i', sep: str=','):
    return format_html_tags(tags, sep.join(map(str, subjects)))

def _format_changelog_string(subjects_to_add: list[Subject], exsisting_subjects: list[Subject]) -> str:
    changelog_string = ''
    if subjects_to_add:
        if len(subjects_to_add) > 1:
            changelog_string += 'Добавлены предметы'
        else:
            changelog_string += 'Добавлен предмет'
        changelog_string += _enumerate_subjects(subjects_to_add)
        changelog_string += '\n'
    if exsisting_subjects:
        changelog_string += '(Предмет'
        if len(exsisting_subjects) > 1:
            changelog_string += 'ы '
        changelog_string += _enumerate_subjects(exsisting_subjects)
    return changelog_string
        

class ChangingSubjectListHandlerFactory:
    def __init__(
            self, router: Router, changing_state: FSMContext, 
            next_state: FSMContext, 
            subject_list_keyword: str,
            subject_groups_dict_keyword: str,
            *,
            after_message_text: str | None=None,
            after_message_reply_markup: InlineKeyboardMarkup | None=None, 
            after_message_kwargs_getter: Callable[[CallbackQuery | Message | None], 
                                                  dict] | None=None,
            after_message_by_state_data: bool=False
            ):
        """Handler generator for changing subject list.\n
            :param router: `Router` object to register handlers
            :param changig_state: `FSMContext` object. Bot will be in this state while user changing subject list
            :param next_state: `FSMContext` object. Bot will be in this state *after* changing subject list
            
            :params after_*: this params describe message to be sent after changing subject list. Fill only "kwargs" or dont fill it.
            
            NOTE: 'text' in after message will be formated with string-formated subject list"""
        if (after_message_text is None or after_message_reply_markup is None) == after_message_kwargs_getter is None:
            raise AttributeError(
                f'{self.__class__.__name__!r}: you should give '+
                '`after_message_text` or/and `after_message_reply_markup` *OR* `after_message_kwargs_getter`'
                )
        
        if after_message_kwargs_getter is None:
            after_message_kwargs_getter = lambda x: {'text': after_message_text, 'reply_markup': after_message_reply_markup}

        def get_kwargs(callback_or_message, sj_string: str):
            kwargs = after_message_kwargs_getter(callback_or_message)
            kwargs['text'] = kwargs['text'].format(sj_string)
            return kwargs
        
        @router.callback_query(changing_state, F.data.startswith('subjectlistchange_'))
        async def change_subject_list(callback: CallbackQuery, state: FSMContext): 
            action = callback.data.split('_')[1]
            subjects = (await state.get_data())[subject_list_keyword]
            match action:
                case 'add':
                    await callback.answer()
                    return await callback.message.answer(
                        'Введите название нового предмета ' +
                        '(только буквы, можно перечислить несколько предметов через запятую)...'
                        )
                case 'remove':
                    await callback.answer()
                    if subjects:
                        return await callback.message.edit_text(
                            'Выберите предмет для удаления:', 
                            reply_markup=InlineMarkup.get_all_subjects_markup(subjects, 'removedsubject')
                        )
                    else: 
                        return await callback.message.edit_text(
                            'Список предметов пуст!',
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                                InlineKeyboardButton(text='Добавить', callback_data='subjectlistchange_add')
                            ]]))
                case 'groups':
                    return await callback.message.edit_text(
                        'Выберите предмет, который является разделённым на группы',
                        reply_markup=InlineMarkup.get_all_subjects_markup(subjects, 'groupedsubject')
                    )
                case 'finish':
                    await state.set_state(next_state)
                    await callback.answer()
                    return await callback.message.edit_text(
                        **get_kwargs(callback if not after_message_by_state_data else (await state.get_data()), subject_list_to_str(subjects, html_tags='b'))
                    )

        @router.message(changing_state, F.text)
        async def add_subject(message: Message, state: FSMContext): # TODO validate (only letters)
            existing_subjects = (await state.get_data())[subject_list_keyword]
            subjects_to_add, already_exists_subjects = _parse_new_subjects(message.text, existing_subjects)
            for subject in subjects_to_add:
                existing_subjects.append(subject)
            
            answer = format_answer_changed_subject_list(
                _format_changelog_string(subjects_to_add, already_exists_subjects),
                existing_subjects
            )
            return await message.answer(answer, reply_markup=InlineMarkup.subjects_list_changing)

        @router.callback_query(changing_state, F.data.startswith('removedsubject_'))
        async def remove_subject(callback: CallbackQuery, state: FSMContext): # TODO cancel button
            removed_subject_code = callback.data.split('_')[1]
            removed_subject = Subject.decode(removed_subject_code)
            subjects = (await state.get_data())[subject_list_keyword]
            subjects.remove(removed_subject)
            return await callback.message.edit_text(
                format_answer_changed_subject_list(
                    f'Удалён предмет {removed_subject}.', subjects
                ), 
                reply_markup=InlineMarkup.subjects_list_changing
            )
            
        @router.callback_query(changing_state, F.data.startswith('groupedsubject_'))
        async def group_subject(callback: CallbackQuery, state: FSMContext):
            grouped_subject = Subject.decode(callback.data.split('_')[1])
            data = await state.get_data()
            subject_groups = data[subject_groups_dict_keyword]
            subjects = data[subject_list_keyword]
            subject_groups[grouped_subject] = 2   # <---
            return await callback.message.edit_text(
                format_answer_changed_subject_list(
                    f'Теперь <b>{grouped_subject}</b> разделён на 2 группы',
                    subjects
                ),
                reply_markup=InlineMarkup.subjects_list_changing
            )