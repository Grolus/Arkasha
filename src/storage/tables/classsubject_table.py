
from .base import BaseTable
from ..connection import DBConection
from exceptions import ValueNotFoundError

db = DBConection()

class ClassSubjectTable(BaseTable):
    _table_name = 'classsubject'
    def insert_if_nessesary(self, new_subject_name, groups):
        from . import SubjectTable
        try:
            self.values.subjectID = SubjectTable.get_by_unique_column(new_subject_name)
        except ValueNotFoundError:
            new_subject = SubjectTable(subjectname=new_subject_name)
            new_subject.insert()
            self.values.subjectID = new_subject
        self.values.groups = groups