
from . import (
    class_,
    homework,

    debug,
    selfcall,
    start
)

__all__ = ('routers')

routers = [
    debug.router,
    selfcall.router,
    start.router,

    *class_.routers,
    *homework.routers
]

