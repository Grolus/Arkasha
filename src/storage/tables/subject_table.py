
from .base import BaseTable
from ..connection import DBConection

db = DBConection()

class SubjectTable(BaseTable):
    _table_name = 'subject'
    