
from model import Timetable, Class
from logers import class_service_logger as loger
from data import class_data as data

async def validate_class_name(new_class_name: str) -> bool: # TODO
    """Проверяет, можно ли использовать имя для создания нового класса"""
    return await data.validate_class_name(new_class_name=new_class_name)

async def save_new_class(class_name: str, creator_username: str, timetable: Timetable) -> None: # TODO
    class_ = Class(name=class_name, creator_username=creator_username, timetable=timetable)
    loger.info(f"Saving new class: {class_!r}")
    await data.save_new_class(class_=class_)
    
async def set_class_for_chat(class_: Class, chat_id: int) -> None:
    return data.set_class_for_chat(class_, chat_id)
    
async def get_class_for_chat_id(chat_id: int) -> Class | None:
    return data.get_class_for_chat_id(chat_id)
    
async def get_user_classes(username: str) -> list[Class]:
    return data.get_user_classes(username)
    