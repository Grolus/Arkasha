from model import Lesson

from .subject import format_subject

from config.constants import GROOPED_LESSON_SUBJECTS_SEPARATOR, EMPTY_LESSON_VIEW

def format_lesson(lesson_list: list[Lesson]) -> str:
    if not lesson_list:
        return EMPTY_LESSON_VIEW
    return GROOPED_LESSON_SUBJECTS_SEPARATOR.join([
        format_subject(lesson.subject) 
        for lesson in lesson_list
    ])
    