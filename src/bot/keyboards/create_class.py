from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ..public import get_prompt_from_file

def _generate(kb: list[list[tuple[str, str]]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=text, callback_data=callback_data) 
            for text, callback_data in row
        ]
        for row in kb
    ])

class_name_typed = _generate([[(
    get_prompt_from_file("keyboard/cancel_class_creation_button.txt"),
    'cancel_class_creation'
)]])

confirming_created_class = _generate([[
    (
        'Готово',
        'confirmed_class'
    ),
    (
        'Изменить имя',
        'edit_class_name'
    ),
    (
        'Изменить расписание',
        'edit_class_timetable'
    )
]])

