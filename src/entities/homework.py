
import datetime

from . import Subject, Class
from utils import Weekday
from storage.tables import HomeworkTable, LessonTable
from utils.slot import slot_to_string


def is_position_needed(class_: Class, subject: Subject, weekday: Weekday):
    return list(class_.timetables[weekday]).count(subject) > 1

class Homework:

    def __init__(
        self, subject: Subject, class_: Class, text: str, 
        weekday: Weekday, week: int, position: int | None=None, year: int=datetime.date.today().year # it`s ugly, but it`s working 
    ):
        self.subject = subject
        self.class_ = class_
        self.text = text
        self.weekday = weekday
        self.week = week
        self.year = year
        if position is None:
            if not is_position_needed(self.class_, self.subject, self.weekday):
                self.position = self.class_.timetables[self.weekday].position(self.subject)
        else:
            self.position = position
        

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

    def get_string(self, now_week: int) -> str:
        return (f'Задание по предмету <b>{self.subject.name}</b>:\n'
        f'<i>{self.text}</i>\n\n'
        f'(на {slot_to_string(self.slot(now_week), case="accusative", title=False)})')

    def get_small_string(self) -> str:
        return f"{self.position}. <i>{self.subject}</i>: <b>{self.text}</b>"

    @classmethod
    def get_awaible(cls, subject: Subject, class_: Class, now_weekday: Weekday, now_week: int):
        table_values = HomeworkTable.get_awaible_homeworks_for_subject(subject.name, class_.connected_table_value, now_weekday, now_week)
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
    
    @classmethod
    def get_last_for_subject(cls, subject, class_):
        table_value = HomeworkTable.get_last_for_subject(subject.name, class_.connected_table_value)
        if table_value:
            return cls.from_table_value(table_value)
        else:
            return None

    def change_slot(self, new_slot: tuple):
        self.weekday, self.position, is_for_next_week = new_slot
        self.week += is_for_next_week
