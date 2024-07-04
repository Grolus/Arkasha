
from .connection import DBConection
import config

DBConection(**{k.lower():v for k, v in config.DATABASE.items()})

from . import  tables




__all__ = (
    'DBConection',
    'tables'
)


