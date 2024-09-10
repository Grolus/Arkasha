

from .base import BaseTable
from ..connection import DBConection

from utils.weekday import Weekday
from logers import database as loger

db = DBConection()

class ClassTable(BaseTable):
    _table_name = 'class'
    unique_column_name = 'classname'
    def __new__(cls, *, _classname: str=None, _class_id: int=None, **kwargs):
        if _classname is None and _class_id is None:
            instance = super().__new__(cls)
            return instance
        instance = cls.get(_classname, _class_id)
        return instance
    def __init__(self, _classname: str=None, _class_id: int=None, **kwargs):
        if _classname is None and _class_id is None:
            super().__init__(**kwargs)
            
    @classmethod
    def get_all_names(cls) -> tuple[str]:
        loger.warn(f'{cls.get_all_names.__name__!r} deprecated. Use {cls.validate_name.__name__!r}')
        result = DBConection().query(f"SELECT classname FROM {cls._table_name}")
        return result[0]

    @classmethod
    def is_valid_name(cls, classname: str):
        "Validates name `classname` for table `class`. Returns `True`, if name not exists in table"
        result = DBConection().query(f"SELECT * FROM {cls._table_name} WHERE classname='{classname}'")
        return not result

    @staticmethod
    def save_new_configuration(classname: str, creator_username: str, subject_list: list, timetables: dict):
        from . import (
            ClassSubjectTable, 
            LessonTable, 
            ClassAdministratorTable,
            ClassWeekdayTable
        )
        lessons = len(list(timetables.values())[0])
        class_ = ClassTable(
            classname=classname,
            username=creator_username,
            lessons=lessons
        )
        class_.insert()
        class_weekday_tables = [
            ClassWeekdayTable(
                **class_.as_kwargs(),
                weekday = int(weekday)
            ) for weekday in timetables.keys()
        ]
        ClassWeekdayTable.insert_many(class_weekday_tables)
        subject_tables = [
            ClassSubjectTable(
                **class_.as_kwargs(),
                subjectname=str(subject)
            )
            for subject in subject_list
        ]
        ClassSubjectTable.insert_many(subject_tables)
        lesson_tables = []
        for weekday, timetable in timetables.items():
            for position, subject in enumerate(timetable):
                lesson_tables.append(LessonTable(
                    **class_.as_kwargs(),
                    subjectname=str(subject),
                    weekday=int(weekday),
                    position=position
                ))
        LessonTable.insert_many(lesson_tables)
        ClassAdministratorTable(
            **class_.as_kwargs()
            ).insert()

    def get_administrators(self) -> list['AdministratorTable']: # type: ignore
        from . import AdministratorTable
        admin_ids = [i[0] for i in db.query(f"SELECT administratorID FROM classadministrator WHERE classID={self.id_}")]
        return [AdministratorTable.get_by_id(id_) for id_ in admin_ids]
    
    def get_subjects(self) -> list['SubjectTable']: # type: ignore
        from . import SubjectTable
        subject_ids = [i[0] for i in db.query(f"SELECT subjectID FROM classsubject WHERE classID={self.id_}")]
        return [SubjectTable.get_by_id(id_) for id_ in subject_ids]
    
    def get_weekdays(self) -> list[Weekday]:
        from . import ClassWeekdayTable
        weekdays = [
            Weekday(i[0]) 
            for i in db.query(f"SELECT weekday FROM {ClassWeekdayTable._table_name} WHERE classID={self.id_} ORDER BY weekday")
        ]
        return weekdays

    def get_subject_groups(self, table_subject: 'SubjectTable') -> int: # type: ignore
        from . import ClassSubjectTable
        result = db.query(
            f"SELECT `groups` FROM {ClassSubjectTable._table_name} WHERE classID={self.id_} AND subjectID={table_subject.id_}"
        )
        groups = result[0][0]
        return groups

    def get_all_timetables(self) -> dict[Weekday: list['SubjectTable']]: # type: ignore
        timetables = {
            weekday: self.get_timetable(weekday)
            for weekday in self.get_weekdays()
        }
        return timetables
    
    def get_timetable(self, weekday: Weekday) -> list['SubjectTable']: # type: ignore
        from . import SubjectTable, LessonTable
        result = db.query(f"SELECT subjectID FROM {LessonTable._table_name} WHERE classID={self.id_} AND weekday={int(weekday)} ORDER BY position")
        return [SubjectTable.get_by_id(i[0]) for i in result]

    def add_subject(self, subject_name: str):
        from . import SubjectTable, ClassSubjectTable
        ClassSubjectTable(
            **self.as_kwargs(),
            **SubjectTable(subjectname=subject_name).as_kwargs()
        ).insert()

    def update_timetables(self, new_timetables: dict[Weekday: list['SubjectTable']]): # type: ignore
        for k, v in new_timetables.items():
            self.update_timetable(k, v)

    def update_timetable(self, weekday: int, new_timetable: list['SubjectTable']): # type: ignore
        for i, sj in enumerate(new_timetable):
            self.update_lesson(weekday, i, sj)

    def update_lesson(self, weekday: int, position: int, new_subject: 'SubjectTable'): # type: ignore
        from . import SubjectTable, LessonTable
        db.query(
            f"UPDATE {LessonTable._table_name} " 
            f"SET subjectID={new_subject.id_} "
            f"WHERE weekday={weekday} AND position={position} AND classID={self.id_}"
        )

    def add_administrator(self, administrator_username: str):
        from . import AdministratorTable, ClassAdministratorTable
        ClassAdministratorTable(self.id_, AdministratorTable(administrator_username).id_).insert()

    def remove_administrator(self, removed_admin_username: str):
        from . import ClassAdministratorTable, AdministratorTable
        db.query(f"DELETE FROM {ClassAdministratorTable._table_name} WHERE classID={self.id_} AND administratorID={AdministratorTable(removed_admin_username).id_}")

    def set_subject_groups(self, table_subject, groups: int):
        db.query(f"UPDATE classsubject SET `groups`={groups} WHERE classID={self.id_} AND subjectID={table_subject.id_}")

