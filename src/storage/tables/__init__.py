
from .base import BaseTable
from .class_table import ClassTable
from .administrator_table import AdministratorTable
from .subject_table import SubjectTable
from .lesson_table import LessonTable
from .classadministrator_table import ClassAdministratorTable
from .classsubject_table import ClassSubjectTable
from .classweekday_table import ClassWeekdayTable
from .chat_table import ChatTable
from .homework_table import HomeworkTable

__all__ = (
    'BaseTable',
    'ClassTable',
    'AdministratorTable',
    'SubjectTable',
    'LessonTable',
    'ClassAdministratorTable',
    'ClassSubjectTable',
    'ClassWeekdayTable',
    'ChatTable',
    'HomeworkTable'
)