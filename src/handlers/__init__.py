
from . import (
    middlewares,
    
    class_,
    homework,

    cancel,
    debug,
    selfcall,
    start
)


__all__ = ('routers', 'middlewares')

routers = [
    cancel.router,
    debug.router,
    selfcall.router,
    start.router,

    *class_.routers,
    *homework.routers
]

