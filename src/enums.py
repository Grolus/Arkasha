from enum import Enum

class GroupNumberEnum(str, Enum):
    FIRST = 'first'
    SECOND = 'second'
    NOT_GROUPED = 'not_grouped'
    
    
    def as_number(self):
        match self:
            case GroupNumberEnum.FIRST:
                return 1
            case GroupNumberEnum.SECOND:
                return 2
            case GroupNumberEnum.NOT_GROUPED:
                return 0