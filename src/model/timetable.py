from pydantic import BaseModel, Field
from typing_extensions import Self

from .class_ import Class
from .weekday import Weekday

from parse_utils import split_with_ignoring, strip_of_brackets
from config.constants import MAX_SUBJECT_NAME_LENGTH, MIN_SUBJECT_NAME_LENGTH, EMPTY_LESSON_INPUT
from exceptions import ParsingError
from logers import parse_loger

class Subject(BaseModel):
    name: str = Field(..., pattern=r'\w{' + str(MIN_SUBJECT_NAME_LENGTH) + ',' + str(MAX_SUBJECT_NAME_LENGTH) + '}')
    def __init__(self, name: str):
        super().__init__(name=name)
    @classmethod
    def parse(cls, text: str):
        parse_loger.debug(f'Parsing Subject: {text}')
        return cls(name=text.strip())

class Lesson(BaseModel):
    subjects: list[Subject]
    
    @classmethod
    def parse(cls, text: str):
        parse_loger.debug(f'Parsing Lesson: {text}')
        if ',' not in text:
            return cls(subjects=[
                Subject(name=text)
            ])
        else:
            subjects = []

            for subject_string in strip_of_brackets(text).split(','):
                subject = Subject.parse(subject_string)
                subjects.append(subject)
            return cls(subjects=subjects)

class Timetable(BaseModel):
    timetable_dict: dict[Weekday, dict[int, Lesson]]

    @classmethod
    def parse(cls, text: str) -> Self:
        """
        Извлекает расписание из строки в формате:\n\n
        ДЕНЬ НЕДЕЛИ: предмет, (предмет 1 группы, предмет 2 группы), ..., предмет\n
        ДЕНЬ НЕДЕЛИ: ОКНО, предмет, ..., предмет\n

        :param text: Текст с расписанием
        :return: `Timetable`
        :raises: `ParseError`, если строка в неподходящем формате
        """
        day_lines = text.split('\n')
        timetable_dict = {}
        for day_line in day_lines:
            if not ':' in day_line:
                raise ParsingError(text, cls)
            weekday_string, lessons_string = day_line.split(':')
            lessons_string = lessons_string.strip()
            weekday = Weekday.parse(weekday_string)
            lessons_dict = _parse_lessons(lessons_string)
            timetable_dict[weekday] = lessons_dict
        return cls(
            timetable_dict=timetable_dict
        )

            
def _parse_lessons(text: str) -> dict[int: Lesson]:
    lessons_dict = {}
    for i, lesson_string in enumerate(split_with_ignoring(text, ',', '()')):
        lesson_string = lesson_string.strip()
        if lesson_string == EMPTY_LESSON_INPUT:
            continue
        lesson = Lesson.parse(lesson_string)
        lessons_dict[i] = lesson
    return lessons_dict
