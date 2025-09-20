from sqlalchemy.ext.asyncio import AsyncSession

from model import Class

from database.dao.dao import ClassDAO, LessonDAO, ClassChatDAO
from database.database import connection
from database.models import ClassBase

from .converter import class_to_model


@connection
async def validate_class_name(session, new_class_name: str) -> bool:
    return await ClassDAO.validate_class_name(session, new_class_name)
    
@connection
async def save_new_class(session: AsyncSession, class_: Class) -> None:
    class_id = await ClassDAO.insert(session, name=class_.name, creator_username=class_.creator_username)
    await LessonDAO.insert_timetable(session, class_id, class_.timetable)
    await session.commit()
    

@connection
async def set_class_for_chat(class_: Class, chat_id: int, session: AsyncSession=...) -> None:
    class_table = await ClassDAO.get_by_name(session, class_.name)
    await ClassChatDAO.set_class_for_chat(class_table.id, chat_id, session)
    await session.commit()
    
@connection
async def get_class_for_chat_id(chat_id: int, session: AsyncSession) -> Class | None:
    class_table = await ClassChatDAO.get_class(chat_id, session)
    if class_table:
        class_ = class_to_model(class_table, await LessonDAO.get_all_for_class(class_table.id, session))
        return class_
    return None
    
@connection
async def get_user_classes(username: str, session: AsyncSession) -> list[Class]:
    table_classes = await ClassDAO.get_by_user(username, session)
    classes = [class_to_model(table_class, await LessonDAO.get_all_for_class(table_class.id, session)) for table_class in table_classes]
    return classes
    
    
    