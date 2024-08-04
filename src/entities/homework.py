
import datetime

from . import Subject, Class
from utils import Weekday


class Homework:

    def __init__(self, subject: Subject, class_: Class, text: str, weekday: Weekday, week: int, position: int, year: int=datetime.date.today().year):
        self.subject = subject
        self.class_ = class_
        self.text = text
        self.weekday = weekday
        self.week = week
        self.position = position
        self.year = year
