
from typing_extensions import Self
from homework import Subject, DEFAULT_SUBJECTS
from exceptions import SubjectListChangingError, ConfigureError
from .weekday import weekday_up

class Bot_configuration():
    _username: str
    _classname: str
    _subjects_list: list[Subject]
    _is_5_days_studytype: bool
    _last_lerning_weekday: int
    _lessons_in_day: int
    _weekday_cursor: int
    _timetable: list[list[None | Subject]]
    _subject_cursor: int
    __instances: dict[tuple[str, str]: Self] = {}
 
    def __new__(cls, username: str, classname: str):
        if instance := cls.__instances.get((username, classname)):
            if isinstance(instance, cls):
                return instance
        instance = super().__new__(cls)
        cls.__instances[(username, classname)] = instance
        instance._classname = classname
        instance._username = username
        instance._subjects_list = DEFAULT_SUBJECTS.copy()
        instance._weekday_cursor = 0
        instance._subject_cursor = 0
        return instance

    def new_subject(self, subject: Subject):
        if subject in self._subjects_list:
            raise SubjectListChangingError(f'Subject "{subject}" already exists in Bot_configuration({self._username})._subjects_list')
        self._subjects_list.append(subject)
    
    def remove_subject(self, subject: Subject):
        if not subject in self._subjects_list:
            raise SubjectListChangingError(f'Bot_configuration.delete_subject(): subject "{subject}" not in subject list!')
        self._subjects_list.remove(subject)
    
    def subjects(self):
        return self._subjects_list.copy()

    def set_is_5_days_studytype(self, is_5_days: bool):
        """`True` if studytype - 5 days, else (6 days) - `False`"""
        self._is_5_days_studytype = is_5_days
        self._last_lerning_weekday = 4 if is_5_days else 5
    
    def weekday_cursor(self) -> int:
        return self._weekday_cursor

    def tt_next_weekday(self) -> int:
        weekday = self._weekday_cursor    
        self._weekday_cursor = weekday_up(self._weekday_cursor, 1)
        return weekday

    def tt_prev_weekday(self):
        self._weekday_cursor = weekday_up(self._weekday_cursor, -1)
        return self._weekday_cursor

    def tt_next_subject(self, subject: None | Subject) -> bool:
        """Returns `True` if day ended and cursor got value `_lessons_in_day - 1`"""
        self._timetable[self._weekday_cursor][self._subject_cursor] = subject
        self._subject_cursor += 1
        if self._subject_cursor == self._lessons_in_day:
            self._subject_cursor = 0
            return True
        return False

    def clear_tt(self, weekday: int):
        self._timetable[weekday] = [None for _ in range(self._lessons_in_day)]

    def timetable(self, weekday: int):
        return self._timetable[weekday]
    
    def timetable_all(self):
        return [tt.copy() for tt in self._timetable.copy()]
    
    def set_lessons_count(self, count: int):
        self._lessons_in_day = count
        self._timetable = [[None for _ in range(self._lessons_in_day)] 
                           for _ in range(5 if self._is_5_days_studytype else 6)]


class Bot_configurator():
    
    __cursors: dict[str: Bot_configuration] = {}
    def __init__(self, username: str, classname: str):
        self.username = username
        self.configuration = Bot_configuration(username, classname)
        Bot_configurator.__cursors[username] = self.configuration

    @staticmethod
    def get(username: str) -> Bot_configuration:
        return Bot_configurator.__cursors[username]

    

