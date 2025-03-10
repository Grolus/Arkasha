from model import Lesson

from .subject import format_subject

from config.constants import GROOPED_LESSONS_SEPARATOR

def format_lesson(lesson: Lesson) -> str:
    return GROOPED_LESSONS_SEPARATOR.join([format_subject(sj) for sj in lesson.subjects])
    