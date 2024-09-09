
from . import (
    middlewares,
    
    class_,
    homework,

    debug,
    selfcall,
    start
)


__all__ = ('routers', 'middlewares')

routers = [
    debug.router,
    selfcall.router,
    start.router,

    *class_.routers,
    *homework.routers
]

