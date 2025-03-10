from model import Timetable

from aiogram import html

from .lesson import format_lesson

def format_timetable_full(timetable: Timetable) -> str:
    result_string = ""
    for weekday, lessons in timetable.timetable_dict.items():
        result_string += html.bold(weekday.name_ru.capitalize()) + ":\n"
        for i, lesson in enumerate(lessons):
            position = i + 1
            result_string += f' {position}. {format_lesson(lesson)}\n'
    return result_string

