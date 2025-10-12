from pydantic import BaseModel, NonNegativeInt, Field, PositiveInt
from typing_extensions import Self, Literal
from exceptions import ParsingError
import datetime

WEEKDAY_TO_NAME_ENG = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
WEEKDAY_TO_NAME_RU = ('понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресение')
WEEKDAY_TO_NOMINATIVE = WEEKDAY_TO_NAME_RU
WEEKDAY_TO_GENETIVE = ('понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресение')
WEEKDAY_TO_ACCUSATIVE = WEEKDAY_TO_GENETIVE
WEEKDAY_TO_DATIV = ('понедельнику', 'вторнику', 'среде', 'четвергу', 'пятнице', 'субботе', 'воскресению')
WEEKDAY_TO_INSTRUMENTAL = ('понедельником', 'вторником', 'средой', 'четвергом', 'пятницей', 'субботой', 'воскресением')
WEEKDAY_TO_PREPOSITIONAL = ('понедельнике', 'вторнике', 'среде', 'четверге', 'пятнице', 'субботе', 'воскресении')
WEEKDAY_TO_SHORT = ('пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс')

class Weekday(BaseModel):
    weekday_number: NonNegativeInt = Field(..., ge=0, le=6)
    
    def __init__(self, weekday_number: int):
        super().__init__(weekday_number=weekday_number)

    def _all_variants(self) -> list[str]:
        return [
            self.short,
            self.genetive,
            self.nominative,
            self.accusative,
            self.instrumental,
            self.prepositional,
            self.eng
            ]

    @property
    def short(self):
        return WEEKDAY_TO_SHORT[self.weekday_number]
    @property
    def eng(self):
        return WEEKDAY_TO_NAME_ENG[self.weekday_number]
    @property
    def genetive(self):
        return WEEKDAY_TO_GENETIVE[self.weekday_number]
    @property
    def nominative(self):
        return WEEKDAY_TO_NOMINATIVE[self.weekday_number]
    name = name_ru = nominative
    @property
    def accusative(self):
        return WEEKDAY_TO_ACCUSATIVE[self.weekday_number]
    @property
    def instrumental(self):
        return WEEKDAY_TO_INSTRUMENTAL[self.weekday_number]
    @property
    def dativ(self):
        return WEEKDAY_TO_DATIV[self.weekday_number]
    @property
    def prepositional(self):
        return WEEKDAY_TO_PREPOSITIONAL[self.weekday_number]
    def to_case(self, case: Literal['nominative', 'genetive', 'accusative', 'dativ', 'instrumental', 'prepositional']) -> str:
        return getattr(self, case)
    def __repr__(self):
        return f'Weekday({WEEKDAY_TO_NAME_ENG[self.weekday_number]})'
    def __str__(self): 
        return WEEKDAY_TO_NAME_RU[self.weekday_number]
    def __add__(self, integer: int) -> Self:
        if not isinstance(integer, int):
            raise ValueError(f"Cant add {type(integer).__name__!r} to a \'Weekday\' (only 'Weekday' + 'int' allowed)")
        new_number = (self.weekday_number + integer) % 7
        return Weekday(new_number)
    def __sub__(self, integer: int) -> Self:
        if not isinstance(integer, int):
            raise ValueError(f"Cant subtract {type(integer).__name__!r} of a \'Weekday\' (only 'Weekday' - 'int' allowed)")
        new_number = (self.weekday_number - integer) % 7
        return Weekday(new_number)
    def __eq__(self, other: Self | int) -> bool:
        return (isinstance(other, Weekday) and self.weekday_number == other.weekday_number) \
             or (isinstance(other, int) and self.weekday_number == other)
    def __lt__(self, other: Self | int) -> bool:
        if isinstance(other, int):
            return self.weekday_number < other
        else:
            return self.weekday_number < other.weekday_number
    def __le__(self, other: Self | int) -> bool:
        if isinstance(other, int):
            return self.weekday_number <= other
        else:
            return self.weekday_number <= other.weekday_number
    def __gt__(self, other: Self | int) -> bool:
        if isinstance(other, int):
            return self.weekday_number > other
        else:
            return self.weekday_number > other.weekday_number
    def __ge__(self, other: Self | int) -> bool:
        if isinstance(other, int):
            return self.weekday_number >= other
        else:
            return self.weekday_number >= other.weekday_number
    def __int__(self):
        return self.weekday_number
    def __hash__(self) -> int:
        return self.weekday_number

class WWDate(BaseModel):
    weekday: Weekday
    week: PositiveInt
    year: PositiveInt

    @classmethod
    def from_date(cls, date: datetime.date) -> Self:
        
        year, week, weekday_number = date.isocalendar() 
        weekday = Weekday(weekday_number - 1)
        
        return WWDate(weekday=weekday, week=week, year=year)
        
        # week = (
        #     datetime.datetime(date.year, 1, 1).weekday() + 
        #     date.timetuple().tm_yday
        # ) // 7 - 1
        # if date.weekday() == 6:
        #     week -= 1
        # weekday = date.weekday()
        # year = date.year
        # return WWDate(
        #     weekday=Weekday(weekday_number=weekday),
        #     week=week,
        #     year=year
        # )
        
        
    def to_date(self) -> datetime.date:
        return datetime.date.fromisocalendar(self.year, self.week, int(self.weekday)+1)
    
    def __add__(self, other: 'WWDateDelta'):
        new_date_ordinal = self.to_date().toordinal() + other.to_days_amount()
        return WWDate.from_date(datetime.date.fromordinal(new_date_ordinal))
    
    def add_days(self, days_amount: int):
        new_date_ordinal = self.to_date().toordinal() + days_amount
        return WWDate.from_date(datetime.date.fromordinal(new_date_ordinal))
    
    def __hash__(self) -> int:
        return self.year * 365 + self.week * 7 + int(self.weekday)
        
class WWDateDelta(WWDate):
    def __init__(self, weekday: Weekday, week: int, year: int):
        self.weekday = weekday
        self.week = week
        self.year = year
    def _to_days_amount(self):
        return self.to_date().toordinal()
    def __add__(self, other: 'WWDateDelta'):
        new_date_ordinal = self.to_date().toordinal() + other.to_days_amount()
        return WWDate.from_date(datetime.date.fromordinal(new_date_ordinal))
    
    
class Slot(BaseModel):
    wwdate: WWDate
    position: int

    @classmethod
    def new(cls, year, week, weekday_number, position) -> Self:
        return Slot(
            wwdate=WWDate(
                week=week,
                year=year,
                weekday=Weekday(weekday_number=weekday_number)
            ),
            position=position
        )
        
    def __hash__(self) -> int:
        return hash(self.wwdate) * self.position