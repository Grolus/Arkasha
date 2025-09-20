from sqlalchemy.ext.asyncio import AsyncSession

from model import Homework

from database.dao.dao import HomeworkDAO, ClassDAO, LessonDAO, SubjectDAO
from database.database import connection

@connection
async def save_homework(homework: Homework, session: AsyncSession) -> None:
    class_id = (await ClassDAO.get_by_name(homework.class_.name)).id
    subject_id = await SubjectDAO.get_id_by_name(session, homework.subject.name)
    lesson_id = await LessonDAO.get_by_fields(
        weekday_number=homework.slot.wwdate.weekday.weekday_number,
        position=homework.slot.position,
        group_number=homework.group,
        class_id=class_id,
        subject_id=subject_id
    ).id
    await HomeworkDAO.insert(session, text=homework.text, class_id=class_id, lesson_id=lesson_id)
    await session.commit()