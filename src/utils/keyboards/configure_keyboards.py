
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from ..weekday import Weekday
from entities import Subject, EmptySubject

def _subject_to_button(subject: Subject | EmptySubject, callback_data_prefix: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=str(subject), callback_data=f'{callback_data_prefix}_{subject.encode()}')

class ConfigureInlineKeyboardMarkup:
    subjects_list_changing = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Добавить', callback_data='subjectlistchange_add'),
             InlineKeyboardButton(text='Удалить', callback_data='subjectlistchange_remove')],
             [InlineKeyboardButton(text='Готово', callback_data='subjectlistchange_finish')]
        ]
    )
    choosing_studytype = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='4 дня', callback_data='studytype_4'),
         InlineKeyboardButton(text='5 дней', callback_data='studytype_5'),
          InlineKeyboardButton(text='6 дней', callback_data='studytype_6')]
          ]
    )
    choosing_timetable_way = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='По кнопкам (рекомендовано)', callback_data='timetableway_smart'),
         #InlineKeyboardButton(text='Вручную', callback_data='timetableway_manually')
         ]
    ])

    def get_timetable_ending_markup(now_weekday: Weekday, is_last_day: bool=False) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Ещё раз', callback_data='ttend_again'),
            InlineKeyboardButton(text=f'Перейти к {(now_weekday+1).dativ}' 
                                if not is_last_day else 'Завершить', 
                                callback_data='ttend_next'
                                if not is_last_day else 'ttend_complete')]
        ])
    
    def get_all_subjects_markup(subjects: list[Subject]) -> InlineKeyboardMarkup:
        keyboard: list[list[InlineKeyboardButton]] = []
        callback_prefix = 'ttsubject'
        for i, subject in enumerate(subjects):
            if i % 3 == 0:
                keyboard.append([_subject_to_button(subject, callback_prefix), None, None])
            else:
                keyboard[i // 3][i % 3] = _subject_to_button(subject, callback_prefix)
        keyboard.append([_subject_to_button(EmptySubject(), callback_prefix)])
        for row in keyboard:
            while None in row:
                row.remove(None)
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    def get_edit_or_new_cfg_choosing_markup(existed_classes):
        return InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f'Класс {class_.values.classname}', callback_data=f'editcfgbegin_{class_.id_}') 
                 ] for class_ in existed_classes
            ] + [[InlineKeyboardButton(text='Создать новый класс', callback_data='newcfgbegin')]])

class EditConfigureInlineKeyboardMarkup:
    choose_value_to_edit = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Изменить имя', callback_data='editclass_name')],
        [InlineKeyboardButton(text='Изменить список предметов', callback_data='editclass_subjects')],
        [InlineKeyboardButton(text='Изменить состав администраторов', callback_data='editclass_administrators')],
        [InlineKeyboardButton(text='Изменить расписание', callback_data='editclass_timetable')],
        [InlineKeyboardButton(text='Отмена', callback_data='editclass_cancel')]
    ])
    administrators_list_changing = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Добавить', callback_data='adminlistchange_add'),
             InlineKeyboardButton(text='Удалить', callback_data='adminlistchange_remove')],
             [InlineKeyboardButton(text='Готово', callback_data='adminlistchange_finish')]
        ]
    )
    def get_all_administrators_markup(admins: list[str]):
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=admin, callback_data=f'removedadmin_{admin}')]
            for admin in admins
        ])
