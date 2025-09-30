
from model import Subject, Class, WWDate, Slot, Homework
from enums import GroupNumberEnum
from data import homework_data as data

    
def get_closest_slot(class_: Class, now_wwdate: WWDate, subject: Subject, group: GroupNumberEnum) -> Slot:
    now_weekday = now_wwdate.weekday
    group_index = 0 if group == GroupNumberEnum.FIRST else 1 if group == GroupNumberEnum.SECOND else None
    for dweekday in range(1, 8):
        if lessons := class_.timetable.timetable_dict.get(now_weekday + dweekday):
            for pos, lesson in enumerate(lessons):
                if (len(lesson) == 1 and subject == lesson[0].subject
                    or
                    len(lesson) == 2 and group != GroupNumberEnum.NOT_GROUPED and subject == lesson[group_index].subject
                    ):
                    return Slot(
                        wwdate=WWDate(
                            year=now_wwdate.year, 
                            week=now_wwdate.week + (now_weekday+dweekday <= now_weekday), 
                            weekday=now_weekday+dweekday
                        ), 
                        position=pos
                    )
            
            
async def save_homework(homework: Homework) -> None:
    await data.save_homework(homework)
    
async def get_awaible_homeworks(class_: Class, subject: Subject, group: GroupNumberEnum, now_wwdate: WWDate) -> list[Homework]:
    """Возвращает все доступные задания, начиная со следющего дня (т. е. избегая старые задания). 
    Если ничего не сохранено - вернет пустой список"""
    return await data.get_awaible_homeworks(class_, subject, group, now_wwdate)
    
async def get_last_saved_homework(class_: Class, subject: Subject, group: GroupNumberEnum) -> Homework | None:
    """Возвращает последнее сохраненное дз по предмету или None, если никакого дз не сохраняли"""
    return await data.get_last_saved_homework(class_, subject, group) 
            
