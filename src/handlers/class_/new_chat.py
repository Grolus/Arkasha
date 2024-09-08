from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.methods import SendMessage

from storage.tables import ChatTable, AdministratorTable
from config import BOT_ID, BOT_USERNAME

router = Router(name='new_chat')


@router.message(F.new_chat_members.func(lambda l: any([i.id for i in l if i.id == BOT_ID])))
async def added_to_chat(message: Message):
    adder = message.from_user.username
    chat_name = message.chat.title
    classes = AdministratorTable(adder).get_classes()
    if classes:
        return await SendMessage(
            chat_id=message.from_user.id, 
            text=f'Вы добавили меня в чат <b>{chat_name}</b>. Выберите класс для этого чата',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=class_.name, callback_data=f'choosedclassforchat_{class_.connected_table_value.id_}'
                )] for class_ in classes
            ]))
    else:
        parameter = f'createnewclassfor_{message.chat.id}'
        return await message.answer(
            'Чтобы я начал свою работу, создайте или выберите класс',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Создать', url=f'tg://resolve?domain={BOT_USERNAME}&start={parameter}')]
            ]))
    



