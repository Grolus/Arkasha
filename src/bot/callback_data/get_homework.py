from aiogram.filters.callback_data import CallbackData

from config.constants import DEFAULT_CALLBACK_DATA_SEPARATOR

class CancelCallback(CallbackData, prefix='homeworkgetcancel', sep=DEFAULT_CALLBACK_DATA_SEPARATOR):
    ...
    
class ShowLastHomeworkCallback(CallbackData, prefix='getlasthomework', sep=DEFAULT_CALLBACK_DATA_SEPARATOR):
    show: bool