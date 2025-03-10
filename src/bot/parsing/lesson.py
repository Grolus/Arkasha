
from .subject import parse_subject
from ._parsing_utils import strip_of_brackets

from model import Lesson
from logers import parse_loger

def parse_lesson(text: str) -> Lesson:
    parse_loger.debug(f'Parsing Lesson: {text}')
    if ',' not in text:
        return Lesson(subjects=[
            parse_subject(text)
        ])
    else:
        subjects = []

        for subject_string in strip_of_brackets(text).split(','):
            subject = parse_subject(subject_string)
            subjects.append(subject)
        return Lesson(subjects=subjects)
