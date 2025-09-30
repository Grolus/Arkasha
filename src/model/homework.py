from pydantic import BaseModel
from . import Subject, Class, Slot
from enums import GroupNumberEnum

class Homework(BaseModel):
    subject: Subject
    text: str
    class_: Class
    slot: Slot
    attachment_url: str | None
    group: GroupNumberEnum
