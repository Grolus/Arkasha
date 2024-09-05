
from typing import Any, Callable
import datetime

from aiogram import BaseMiddleware
from aiogram.types import Update

from utils.tools import get_now_week
from utils import Weekday

class GetWeekAndWeekdayMiddleware(BaseMiddleware):
    async def __call__(
        self, handler: Callable,
        update: Update,
        data: dict[str: Any]
    ):
        if update.message:
            now = update.message.date
        else:
            now = datetime.date.today()
        now_week = get_now_week(now)
        now_weekday = Weekday(now.weekday())
        data.update({'week': now_week, 'weekday': now_weekday})
        return await handler(update, data)

