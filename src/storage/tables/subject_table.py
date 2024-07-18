
from .base import BaseTable
from ..connection import DBConection

db = DBConection()

class SubjectTable(BaseTable):
    _table_name = 'subject'
    @staticmethod
    def get_creator_by_name(name: str) -> str | None:
        from . import AdministratorTable
        result = db.query(f"SELECT creatorID FROM {SubjectTable._table_name} WHERE subjectname='{name}'")
        if result:
            return AdministratorTable(result[0][0])