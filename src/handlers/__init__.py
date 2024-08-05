
from . import (
    start,
    configure,
    edit_configuration,
    debug,
    setclass,
    new_chat,
    new_homework,
    get_homework,
)

routers = [
    debug.router,
    start.router,
    new_homework.router,
    configure.router,
    edit_configuration.router,
    new_chat.router,
    setclass.router,
    get_homework.router,
    get_homework.extra_router
]

__all__ = ('routers')
