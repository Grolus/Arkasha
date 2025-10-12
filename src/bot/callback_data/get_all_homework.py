from aiogram.filters.callback_data import CallbackData

from model import Weekday
from config.constants import DEFAULT_CALLBACK_DATA_SEPARATOR

class WeekdayCallback(CallbackData, prefix='choosedweekdaygelallhomework', sep=DEFAULT_CALLBACK_DATA_SEPARATOR):
    weekday_number: int
    
        
        
        