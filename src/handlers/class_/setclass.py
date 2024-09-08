
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from storage.tables import AdministratorTable, ChatTable, ClassTable
from entities import Class
from config import BOT_USERNAME
from utils.states import SetClassState

router = Router()

@router.message(Command('setclass'))
async def set_class_handler(message: Message, state: FSMContext):
    classes = [Class.from_table_value(v) for v in AdministratorTable(message.from_user.username).get_classes()]

    if classes:
        await state.set_state(SetClassState.choosing_class)
        return await message.answer(
            f'<b>{message.from_user.full_name}</b>, выберите класс для чата <b>{message.chat.title}</b>',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=class_.name, callback_data=f'choosedclassforchat_{class_.connected_table_value.id_}')] for class_ in classes
            ])
        )
    else:
        parameter = f'createnewclassfor_{message.chat.id}'
        return await message.answer(
            f'<b>{message.from_user.full_name}</b>, у вас нет созданных классов',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Создать', url=f'tg://resolve?domain={BOT_USERNAME}&start={parameter}')]
            ])
        )

@router.callback_query(SetClassState.choosing_class, F.data.startswith('choosedclassforchat_'))
async def choosed_class_for_chat(callback: CallbackQuery, state: FSMContext):
    choosed_class_id = callback.data.split('_')[1]
    choosed_class = ClassTable.get_by_id(choosed_class_id)
    ChatTable(
        str(callback.message.chat.id),
        choosed_class,
        AdministratorTable(callback.from_user.username)
    ).insert()
    await state.set_state(None)
    return await callback.message.edit_text(f'Теперь этот чат - класс <b>{choosed_class.values.classname}</b>')

