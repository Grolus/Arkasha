import logging
from logers import arkasha, handle

class BaseArkashaException(BaseException):
    loger: logging.Logger = arkasha
    def __init__(self, message: str):
        """Message to be shown in logs"""
        self.loger.error(message)


class ConfigureError(BaseArkashaException):
    loger = handle

class SubjectListChangingError(ConfigureError):
    ...

class SubjectError(BaseArkashaException):
    ...

class DecodingSubjectError(SubjectError):
    ...
