from . import (
    configure, edit_configuration, new_chat, setclass
)


__all__ = ('routers')

routers = [
    configure.router,
    edit_configuration.router,
    new_chat.router,
    setclass.router
]
