from enum import Enum

class GroupNumberEnum(str, Enum):
    FIRST = 'first'
    SECOND = 'second'
    NOT_GROUPED = 'not_grouped'