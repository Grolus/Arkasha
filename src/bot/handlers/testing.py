from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

router = Router(name="testing")


class Statess(StatesGroup):
    test_state = State()


@router.message(Command("kb"))
async def test2(message: Message, state: FSMContext):
    await state.set_state(Statess.test_state)
    await message.answer(

        "msg",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text='text', callback_data='cbdata')]]
        )
    )

@router.callback_query(Statess.test_state)
async def test3(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("wow")
