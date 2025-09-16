
from model import Class, Lesson, Subject, Timetable, Weekday

from database.models import ClassBase, LessonBase, SubjectBase
from database.dao.dao import ClassDAO

from enums import GroupNumberEnum

def class_to_model(table_class: ClassBase):
    lessons = ClassDAO.get_lessons(table_class)
    
    Class(
        name=table_class.name,
        creator_username=table_class.creator_username,
        timetable=timetable
    )
    
def lessons_to_timetable(table_lessons: list[LessonBase]) -> Timetable:
    timetable_dict = {}
    for lesson in table_lessons:
        if not (lessons_list := timetable_dict.get(lesson.weekday_number)):
            lessons_list = []
            timetable_dict[lesson.weekday_number] = lessons_list
        if lesson.group_number == GroupNumberEnum.NOT_GROUPED:
            lessons_list.append(Lesson(subject=subject_to_model(lesson.subject)))
        else:
            lessons_list.
            
    return Timetable(timetable_dict=timetable_dict)
    

def subject_to_model(table_subject: Subject):
    return Subject(name=table_subject.name)

# def lesson_to_model(table_lesson: LessonBase) -> Lesson:
#     return Lesson(
#         subjects=[
#             subject_to_model(subject)
#             for subject in table_lesson.su
#         ]
#     )
