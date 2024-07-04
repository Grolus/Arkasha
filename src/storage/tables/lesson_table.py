from .base import BaseTable
from ..connection import DBConection

db = DBConection()

class LessonTable(BaseTable):
    _table_name = 'lesson'