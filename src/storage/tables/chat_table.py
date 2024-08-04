
from MySQLdb._exceptions import IntegrityError
from typing_extensions import override

from .base import BaseTable
from typing_extensions import override

class ChatTable(BaseTable):
    _table_name = 'chat'
    unique_column_name = 'telegramid'

    @override
    def insert(self):
        try:
            super().insert()
        except IntegrityError:
            instance = self.get_by_unique_column(self.values.telegramid)
            instance.values.classID = self.values.classID
            instance.values.adderID = self.values.adderID


