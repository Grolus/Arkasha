import logging
from logers import arkasha, handle, database, entity

class BaseArkashaException(BaseException):
    loger: logging.Logger = arkasha
    def __init__(self, message: str):
        """Message to be shown in logs"""
        self.loger.error(f'{self.__class__.__name__}: {message}')


class BaseEntityException(BaseArkashaException):
    loger = entity

class ConfigureError(BaseArkashaException):
    loger = handle

class SubjectListChangingError(ConfigureError):
    ...

class SubjectError(BaseEntityException):
    ...

class DecodingSubjectError(SubjectError):
    ...

class ClassError(BaseEntityException):
    ...

class AdministratorsListChangingError(ClassError):
    ...

class TimetableUpdatingError(ClassError):
    ...

class BaseDatabaseException(BaseArkashaException):
    loger = database

class ColumnError(BaseDatabaseException):
    ...

class WrongColumnError(ColumnError):
    ...

class WrongDatatypeError(ColumnError):
    ...

class ColumnNotFoundError(ColumnError):
    ...

class ConnectionError(BaseDatabaseException):
    ...
