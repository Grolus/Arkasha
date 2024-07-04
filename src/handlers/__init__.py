
from . import (
    start,
    new_homework,
    configure,
    edit_configuration
)

routers = [
    start.router,
    new_homework.router,
    configure.router,
    edit_configuration.router
]

__all__ = ('routers')
