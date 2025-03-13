from pydantic import BaseModel
from .user import User
from .timetable import Timetable

class Class(BaseModel):
    name: str
    creator: User
    timetable: Timetable
    