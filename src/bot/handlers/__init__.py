from .start import router as start_router
from .setclass import router as setclass_router
from .create_class import router as create_class_router
from .testing import router as test_router
from .new_homework import router as hw_set_router
from .get_homework import router as hw_get_router
from .instant_get_homework import router as instant_hw_get_router

routers = [
    start_router,
    create_class_router,
    hw_set_router,
    hw_get_router,
    instant_hw_get_router,
    setclass_router,
    test_router,
]

__all__ = (
    "routers"
)