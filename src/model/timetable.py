from pydantic import BaseModel

from .lesson import Lesson
from .weekday import Weekday

class Timetable(BaseModel):
    timetable_dict: dict[Weekday, list[Lesson | None]]
