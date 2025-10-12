from typing import Callable, Any

from aiogram import F, Router, BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from ..middlewares import GetClassMiddleware
from ..parsing.subject import get_most_similar_subjects_with_distantions
from ..public import get_prompt_from_file
from ..callback_data.new_homework import ChoosedSubjectCallback
from ..callback_data.get_homework import CancelCallback

from .get_homework import DataPart, GetHomeworkState

from logers import handle_loger as loger
from config.constants import MAX_SUBJECT_DISTANCE_IN_INSTANT_HOMEWORK_GETTING
from model import Class, Subject

router = Router(name='instant_get_homework')

subrouter_subject_checking = Router(name='instant_get_homework_subrouter')
router.sub_routers.append(subrouter_subject_checking)

def get_text(n: str) -> str:
    return get_prompt_from_file(f'instant_get_homework/{n}.txt')

class CheckForSubjectMiddleware(BaseMiddleware):
    """Ищет в тексте сообщения название какого-либо предмета, и если находит, возвращает в качестве доп. данных (аргумента в хендлере). 
    Если предмета нет, то хендлер не вызовется.
    Работает только после `GetClassMiddleware`, иначе - ошибка"""
    async def __call__(self, handler: Callable,
        message: Message,
        data: dict[str: Any]
    ):
        class_: Class = data['class_']
        dist_to_subject = get_most_similar_subjects_with_distantions(message.text, class_.get_subjects_list(), 1)
        dist, subject = list(dist_to_subject.items())[0]
        if dist > MAX_SUBJECT_DISTANCE_IN_INSTANT_HOMEWORK_GETTING:
            loger.info(f'Instant Get Homework: subject {subject.name} has distant {dist} greater than {MAX_SUBJECT_DISTANCE_IN_INSTANT_HOMEWORK_GETTING}')
            return None
        loger.info(f'Instant Get Homework: finded subject {subject.name}')
        data['subject'] = subject
        return await handler(message, data)
    
router.message.middleware(GetClassMiddleware())
subrouter_subject_checking.message.middleware(GetClassMiddleware())
subrouter_subject_checking.message.middleware(CheckForSubjectMiddleware())

@subrouter_subject_checking.message(F.text.regexp(r'что по .*\?'))
async def subject_found(message: Message, state: FSMContext, class_: Class, subject: Subject):
    
    await state.set_data({DataPart.subject: subject})
    await state.set_state(GetHomeworkState.instant_triggered)
    
    return await message.reply(
        get_text('subject_found').format(subject_name=subject.name),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=get_text('yes_button'), callback_data=ChoosedSubjectCallback.from_subject(subject).pack()),
            InlineKeyboardButton(text=get_text('no_button'), callback_data=CancelCallback().pack())
        ]])
    )
    