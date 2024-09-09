
from typing import Literal
from . import Weekday

def slot_to_string(
        slot: tuple[Weekday, int, bool], *, 
        case: Literal['nominative', 'genetive', 'accusative', 'dativ', 'instrumental', 'prepositional']='nominative',
        title: bool=True):
    weekday, position, is_for_next_week = slot
    weekday_word = getattr(weekday, case)
    weekday_word = weekday_word.title() if title else weekday_word
    return weekday_word + (" следующей недели" if is_for_next_week else "") + f", {position} урок"

def slot_to_callback(slot: tuple[Weekday, int, bool], callback_prefix: str='choosedslot'):
    return f'{callback_prefix}_{int(slot[0])}_{slot[1]}_{int(slot[2])}'

def callback_to_slot(callback_data: str) -> tuple[Weekday, int, bool]:
    _, weekday, pos, is_next_week = callback_data.split('_')
    return Weekday(int(weekday)), int(pos), bool(int(is_next_week))

def sort_slots(slots: list[tuple[Weekday, int, bool]]):
    slots.sort(key=lambda t: int(t[0])*10+t[1] + t[2]*100)