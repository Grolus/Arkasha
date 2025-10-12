
from model import Class, Lesson, Subject, Timetable, Weekday, Homework, Slot, WWDate, DailyTimetable

from database.models import ClassBase, LessonBase, HomeworkBase
from database.dao.dao import ClassDAO

from enums import GroupNumberEnum

def class_to_model(table_class: ClassBase, lessons: list[LessonBase]):
    # lessons = ClassDAO.get_lessons(table_class)
    timetable = lessons_to_timetable(lessons)
    return Class(
        name=table_class.name,
        creator_username=table_class.creator_username,
        timetable=timetable
    )
    
def lessons_to_timetable(table_lessons: list[LessonBase]) -> Timetable:
    timetable_dict = {}
    for lesson in table_lessons:
        if not (lessons_dict := timetable_dict.get(lesson.weekday_number)):
            lessons_dict = {}
            timetable_dict[lesson.weekday_number] = lessons_dict
        if lesson.group_number == GroupNumberEnum.NOT_GROUPED:
            lessons_dict[lesson.position] = [Lesson(subject=subject_to_model(lesson.subject))]
        else:
            if not (lessons_list := lessons_dict.get(lesson.position)):
                lessons_dict[lesson.position] = [None, None]
                lessons_list = lessons_dict[lesson.position]
            group_pos = 0 if lesson.group_number == GroupNumberEnum.FIRST else 1
            lessons_list[group_pos] = Lesson(subject=subject_to_model(lesson.subject))
    
    for k, v in timetable_dict.items():
        lessons_list = [None] * (max(v.keys()) + 1)
        for i, j in v.items():
            lessons_list[i] = j
        timetable_dict[k] = lessons_list

    timetable_dict = {
        Weekday(weekday_number): DailyTimetable(lessons=[
            lesson for lesson in lessons
        ])
        for weekday_number, lessons in timetable_dict.items()
    }
    return Timetable(timetable_dict=timetable_dict)    

def subject_to_model(table_subject: Subject):
    return Subject(name=table_subject.name)

def homework_to_model(table_homework: HomeworkBase) -> Homework:
    
    return Homework(
        subject=subject_to_model(table_homework.lesson.subject),
        text=table_homework.text,
        class_=class_to_model(table_homework.class_, table_homework.class_.lessons),
        slot=Slot(
            wwdate=WWDate(
                weekday=Weekday(table_homework.lesson.weekday_number),
                week=table_homework.week,
                year=table_homework.year
            ),
            position=table_homework.lesson.position
        ),
        attachment_url=table_homework.attachment_url,
        group=table_homework.lesson.group_number
    )


def lesson_to_model(table_lesson: LessonBase) -> Lesson:
    return Lesson(subject=subject_to_model(table_lesson.subject))

