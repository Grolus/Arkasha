from .start import router as start_router
from .create_class import router as create_class_router
from .testing import router as test_router

routers = [
    start_router,
    create_class_router,
    test_router
]

__all__ = (
    "routers"
)