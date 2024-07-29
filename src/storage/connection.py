
import MySQLdb as mysql
from MySQLdb.cursors import Cursor
from typing import Any
from logers import database as loger
from exceptions import ConnectionError

class DBConection():
    __instance = None
    _connection: mysql.Connection
    _cursor: Cursor
    _c: Cursor
    def __new__(cls, host: str=..., password: str=..., database: str=..., port: int=..., user: str=...):
        if not isinstance(cls.__instance, cls):
            if all([arg is ... for arg in [host, password, database, port, user]]):
                raise ConnectionError(f'{cls.__name__!r} not initiated!')
            instance = super().__new__(cls)
            instance._connection = mysql.Connection(host=host, password=password, port=port, database=database, user=user)
            instance._cursor = instance._connection.cursor()
            instance._c = instance._cursor
            cls.__instance = instance
        return cls.__instance

    def _execute(self, query: str) -> None:
        (loger.debug if query.strip().lower().startswith('select') else loger.info)(f'Executing query: {query}')
        self._c.execute(query)
        self._connection.commit()
    
    def query(self, query: str) -> tuple[None | tuple[Any]]:
        self._execute(query)
        result = self._c.fetchall()
        loger.debug(f'Return: {result}')
        return result
    
