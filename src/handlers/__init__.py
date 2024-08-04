
from . import (
    start,
    new_homework,
    configure,
    edit_configuration,
    debug,
    setclass,
    new_chat
)

routers = [
    debug.router,
    start.router,
    new_homework.router,
    configure.router,
    edit_configuration.router,
    new_chat.router,
    setclass.router,
]

__all__ = ('routers')
