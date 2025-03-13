
from model import Timetable, Class, User
from logers import class_service_logger as loger

def validate_class_name(new_class_name: str) -> bool: # TODO
    """Проверяет, можно ли использовать имя для создания нового класса"""
    return not (new_class_name == 'есть')

def save_new_class(class_name: str, creator_username: str, creator_fullname: str, timetable: Timetable) -> Class:
    class_ = Class(name=class_name, creator=User(username=creator_username, fullname=creator_fullname), timetable=timetable)
    loger.info(f"Saving new class: {class_!r}")
    return class_