
from .base import BaseTable
from ..connection import DBConection

db = DBConection()

class ClassSubjectTable(BaseTable):
    _table_name = 'classsubject'