
from ..connection import DBConection
from .base import BaseTable

from exceptions import ValueNotFoundError
from utils import Weekday
from logers import database as loger

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
                homework.position,
                homework.group_number
            ),
            homework.text,
            homework.week,
            homework.year
        ).insert()

    @classmethod
    def get_text_by_week_weekday(cls, subject_name, class_table, group_number: int, weekday: Weekday, week: int, position: int, year: int) -> str:
        # subject, text, weekday, week, position, year
        from . import LessonTable, SubjectTable
        result = DBConection().query(
            f"SELECT hw.text FROM {cls._table_name} hw JOIN {LessonTable._table_name} l ON l.idLesson=hw.lessonID "
            f"WHERE l.subjectID={SubjectTable(subject_name).id_} AND l.position={position} AND hw.year={year} AND "
            f"l.classID={class_table.id_} AND l.weekday={int(weekday)} AND l.groupnumber={group_number} AND hw.week={week}"
        )
        if result:
            return result[0][0]
        else:
            raise ValueNotFoundError(
                f'{cls._table_name!r} doesn`t has row with {year=}, {position=}, {week=}, {weekday=}, {subject_name=}, {class_table=}'
            )

    @classmethod
    def get_awaible_homeworks_for_subject(cls, subject_name: str, class_table: 'ClassTable', now_weekday: Weekday, now_week: int): # type: ignore
        from . import SubjectTable, LessonTable
        now_weekday = int(now_weekday)
        result = DBConection().query(
            f"""SELECT homework.text, lesson.weekday, homework.week, lesson.position, homework.year
            FROM homework
                JOIN lesson ON homework.lessonID=lesson.idLesson 
            WHERE lesson.subjectID={SubjectTable(subject_name).id_} AND lesson.classID={class_table.id_}
                AND (
                    (homework.week={now_week} AND lesson.weekday >={now_weekday}) OR 
                    (homework.week>{now_week})
                )
            ORDER BY homework.year DESC, homework.week DESC, 
                    lesson.weekday DESC, lesson.position DESC
        """)
        if result:
            table_homeworks = [cls(
                LessonTable(
                    class_table,
                    SubjectTable(subject_name),
                    weekday,
                    position
                ),
                text, week, year
            ) for text, weekday, week, position, year in result
            ]
            loger.debug(f"Collected homework tables: {table_homeworks}")
            return table_homeworks
        else:
            return []

    @classmethod
    def get_all_for_day(cls, class_table, weekday, week):
        result = DBConection().query(
            f"SELECT * FROM homework JOIN lesson ON homework.lessonID=lesson.idLesson "
            f"WHERE lesson.classID={class_table.id_} AND lesson.weekday={int(weekday)} AND homework.week={week}"
        )
        return [cls.from_selected_row(row) for row in result]

    @classmethod
    def get_last_for_subject(cls, subject_name, class_table):
        from . import SubjectTable, LessonTable
        result = DBConection().query(
            f"""SELECT homework.text, lesson.weekday, homework.week, lesson.position, homework.year
            FROM homework
                JOIN lesson ON homework.lessonID=lesson.idLesson 
            WHERE lesson.subjectID={SubjectTable(subject_name).id_} AND lesson.classID={class_table.id_}
            ORDER BY homework.year DESC, homework.week DESC, 
                    lesson.weekday DESC, lesson.position DESC
            LIMIT 1"""
        )
        if result:
            text, weekday, week, position, year = result[0]
            homework = cls(
                LessonTable(
                    class_table,
                    SubjectTable(subject_name),
                    weekday,
                    position
                ),
                text, week, year
            )
            loger.debug(f"Collected homework table: {homework}")
            return homework
        else: 
            return None
