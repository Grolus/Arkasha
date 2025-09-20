
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from ..middlewares.getclass import SetClassState, ChoosedClassCallback

import service.class_service as service




# service.set_class_for_chat: Callable[[int, Class], bool]

router = Router(name="setclass")



@router.callback_query(SetClassState.choosing_class, ChoosedClassCallback.filter())
async def choosed_class_for_chat(callback: CallbackQuery, state: FSMContext):
    # получение класса из callback data
    class_ = ChoosedClassCallback.unpack(callback.data).get_class()
    
    chat_id = callback.message.chat.id
    await service.set_class_for_chat(class_, chat_id)
    await state.clear()
    return await callback.message.edit_text(f'Теперь этот чат - класс <b>{class_.name}</b>')