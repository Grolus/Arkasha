
from typing import Any, Callable
import datetime

from aiogram import BaseMiddleware
from aiogram.types import Update

from model import WWDate

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
        wwdate = WWDate.from_date(now)
        data.update({'wwdate': wwdate})
        return await handler(update, data)

