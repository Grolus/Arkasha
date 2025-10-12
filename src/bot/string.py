from typing import Literal

from enums import GroupNumberEnum
from model import WWDate, Slot, Homework, Weekday
from config.constants import NO_HOMEWORK_MARKER, EXISTED_HOMEWORK_MARKER


def format_relative_slot_string(now_wwdate: WWDate, slot: Slot) -> str:
    """Преобразует `slot` к строке вида `'Понедельник ... недели [назад], 1 урок'`"""
    position_part = f"{slot.position + 1} урок"
    day_part = format_relative_wwdate_string(slot.wwdate, now_wwdate)
    result = f"{day_part.capitalize()}, {position_part}"
    return result

def format_relative_wwdate_string(target_wwdate: WWDate, now_wwdate: WWDate):
    """Возвращает строку вида `'понедельник'` ил `'вторнки следующей недели'`"""
    weekday_word = target_wwdate.weekday.name_ru

    # если неделя не меняется и день впереди - строка недели пуста
    # если неделя не меняется и день этот сзади - "этой недели"
    # если неделя впереди - "следующей недели", "через {2+} недель(и)"
    if now_wwdate.week == target_wwdate.week:
        if target_wwdate.weekday > now_wwdate.weekday:
            week_part = ""
        else:
            week_part = " этой недели"
    else:
        difference = abs(target_wwdate.week - now_wwdate.week)
        if difference % 100 >= 5 and difference % 100 <= 20:
            week_word = "недель"
        elif difference % 10 == 1:
            week_word = "неделю"
        elif difference % 10 >= 2 and difference % 10 <= 4:
            week_word = "недели"
        else:
            week_word = "недель"
        if target_wwdate.week > now_wwdate.week:
            if difference == 1:
                week_part = " следующей недели"
            else:
                week_part = f" через {difference} {week_word}"
        else:
            if difference == 1:
                week_part = " прошлой недели"
            else:
                week_part = f" {difference} {week_word} назад"
    
    result = f"{weekday_word}{week_part}"
    return result

def format_relative_weekday_string(
    target_weekday: Weekday, now_weekday: Weekday, 
    *, 
    case: Literal['nominative', 'genetive', 'accusative', 'dativ', 'instrumental', 'prepositional']='nominative') -> str:
    weekday_word = target_weekday.to_case(case)
    if int(target_weekday) > int(now_weekday):
        return weekday_word
    else:
        return f'{weekday_word} следующей недели'

def format_all_homeworks_list_string(homeworks: list[Homework]) -> str:
    result = ''
    
    # Приводим все к формату {номер урока: [задания, отсортированные по номеру группы]}
    pos_to_homeworks: dict[int: list[Homework]] = {}
    for homework in homeworks:
        if pos_to_homeworks.get(homework.slot.position, 'none') == 'none':
            pos_to_homeworks[homework.slot.position] = []
        pos_to_homeworks[homework.slot.position].append(homework)
        
    for pos, homeworks_for_pos in pos_to_homeworks.items():
        if len(homeworks_for_pos) == 1:
            result += f'{pos + 1}. {format_homework_string(homeworks_for_pos[0])}'
        else:
            result += f'{pos + 1}. ' + '\n    '.join([format_homework_string(homework) for homework in homeworks_for_pos])
        result += '\n'
    return result
        
    
def format_homework_string(homework: Homework) -> str:
    subject_and_group_string = f'{homework.subject.name.capitalize()}{f" ({homework.group.as_number()} группа)" if homework.group != GroupNumberEnum.NOT_GROUPED else ""}'
    if not homework.is_empty:
        return f'{EXISTED_HOMEWORK_MARKER} {subject_and_group_string}: {homework.text}'
    return f'{NO_HOMEWORK_MARKER} {subject_and_group_string}'

