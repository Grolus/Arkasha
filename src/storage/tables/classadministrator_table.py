from .base import BaseTable
from ..connection import DBConection

db = DBConection()

class ClassAdministratorTable(BaseTable):
    _table_name = 'classadministrator'