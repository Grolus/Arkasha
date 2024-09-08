from . import (
    all_homework, btw_new_homework, get_homework, new_homework
)

__all__ = ('routers')

routers = [
    all_homework.router,
    btw_new_homework.router,
    get_homework.router,
    new_homework.router
]
