from sqlalchemy.ext.asyncio import AsyncSession

from model import Class

from database.dao.dao import ClassDAO, LessonDAO
from database.database import connection
from database.models import ClassBase


@connection
async def validate_class_name(session, new_class_name: str) -> bool:
    return await ClassDAO.validate_class_name(session, new_class_name)
    
@connection
async def save_new_class(session, class_: Class) -> None:
    class_id = await ClassDAO.insert(session, name=class_.name, creator_username=class_.creator_username)
    await LessonDAO.insert_timetable(session, class_id, class_.timetable)

@connection
async def set_class_for_chat(class_: Class, chat_id: int, session: AsyncSession=...) -> None:
    class_table = await ClassDAO.get_by_name(session, class_.name)
    
    
async def get_class_for_chat_id(chat_id: int) -> Class:
    ...
    
async def get_user_classes(username: str) -> list[Class]:
    ...