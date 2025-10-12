from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, text

from .base import BaseDAO
from ..models import ClassBase, SubjectBase, LessonBase, HomeworkBase, ClassChatBase, GroupNumberEnum

from model import Timetable, WWDate

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
    
    @classmethod 
    async def get_id_by_name(cls, session: AsyncSession, class_name: str) -> int:
        # print('dao.py:28 class_name=%s' % class_name)
        return (await cls.get_by_name(session, class_name)).id
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
        print('find subject %s' % subject_name)
        subject = (await cls.get_by_fields(session, (cls.model.name, subject_name))).one()
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
        for wd, daily_tt in timetable.timetable_dict.items():
            for pos, lessons in enumerate(daily_tt.lessons):
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
    
    @classmethod
    async def get_awaible_homeworks(cls, session: AsyncSession, class_id: int, subject_id: int, group: GroupNumberEnum, now_wwdate: WWDate) -> list[HomeworkBase]:
        query = select(cls.model).join(
            LessonBase, 
            cls.model.lesson_id == LessonBase.id
        ).where(
            cls.model.class_id == class_id,
            LessonBase.subject_id == subject_id,
            LessonBase.group_number == group,
            cls.model.week >= now_wwdate.week,
            or_(
                LessonBase.weekday_number > int(now_wwdate.weekday),
                cls.model.week > now_wwdate.week
            )
        )
        print(f"dao.py:128 {query=!s}")
        result = await session.execute(query)
        homeworks = list(result.scalars())
        return homeworks
    
    @classmethod
    async def get_last_saved_homework(cls, session: AsyncSession, class_id: int, subject_id: int, group: GroupNumberEnum) -> HomeworkBase | None:
        query = select(cls.model).join(
            LessonBase,
            cls.model.lesson_id == LessonBase.id
        ).where(
            cls.model.class_id == class_id,
            LessonBase.subject_id == subject_id,
            LessonBase.group_number == group
        ).order_by(
            cls.model.year,
            cls.model.week,
            LessonBase.weekday_number,
            LessonBase.position
        ).limit(1)
        
        result = await session.execute(query)
        
        homework = result.one_or_none()
        return homework[0] if homework else None
    
    @classmethod
    async def get_all_homeworks_for_day(cls, session: AsyncSession, class_id: int, weekday_number: int, week: int, year: int) -> list[HomeworkBase]:
        # print(f'{class_id=}, {weekday_number=}, {week=}, {year=}')
        query = (
            select(LessonBase, HomeworkBase)
            .outerjoin(HomeworkBase, HomeworkBase.lesson_id==LessonBase.id)
            .join(SubjectBase, SubjectBase.id==LessonBase.subject_id)
            .where(
                LessonBase.class_id == class_id,
                LessonBase.weekday_number == weekday_number,
                or_(HomeworkBase.class_id == class_id, HomeworkBase.class_id == None),
                or_(HomeworkBase.week == week, HomeworkBase.week == None),
                or_(HomeworkBase.year == year, HomeworkBase.year == None)
            )
            .order_by(LessonBase.position, LessonBase.group_number)
        )
        
        # print('dao.py:172 query=', str(query), )
        
        result = await session.execute(query)
        
        
        # print('result:')
        # for row in result:
            
        #     print(*row, sep='; ')
        
        return [(lesson, homework) for lesson, homework in result]