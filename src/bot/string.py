from model import WWDate, Slot

def format_relative_slot_string(now_wwdate: WWDate, slot: Slot) -> str:
    """Преобразует `slot` к строке вида `'Понедельник ... недели [назад], 1 урок'`"""
    weekday_word = slot.wwdate.weekday.name_ru
    position_part = f"{slot.position} урок"

    # если неделя не меняется и день впереди - строка недели пуста
    # если неделя не меняется и день этот или сзади - "этой недели"
    # если неделя впереди - "следующей недели", "через {2+} недель(и)"
    if now_wwdate.week == slot.wwdate.week:
        if slot.wwdate.weekday > now_wwdate.weekday:
            week_part = ""
        else:
            week_part = " этой недели"
    else:
        difference = abs(slot.wwdate.week - now_wwdate.week)
        if difference % 100 >= 5 and difference % 100 <= 20:
            week_word = "недель"
        elif difference % 10 == 1:
            week_word = "неделю"
        elif difference % 10 >= 2 and difference % 10 <= 4:
            week_word = "недели"
        else:
            week_word = "недель"
        if slot.wwdate.week > now_wwdate.week:
            if difference == 1:
                week_part = " следующей недели"
            else:
                week_part = f" через {difference} {week_word}"
        else:
            if difference == 1:
                week_part = " прошлой недели"
            else:
                week_part = f" {difference} {week_word} назад"
        
    result = f"{position_part}, {weekday_word}{week_part}"
    return result
