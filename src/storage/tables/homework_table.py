
from ..connection import DBConection
from .base import BaseTable

class HomeworkTable(BaseTable):
    _table_name = 'homework'

    @classmethod
    def save_new_homework(cls, homework):
        from . import LessonTable, SubjectTable
        HomeworkTable(
            LessonTable(
                homework.class_.connected_table_value,
                SubjectTable(homework.subject.name),
                int(homework.weekday),
                homework.position
            ),
            homework.text,
            homework.week,
            homework.year
        ).insert()


