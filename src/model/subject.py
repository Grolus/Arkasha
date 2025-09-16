from typing_extensions import Self

from pydantic import BaseModel, Field

from config.constants import MIN_SUBJECT_NAME_LENGTH, MAX_SUBJECT_NAME_LENGTH

class Subject(BaseModel):
    name: str = Field(..., pattern=r'\w{' + str(MIN_SUBJECT_NAME_LENGTH) + ',' + str(MAX_SUBJECT_NAME_LENGTH) + '}')
    
    __ALL_SUBJECT_DICT = {}
    
    def __init__(self, name: str):
        super().__init__(name=name)
        self.__class__.__ALL_SUBJECT_DICT[name] = self
    def __eq__(self, other: Self) -> bool:
        if not isinstance(other, Self):
            raise TypeError('Can compare only Subject and Subject')
        return self.name == other.name
    def __hash__(self):
        return hash(self.name+'_subject_object')