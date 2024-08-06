
import datetime

from . import Subject, Class
from utils import Weekday
from storage.tables import HomeworkTable, LessonTable



class Homework:

    def __init__(
        self, subject: Subject, class_: Class, text: str, 
        weekday: Weekday, week: int, position: int, year: int=datetime.date.today().year
    ):
        self.subject = subject
        self.class_ = class_
        self.text = text
        self.weekday = weekday
        self.week = week
        self.position = position
        self.year = year

    def save(self):
        HomeworkTable.save_new_homework(self)

    @classmethod
    def get(cls, class_: Class, subject: Subject, weekday: Weekday, week: int, position: int, year: int):
        text = HomeworkTable.get_text_by_week_weekday(
            subject_name=subject.name, class_table=class_.connected_table_value, 
            weekday=weekday, week=week, position=position, year=year
        )
        return cls(subject, class_, text, weekday, week, position, year)
    
    def slot(self, now_week: int):
        return (self.weekday, self.position, self.week > now_week)

    def __str__(self) -> str:
        return f"Домашнее задание по {self.subject.name} на {self.weekday.accusative}, {self.position} урок:\n<b>{self.text}</b>"

    def get_small_string(self) -> str:
        return f"{self.position}. <i>{self.subject}</i>: <b>{self.text}</b>"

    @classmethod
    def get_recent(cls, subject: Subject, class_: Class):
        table_values = HomeworkTable.get_recent_homeworks_for_subject(subject.name, class_.connected_table_value)
        return [cls.from_table_value(v) for v in table_values]

    @classmethod
    def from_table_value(cls, table_value: HomeworkTable):
        lesson_table = table_value.values.lessonID
        return cls(
            Subject(lesson_table.values.subjectID.values.subjectname),
            Class.from_table_value(lesson_table.values.classID),
            table_value.values.text,
            Weekday(lesson_table.values.weekday),
            table_value.values.week,
            lesson_table.values.position,
            table_value.values.year
        )   
    
    @classmethod
    def get_all_homeworks_for_day(cls, class_: Class, weekday: Weekday, week: int):
        table_values = HomeworkTable.get_all_for_day(class_.connected_table_value, weekday, week)
        return [cls.from_table_value(v) for v in table_values]
