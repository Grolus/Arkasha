from pydantic import BaseModel

from .class_ import Class
from .weekday import Weekday

class Subject(BaseModel):
    name: str

class Lesson(BaseModel):
    subjects: list[Subject]

class Timetable(BaseModel):
    class_: Class
    days: dict[Weekday: dict[int: Lesson]]