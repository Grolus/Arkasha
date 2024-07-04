
from .base import BaseTable
from ..connection import DBConection

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
        result = DBConection().query(f"SELECT classname FROM {cls._table_name}")
        return result[0]

    @staticmethod
    def save_new_configuration(configuration):
        from . import (
            ClassSubjectTable, 
            LessonTable, 
            ClassAdministratorTable
        )
        class_ = ClassTable(
            classname=configuration._classname,
            username=configuration._username,
            lessons=configuration._lessons_in_day,
            lastlearningweekday=configuration._last_lerning_weekday
            )
        class_.insert()
        for weekday, timetable in enumerate(configuration.timetable_all()):
            for position, subject in enumerate(timetable):
                ClassSubjectTable(
                    **class_.as_kwargs(),
                    subjectname=str(subject)
                    ).insert()
                LessonTable(
                    **class_.as_kwargs(),
                    subjectname=str(subject),
                    weekday=weekday,
                    position=position
                ).insert()
        ClassAdministratorTable(
            **class_.as_kwargs()
            ).insert()

    def get_administrators(self) -> list:
        from . import AdministratorTable
        admin_ids = [i[0] for i in db.query(f"SELECT administratorID FROM classadministrator WHERE classID={self.id_}")]
        return [AdministratorTable.get_by_id(id_) for id_ in admin_ids]
    
    def get_subjects(self):
        from . import SubjectTable
        subject_ids = [i[0] for i in db.query(f"SELECT subjectID FROM classsubject WHERE classID={self.id_}")]
        return [SubjectTable.get_by_id(id_) for id_ in subject_ids]
    
    def get_all_timetables(self):
        from . import LessonTable, SubjectTable
        lessons = [
            [LessonTable.from_selected_row(row) 
             for row in db.query(f"SELECT * FROM lesson WHERE ClassID={self.id_} AND weekday={weekday} ORDER BY position")]
             for weekday in range(self._v_lastlearningweekday + 1)
             ]
        subjects = [
            [SubjectTable.get_by_id(l._v_subjectID.id_) 
             for l in lessons_row]
            for lessons_row in lessons
            ]
        return subjects
    
