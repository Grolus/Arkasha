
from model import Subject, Class, WWDate, Slot, Homework
from data import homework_data as data

    
def get_closest_slot(class_: Class, now_wwdate: WWDate, subject: Subject) -> Slot:
    now_weekday = now_wwdate.weekday
    for dweekday in range(1, 8):
        if lessons := class_.timetable.timetable_dict.get(now_weekday + dweekday):
            for pos, lesson in enumerate(lessons):
                if subject in lesson.subjects:
                    return Slot(
                        now_wwdate.year, 
                        now_wwdate.week + (now_weekday+dweekday <= now_weekday), 
                        now_weekday+dweekday, 
                        pos
                    )
                    
def get_subject_groups(class_: Class, subject: Subject) -> int:
    for lessons in class_.timetable.timetable_dict.values():
        for lesson in lessons:
            if len(lesson.subjects) > 1 and subject in lesson.subjects:
                return len(lesson.subjects)
            
            
async def save_homework(homework: Homework) -> None:
    data.save_homework(homework)
            
