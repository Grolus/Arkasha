from model import Lesson

from .subject import format_subject

from config.constants import GROOPED_LESSON_SUBJECTS_SEPARATOR, EMPTY_LESSON_VIEW

def format_lesson(lesson: Lesson) -> str:
    if not lesson:
        return EMPTY_LESSON_VIEW
    return GROOPED_LESSON_SUBJECTS_SEPARATOR.join([
        format_subject(sj) 
        for sj in lesson.subjects
    ])
    