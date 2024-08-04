
from typing import Any
from .base import BaseTable, Column
from ..connection import DBConection

from typing_extensions import override


db = DBConection()

class AdministratorTable(BaseTable):
    _table_name = 'administrator'
    unique_column_name = 'username'
    def __new__(cls, _username: str | None=None, _administrator_id: int | None=None, **kwargs):
        if _username is None and _administrator_id is None:
            instance = super().__new__(cls)
            return instance
        instance = cls.get(_username, _administrator_id)
        return instance
    def __init__(self, _username: str | None=None, _administrator_id: int | None=None, **kwargs):
        if _username is None and _administrator_id is None:
            super().__init__(**kwargs)
        
    def get_classes(self) -> list['ClassTable']: # type: ignore
        from . import ClassTable
        if result := db.query(f"SELECT idAdministrator FROM administrator WHERE username='{self.values.username}'"):
            admin_id = result[0][0]
            result = db.query(f"SELECT classID FROM classadministrator WHERE administratorID={admin_id}")
            classes = []
            for class_id, in result:
                result = db.query(f"SELECT * FROM class WHERE idClass={class_id}")
                classes.append(ClassTable.from_selected_row(result[0]))
            return classes
        else:
            return []

    @override
    @classmethod
    def get_by_unique_column(cls, unique_column_value: Any):
        try:
            instance = super().get_by_unique_column(unique_column_value)
        except ValueError:
            instance = AdministratorTable(username=unique_column_value)
        return instance