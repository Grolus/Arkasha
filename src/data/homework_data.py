from sqlalchemy.ext.asyncio import AsyncSession

from model import Homework, Class, Subject, WWDate
from enums import GroupNumberEnum

from database.dao.dao import HomeworkDAO, ClassDAO, LessonDAO, SubjectDAO
from database.database import connection

from .converter import homework_to_model

@connection
async def save_homework(homework: Homework, session: AsyncSession) -> None:
    class_id = (await ClassDAO.get_by_name(session, homework.class_.name)).id
    subject_id = await SubjectDAO.get_id_by_name(session, homework.subject.name)
    lesson_id = (await LessonDAO.get_by_fields(
        session,
        (LessonDAO.model.weekday_number, homework.slot.wwdate.weekday.weekday_number),
        (LessonDAO.model.position, homework.slot.position),
        (LessonDAO.model.group_number, homework.group),
        (LessonDAO.model.class_id, class_id),
        (LessonDAO.model.subject_id, subject_id)
    )).one().id
    attachment_url = homework.attachment_url
    await HomeworkDAO.insert(
        session, 
        text=homework.text, 
        class_id=class_id, 
        lesson_id=lesson_id, 
        attachment_url=attachment_url, 
        week=homework.slot.wwdate.week,
        year=homework.slot.wwdate.year
    )
    await session.commit()
    
@connection
async def get_awaible_homeworks(class_: Class, subject: Subject, group: GroupNumberEnum, now_wwdate: WWDate, session: AsyncSession) -> list[Homework]:
    class_id = await ClassDAO.get_id_by_name(session, class_.name)
    subject_id = await SubjectDAO.get_id_by_name(session, subject.name)
    homework_tables = await HomeworkDAO.get_awaible_homeworks(session, class_id, subject_id, group, now_wwdate)
    homeworks = [homework_to_model(hw) for hw in homework_tables]
    return homeworks

@connection
async def get_last_saved_homework(class_: Class, subject: Subject, group: GroupNumberEnum, session: AsyncSession) -> Homework | None:
    class_id = await ClassDAO.get_id_by_name(session, class_.name)
    subject_id = await SubjectDAO.get_id_by_name(session, subject.name)
    homework = await HomeworkDAO.get_last_saved_homework(session, class_id, subject_id, group)
    if not homework:
        return None
    return homework_to_model(homework)
    