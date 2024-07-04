import logging
from logers import arkasha, handle, database

class BaseArkashaException(BaseException):
    loger: logging.Logger = arkasha
    def __init__(self, message: str):
        """Message to be shown in logs"""
        self.loger.error(f'{self.__class__.__name__}: {message}')


class ConfigureError(BaseArkashaException):
    loger = handle

class SubjectListChangingError(ConfigureError):
    ...

class SubjectError(BaseArkashaException):
    ...

class DecodingSubjectError(SubjectError):
    ...

class BaseDatabaseException(BaseArkashaException):
    loger = database

class ColumnError(BaseDatabaseException):
    ...

class WrongColumnError(ColumnError):
    ...

class WrongDatatypeError(ColumnError):
    ...

class ColumnNotFoundedError(ColumnError):
    ...

class ConnectionError(BaseDatabaseException):
    ...

