from . import (
    configure, edit_configuration, new_chat, setclass, print_timetable
)


__all__ = ('routers')

routers = [
    configure.router,
    edit_configuration.router,
    new_chat.router,
    setclass.router,
    print_timetable.router
]
