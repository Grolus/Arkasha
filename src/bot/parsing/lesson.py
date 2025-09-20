
from .subject import parse_subject
from ._parsing_utils import strip_of_brackets

from model import Lesson
from logers import parse_loger

def parse_lesson(text: str) -> list[Lesson]:
    parse_loger.debug(f'Parsing Lesson: {text}')
    if ',' not in text:
        return [Lesson(subject=parse_subject(text))]
    else:
        lessons = []

        for subject_string in strip_of_brackets(text).split(','):
            subject = parse_subject(subject_string)
            lessons.append(Lesson(subject=subject))
        return lessons
