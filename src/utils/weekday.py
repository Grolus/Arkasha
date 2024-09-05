

from typing import Literal
from typing_extensions import Self

class Weekday:
    
    __NAMES_ENG = ('monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
    __NAMES_RU = ('понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресение')
    __NOMINATIVE = __NAMES_RU
    __GENETIVE = ('понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресение')
    __ACCUSATIVE = __GENETIVE
    __DATIV = ('понедельнику', 'вторнику', 'среде', 'четвергу', 'пятнице', 'субботе', 'воскресению')
    __INSTRUMENTAL = ('понедельником', 'вторником', 'средой', 'четвергом', 'пятницей', 'субботой', 'воскресением')
    __PREPOSITIONAL = ('понедельнике', 'вторнике', 'среде', 'четверге', 'пятнице', 'субботе', 'воскресении')
    __SHORT = ('пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс')

    __instances = [None] * 7
    def __new__(cls, weekday_number: Literal[0, 1, 2, 3, 4, 5, 6]):
        if not isinstance(weekday_number, int) or 0 > weekday_number > 6:
            raise ValueError(f'Weekday number must be integer in range 0-6 (not {weekday_number})')
        if instance := cls.__instances[weekday_number]:
            return instance
        instance = super(cls).__new__()
        cls.__instances[weekday_number] = instance
        instance.__number = weekday_number
        return instance

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
        return Weekday.__SHORT[self.__number]
    @property
    def eng(self):
        return Weekday.__NAMES_ENG[self.__number]
    @property
    def genetive(self):
        return Weekday.__GENETIVE[self.__number]
    @property
    def nominative(self):
        return Weekday.__NOMINATIVE[self.__number]
    name = name_ru = nominative
    @property
    def accusative(self):
        return Weekday.__ACCUSATIVE[self.__number]
    @property
    def instrumental(self):
        return Weekday.__INSTRUMENTAL[self.__number]
    @property
    def dativ(self):
        return Weekday.__DATIV[self.__number]
    @property
    def prepositional(self):
        return Weekday.__PREPOSITIONAL[self.__number]
    def __repr__(self):
        return f'<{Weekday.__NAMES_ENG[self.__number]}>'
    def __str__(self): 
        return Weekday.__NAMES_RU[self.__number]
    def __add__(self, integer: int) -> Self:
        if not isinstance(integer, int):
            raise ValueError(f"Cant add {type(integer).__name__!r} to a \'Weekday\' (only 'Weekday' + 'int' allowed)")
        new_number = (self.__number + integer) % 7
        return Weekday(new_number)
    def __sub__(self, integer: int) -> Self:
        if not isinstance(integer, int):
            raise ValueError(f"Cant subtract {type(integer).__name__!r} of a \'Weekday\' (only 'Weekday' - 'int' allowed)")
        new_number = (self.__number - integer) % 7
        return Weekday(new_number)
    def __eq__(self, other: Self | int) -> bool:
        return (isinstance(other, Weekday) and self.__number == other.__number) \
             or (isinstance(other, int) and self.__number == other)
    def __int__(self):
        return self.__number
    def __hash__(self) -> int:
        return self.__number
    