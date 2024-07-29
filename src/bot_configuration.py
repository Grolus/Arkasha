
from typing_extensions import Self
from entities import Subject, Timetable, DEFAULT_SUBJECTS, Class
from exceptions import SubjectListChangingError, ConfigureError
from utils.weekday import Weekday




class Bot_configuration():
    _username: str
    _classname: str
    _subjects_list: list[Subject]
    _is_5_days_studytype: bool
    _last_lerning_weekday: int
    _lessons_in_day: int
    _weekday_cursor: Weekday
    _all_timetable: list[Timetable]
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
        instance._weekday_cursor = Weekday(0)
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
    
    def weekday_cursor(self) -> Weekday:
        return self._weekday_cursor

    def tt_next_weekday(self) -> int:
        weekday = self._weekday_cursor    
        self._weekday_cursor = self._weekday_cursor + 1
        return weekday

    def tt_prev_weekday(self):
        self._weekday_cursor = self._weekday_cursor - 1
        return self._weekday_cursor

    def tt_next_subject(self, subject: None | Subject) -> bool:
        """Returns `True` if day ended and cursor got value `_lessons_in_day - 1`"""
        self._all_timetable[int(self._weekday_cursor)][self._subject_cursor] = subject
        self._subject_cursor += 1
        if self._subject_cursor == self._lessons_in_day:
            self._subject_cursor = 0
            return True
        return False

    def clear_tt(self, weekday: int):
        self._all_timetable[int(weekday)] = [None for _ in range(self._lessons_in_day)]

    def timetable(self, weekday: Weekday):
        return self._all_timetable[int(weekday)]
    
    def timetable_all(self) -> dict[Weekday: Timetable]:
        return self._all_timetable.copy()
    
    def set_lessons_count(self, count: int):
        self._lessons_in_day = count
        self._all_timetable = [[None for _ in range(self._lessons_in_day)] 
                           for _ in range(5 if self._is_5_days_studytype else 6)]

    @classmethod
    def from_entity(class_: Class) -> Self:
        Bot_configurator(class_.creator, class_.name)
        cfg = Bot_configurator.get(class_.creator)
        cfg._all_timetable = sorted([v for v in class_.timetables.values()])
        cfg._subjects_list = class_.subjects
        cfg._lessons_in_day = max(map(len, class_.timetables.values()))
        cfg.set_is_5_days_studytype(len(class_.timetables) == 5)
        

class Bot_configurator():
    """Defines class to be configured by a user"""
    __cursors: dict[str: Bot_configuration] = {}
    def __init__(self, username: str, classname: str):
        self.username = username
        self.configuration = Bot_configuration(username, classname)
        Bot_configurator.__cursors[username] = self.configuration

    @staticmethod
    def get(username: str) -> Bot_configuration:
        return Bot_configurator.__cursors[username]

    

