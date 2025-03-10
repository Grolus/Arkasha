
from pydantic import BaseModel, Field

from config.constants import MIN_SUBJECT_NAME_LENGTH, MAX_SUBJECT_NAME_LENGTH

class Subject(BaseModel):
    name: str = Field(..., pattern=r'\w{' + str(MIN_SUBJECT_NAME_LENGTH) + ',' + str(MAX_SUBJECT_NAME_LENGTH) + '}')
    def __init__(self, name: str):
        super().__init__(name=name)