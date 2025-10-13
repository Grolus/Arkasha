

from._parsing_utils import split_with_ignoring
from .weekday import parse_weekday
from .lesson import parse_lesson

from model import Timetable, Lesson, DailyTimetable
from exceptions import ParsingError
from config.constants import EMPTY_LESSON_INPUT
from logers import parse_loger

TIMETABLE_LINE_SEPARATOR = ":"
LESSONS_SEPARATOR = ","

def parse_timetable(text: str) -> Timetable:
    """
    Извлекает расписание из строки в формате:\n\n
    ДЕНЬ НЕДЕЛИ: предмет, (предмет 1 группы, предмет 2 группы), ..., предмет\n
    ДЕНЬ НЕДЕЛИ: ОКНО, предмет, ..., предмет\n

    :param text: Текст с расписанием
    :return: `Timetable`
    :raises: `ParsingError`, если строка в неподходящем формате
    """
    parse_loger.debug(f"Parsing Timetable: {text}")
    day_lines = text.split('\n')
    timetable_dict = {}
    for day_line in day_lines:
        if not TIMETABLE_LINE_SEPARATOR in day_line:
            raise ParsingError(text, Timetable)
        weekday_string, lessons_string = day_line.split(TIMETABLE_LINE_SEPARATOR)
        lessons_string = lessons_string.strip()
        weekday = parse_weekday(weekday_string)
        lessons = _parse_lessons(lessons_string)
        timetable_dict[weekday] = DailyTimetable(lessons=lessons)
    return Timetable(
        timetable_dict=timetable_dict
    )

def _parse_lessons(text: str) -> list[list[Lesson]]:
    lessons = []
    for i, lesson_string in enumerate(split_with_ignoring(text, LESSONS_SEPARATOR, '()')):
        lesson_string = lesson_string.strip()
        if lesson_string == EMPTY_LESSON_INPUT:
            lessons.append(None)
            continue
        lesson = parse_lesson(lesson_string)
        lessons.append(lesson)
    return lessons
