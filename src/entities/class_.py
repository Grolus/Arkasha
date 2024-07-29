
from typing_extensions import Self

from .subject import Subject
from .timetable import Timetable, TimetableBuilder
from utils import Weekday
from storage.tables import ClassTable, AdministratorTable, SubjectTable
from exceptions import AdministratorsListChangingError, TimetableUpdatingError

class Class():
    connected_table_value: ClassTable
    def __init__(
            self, 
            name: str, 
            creator_username: str, 
            administrators: list[str], 
            subjects: list[Subject], 
            timetables: dict[Weekday: Timetable],
            connected_table_value: ClassTable=None
            ):
        self.name = name
        self.creator = creator_username
        self.administrators = administrators
        self.subjects = subjects
        self.timetables = timetables
        self.weekdays = list(timetables.keys())
        self.editor = self.creator
        self.__is_updating_timetable = False
        if connected_table_value is None:
            connected_table_value = ClassTable(
                classname=self.name,
                username=self.creator,
                lessons=max(map(len, self.timetables.values()))
                )
        self.connected_table_value = connected_table_value

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__!r} object ({self.name!r}, {self.creator!r})>'
    
    def update_name(self, new_name: str):
        self.connected_table_value.values.classname = new_name
        self.name = new_name

    def add_administrator(self, new_administrator: str):
        self.connected_table_value.add_administrator(new_administrator)
        self.administrators.append(new_administrator)

    def remove_administrator(self, removed_administrator: str):
        if removed_administrator in self.administrators:
            self.connected_table_value.remove_administrator(removed_administrator)
            self.administrators.remove(removed_administrator)
        else: 
            raise AdministratorsListChangingError(f'user {removed_administrator} not a {self!r} administrator')

    def add_subject(self, subject: Subject):
        self.subjects.append(subject)
        self.connected_table_value.add_subject(subject.name)

    def start_timetable_updating(self, weekday: Weekday):
        self._tt_updating_builder = TimetableBuilder(
            pre_timetables=self.timetables, 
            starting_weekday=weekday, 
            build_only_starting_weekday=True
        )
        self.__is_updating_timetable = True


    def update_timetable(self, subject: Subject):
        if not self.__is_updating_timetable:
            raise TimetableUpdatingError(f'Updating timetable not started for class {self!r}')
        updating_result = self._tt_updating_builder.next_subject(subject)
        return updating_result
    
    def end_timetable_updating(self):
        timetables = self._tt_updating_builder.to_dict()
        del self._tt_updating_builder
        self._update_timetables(timetables)
        self.__is_updating_timetable = False

    def _update_timetables(self, new_timetables):
        self.connected_table_value.update_timetables(new_timetables)

    def get_information_string(self):
        enter = '\n'
        subjects_enumerating = enter.join(
            [f'<i>{subject.name}</i>' 
             for subject in (self.subjects[:3] if len(self.subjects) > 5 else self.subjects)]
             ) + ((enter + f"<i><b>ещё {len(self.subjects)-3} предмет{'' if len(self.subjects)-3 == 1 else 'а' if str(len(self.subjects))[-1] in (2, 3, 4) else 'ов'}</b></i>") if len(self.subjects) > 5 else '')
        return f"Класс <u><b>{self.name}</b></u>:{enter*2}{subjects_enumerating}{enter*2}Создатель: @{self.creator}{enter}"

    @classmethod
    def from_table_value(cls, tableclass: ClassTable) -> Self:
        connected_table_value = tableclass
        classname = tableclass.values.classname
        creator = AdministratorTable.get_by_id(tableclass.values.creatorID.id_).values.username
        administrators = [admin.values.username for admin in tableclass.get_administrators()]
        subjects = [Subject.from_table_value(s) for s in tableclass.get_subjects()]
        timetables = {
            wd: Timetable(
                [Subject.from_table_value(subject)
                 for subject in subjects_list]
                 ) 
            for wd, subjects_list in tableclass.get_all_timetables().items()
            }
        return cls(classname, creator, administrators, subjects, timetables, connected_table_value)
    
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__!r} object ({self.name!r})>'
    
