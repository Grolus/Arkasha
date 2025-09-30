from typing_extensions import Self

from pydantic import BaseModel, Field

from config.constants import MIN_SUBJECT_NAME_LENGTH, MAX_SUBJECT_NAME_LENGTH

ALL_SUBJECT_DICT = {}

class Subject(BaseModel):
    name: str = Field(..., pattern=r'\w{' + str(MIN_SUBJECT_NAME_LENGTH) + ',' + str(MAX_SUBJECT_NAME_LENGTH) + '}')
    
    def __init__(self, name: str):
        super().__init__(name=name)
        ALL_SUBJECT_DICT[name] = self
    def __eq__(self, other: Self) -> bool:
        if not isinstance(other, self.__class__):
            raise TypeError('Can compare only Subject and Subject')
        return self.name == other.name
    def __hash__(self):
        return hash(self.name+'_subject_object')