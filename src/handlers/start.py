from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from filters import ChatTypeFilter

from utils.states import ConfigureState

router = Router(name='start')

@router.message(
    CommandStart(),
    ChatTypeFilter('private')
)
async def start(message: Message, state: FSMContext):
    parameter = message.text.split()[1] if ' ' in message.text else ''
    if parameter.startswith('createnewclassfor_'):
        chat_id = int(parameter.split('_')[1])
        await state.set_state(ConfigureState.typing_class_name)
        await state.set_data({'chat_id': chat_id})
        return await message.answer('Вы начали конфигурацию нового класса! Для начала придумайте уникальное имя для вашего нового класса. Например, "1А 1 школа"')
    else:
        return await message.answer(
        '''Привет, я <b>Аркаша</b> - бот для <u>облегчения</u> вашей школьной жизни.

        Я умею: 
            сохранять и рассказывать домашнее задание

        Для начала работы вам следует настроить бота под свой класс (/configure)'''
        )