
from typing import Literal

from .subject import Subject, EmptySubject
from utils import Weekday
from storage.tables import LessonTable, SubjectTable

class Timetable:
    def __init__(self, subjects: list[Subject | EmptySubject]):
        self.lessons = [s for s in subjects]
        self.table_subjects = tuple(SubjectTable(sj.name) for sj in self.lessons)
    def __str__(self):
        return '\n'.join([f'{i+1}. {subject.name}' for i, subject in enumerate(self.subject)])
    def __getitem__(self, index: int):
        return self.lessons[index]
    def __setitem__(self, index: int, new_value: Subject):
        if not isinstance(new_value, Subject):
            raise TypeError('Timetable can recive only \'Subject\' objects')
        self.lessons[index] = new_value
    def __iter__(self):
        return iter(self.lessons)
    def __len__(self):
        return len(self.lessons)
    
    def update_lesson(self, class_: 'Class', new_subject: Subject): # type: ignore
        pos = class_._subject_cursor
        old_subject = self[pos]
        LessonTable(
            **class_.connected_table_value.as_kwargs(), 
            **SubjectTable(old_subject.name),
            weekday=int(class_._weekday_cursor),
            position=pos
            ).values.subjectID = SubjectTable(new_subject)

    @classmethod
    def from_lesson_table_list(cls, lessons_list: list[LessonTable]):
        lessons_list.sort(key=lambda l: l.values.position)
        subjects = [Subject(lesson.values.subjectID.values.subjectname) for lesson in lessons_list]
        return cls(subjects)
    
    @classmethod
    def from_subject_table_list(cls, subject_table_list: list[SubjectTable]):
        subjects = [Subject(sj_table.values.subjectname) for sj_table in subject_table_list]
        return cls(subjects)

class TimetableBuilder:
    lessons: int
    weekdays: list[Weekday]
    weekday_cursor: Weekday
    _end_after_one_day = False
    def __init__(
        self, *, 
        pre_timetables: dict[Weekday: Timetable] | None=None, 
        starting_weekday: Weekday | None=None, 
        build_only_starting_weekday: bool | None=None
    ):
        self.__wd_cursor = 0
        self.subject_cursor = 0
        if not pre_timetables is None:
            self.lessons = max(map(len, list(pre_timetables.values())))
            self.weekdays = list(pre_timetables.keys())
            self.weekday_cursor = starting_weekday or self.weekdays[0]
            self.raw_timetables = pre_timetables
            self._end_after_one_day = True
        else:
            self.raw_timetables = {}

    def set_weekdays(self, weekdays: list[Weekday]):
        self.weekdays = weekdays
        self.weekday_cursor = weekdays[0]

    def set_lessons_amount(self, amount: int):
        self.lessons = amount
        self.raw_timetables = {wd: [EmptySubject() for _ in range(amount)] for wd in self.weekdays}

    def next_subject(self, subject: Subject) -> Literal[0, 1, 2]:
        """Returns 0 if its just next subject, 1 if its next day, 2 if its end"""
        self.raw_timetables[self.weekday_cursor][self.subject_cursor] = subject
        self.subject_cursor += 1
        if self.subject_cursor == self.lessons:
            self.subject_cursor = 0
            if self._next_weekday():
                return 2
            return 1
        return 0

    def _next_weekday(self):
        if self._end_after_one_day:
            return True
        self.__wd_cursor += 1
        flag = False
        if self.__wd_cursor == len(self.weekdays):
            self.__wd_cursor = 0
            flag = True
        self.weekday_cursor = self.weekdays[self.__wd_cursor]
        return flag
    
    def to_dict(self):
        return {wd: Timetable(sj_list) for wd, sj_list in self.raw_timetables.items()}

    def __getitem__(self, wd: Weekday):
        return self.raw_timetables[wd]
    
    def __delitem__(self, wd: Weekday):
        self.raw_timetables[wd] = [EmptySubject() for _ in range(self.lessons)]
        

