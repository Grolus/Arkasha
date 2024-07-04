
from typing_extensions import Self

from .subject import Subject
from .timetable import Timetable
from utils import Weekday
from storage.tables import ClassTable, AdministratorTable


class Class():
    connected_table_value: ClassTable
    def __init__(
            self, 
            name: str, 
            creator_username: str, 
            administrators: list[str], 
            subjects: list[Subject], 
            timetables: dict[int: Timetable],
            connected_table_value: ClassTable=None
            ):
        self.name = name
        self.creator = creator_username
        self.administrators = administrators
        self.subjects = subjects
        self.timetables = timetables
        if not connected_table_value:
            connected_table_value = ClassTable(
                classname=self.name,
                username=self.creator,
                lessons=max(map(len, self.timetables.values())),
                lastlearningweekday=len(self.timetables)-1
                )
        self.connected_table_value = connected_table_value
        

    def get_information_string(self):
        enter = '\n'
        subjects_enumerating = enter.join(
            [f'<i>{subject.name}</i>' 
             for subject in (self.subjects[:3] if len(self.subjects) > 5 else self.subjects)]
             ) + ((enter + f'<i>Ещё {len(self.subjects)-3} предметов</i>') if len(self.subjects) > 5 else '')
        return f"Класс <u><b>{self.name}</b></u>:{enter*2}{subjects_enumerating}{enter*2}Создатель: @{self.creator}{enter}"

    @classmethod
    def from_table_value(cls, tableclass: ClassTable) -> Self:
        connected_table_value = tableclass
        classname = tableclass._v_classname
        creator = AdministratorTable.get_by_id(tableclass._v_creatorID.id_)._v_username
        administrators = tableclass.get_administrators()
        subjects = [Subject.from_table_value(s) for s in tableclass.get_subjects()]
        timetables = {
            wd: Timetable(
                [Subject.from_table_value(subject) 
                 for subject in subjects_list]
                 ) 
            for wd, subjects_list in enumerate(tableclass.get_all_timetables())
            }
        return cls(classname, creator, administrators, subjects, timetables, connected_table_value)
    