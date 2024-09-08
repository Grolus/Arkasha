
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
    def __contains__(self, sj):
        return sj in self.lessons
    
    def position(self, subject: Subject):
        return self.lessons.index(subject) + 1

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
    lessons_amount: int
    weekdays: list[Weekday]
    weekday_cursor: Weekday
    _end_after_one_day = False
    def __init__(
        self, 
        lessons_amount: int,
        weekdays: list[Weekday]
    ):
        self.lessons_amount = lessons_amount
        self.weekdays = weekdays
        self.__wd_cursor = 0
        self.subject_cursor = 0
        self.group_cursor = 0
        self.raw_timetables = {wd: [EmptySubject() for _ in range(self.lessons_amount)] for wd in self.weekdays}

    @classmethod
    def from_existing_timetable(
        cls, 
        pre_timetables: 
        dict[Weekday: Timetable], starting_weekday: Weekday | None=None
    ):
        self = cls.__new__(cls)
        self.lessons_amount = max(map(len, list(pre_timetables.values())))
        self.weekdays = list(pre_timetables.keys())
        self.weekday_cursor = starting_weekday or self.weekdays[0]
        self.subject_cursor = 0
        self.group_cursor = 0
        self.raw_timetables = pre_timetables
        self._end_after_one_day = True
        return self

    @property
    def weekday_cursor(self):
        return self.weekdays[self.__wd_cursor]

    def next_subject(self, subject: Subject, subject_groups: int=1):
        is_subject_grouped = subject_groups > 1
        # cursors: subject, group, weekday
        if not is_subject_grouped:
            if self.group_cursor != 0:
                raise ValueError(f'Expexted grouped subject, got {subject} ({subject_groups})')
            else:
                self.current_timetable[self.subject_cursor] = subject
                return self.up_subject_cursor()
        else:
            if self.group_cursor == 0:
                self.current_timetable[self.subject_cursor] = [subject]
                self.group_cursor += 1
                return -1
            else:
                self.current_timetable[self.subject_cursor].append(subject)
                self.group_cursor += 1
                if self.group_cursor >= subject_groups: # is end of grouped lesson building
                    self.group_cursor = 0
                    return self.up_subject_cursor()
                
    def up_subject_cursor(self):
        self.subject_cursor += 1
        if self.subject_cursor >= self.lessons_amount:
            self.subject_cursor = 0
            return self._next_weekday() + 1
        return 0
        
    def _next_weekday(self):
        if self._end_after_one_day:
            return True
        self.__wd_cursor += 1
        flag = False
        if self.__wd_cursor == len(self.weekdays):
            self.__wd_cursor = 0
            flag = True
        return flag
    
    def get_next_weekday(self):
        if self.__wd_cursor < len(self.weekdays):
            return self.weekdays[self.__wd_cursor + 1]
        return None

    def weekday_again(self):
        self.__wd_cursor -= 1
        self.raw_timetables[self.weekday_cursor] = [EmptySubject() for _ in range(self.lessons_amount)]

    @property
    def current_timetable(self) -> list[Subject]:
        return self.raw_timetables[self.weekday_cursor]



    def to_dict(self):
        return {wd: Timetable(sj_list) for wd, sj_list in self.raw_timetables.items()}

    def __getitem__(self, wd: Weekday):
        return self.raw_timetables[wd]
    
    def __delitem__(self, wd: Weekday):
        self.raw_timetables[wd] = [EmptySubject() for _ in range(self.lessons_amount)]
        

