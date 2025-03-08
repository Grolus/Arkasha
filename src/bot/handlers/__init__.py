from .start import router as start_router
from .create_class import router as create_class_router


routers = [
    start_router,
    create_class_router
]

__all__ = (
    "routers"
)