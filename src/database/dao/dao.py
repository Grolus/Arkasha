from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .base import BaseDAO
from ..models import ClassBase, SubjectBase, LessonBase, HomeworkBase, ClassChatBase, GroupNumberEnum

from model import Timetable, Weekday, Lesson

class ClassDAO(BaseDAO):
    model = ClassBase
    
    @classmethod
    async def validate_class_name(cls, session: AsyncSession, class_name: str) -> bool:
        stmt = select(cls.model).where(cls.model.name == class_name).limit(1)
        result = await session.execute(stmt)
        if result.all():
            return False
        return True
    
    @classmethod
    async def get_by_name(cls, session: AsyncSession, class_name: str) -> ClassBase | None:
        stmt = select(cls.model).where(cls.model.name == class_name).limit(1)
        result = await session.execute(stmt)
        return result.scalar()
    
    # @classmethod
    # async def get_lessons(cls, class_: ClassBase, session: AsyncSession) -> Timetable:
    #     stmt = select(cls.model).where()
    
    @classmethod
    async def get_by_user(cls, username: str, session: AsyncSession) -> list[ClassBase]:
        stmt = select(cls.model).where(cls.model.creator_username == username)
        result = await session.execute(stmt)
        classes = result.scalars()
        return list(classes)
        
class ClassChatDAO(BaseDAO):
    model = ClassChatBase
    
    @classmethod
    async def set_class_for_chat(cls, class_id: int, chat_id: int, session: AsyncSession) -> int:
        classchat = cls.model(chat_id=chat_id, class_id=class_id)
        session.add(classchat)
        await session.flush()
        return classchat.id
        
    @classmethod
    async def get_class(cls, chat_id: int, session: AsyncSession) -> ClassBase | None:
        result = await cls.get_by_fields(session, (cls.model.chat_id, chat_id))
        scalar = result.one_or_none()
        if scalar:
            return await session.get(ClassBase, scalar.class_id)
        
class SubjectDAO(BaseDAO):
    model = SubjectBase
    
    @classmethod
    async def get_id_by_name(cls, session, subject_name: str) -> int:
        subject = (await cls.get_by_fields(session, name=subject_name))[0]
        return subject.id
    
class LessonDAO(BaseDAO):
    model = LessonBase
    
    @classmethod
    async def get_all_for_class(cls, class_id: int, session: AsyncSession) -> list[LessonBase]:
        stmt = select(cls.model).where(cls.model.class_id == class_id)
        result = await session.execute(stmt)
        lessons = result.scalars().all()
        return lessons
    
    @classmethod
    async def insert_timetable(cls, session: AsyncSession, class_id: int, timetable: Timetable):
        lesson_rows = []
        inserted_subjects: dict[str: int] = {}
        for wd, lessons in timetable.timetable_dict.items():
            for pos, lessons in enumerate(lessons):
                if len(lessons) == 1:
                    subject_name = lessons[0].subject.name
                    if not (subject_id := inserted_subjects.get(subject_name)):
                        subject_id = await SubjectDAO.insert(session, name=subject_name, class_id=class_id)
                        inserted_subjects[subject_name] = subject_id
                    lesson_rows.append({
                        'weekday_number': int(wd),
                        'position': pos,
                        'group_number': GroupNumberEnum.NOT_GROUPED,
                        'class_id': class_id,
                        'subject_id': subject_id
                    })
                elif len(lessons) == 2:
                    for lesson, group in zip(lessons, [GroupNumberEnum.FIRST, GroupNumberEnum.SECOND]):
                        subject_name = lesson.subject.name
                        if not (subject_id := inserted_subjects.get(subject_name)):
                            subject_id = await SubjectDAO.insert(session, name=subject_name, class_id=class_id)
                            inserted_subjects[subject_name] = subject_id
                        lesson_rows.append({
                            'weekday_number': int(wd),
                            'position': pos,
                            'group_number': group,
                            'class_id': class_id,
                            'subject_id': subject_id
                        })
        await cls.insert_many(session, lesson_rows)
    
    
class HomeworkDAO(BaseDAO):
    model = HomeworkBase