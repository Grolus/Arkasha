from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

router = Router(name="testing")
class States(StatesGroup):
    test_state = State()
    typing_homework = State()
"""



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
"""


# @router.message()
# async def echo_handler(message: Message):
#     return await message.reply(message.text)

# @router.message(Command('test'))
# async def test_handler(message: Message, state: FSMContext):
#     await state.set_state(States.test_state)
#     return await message.reply("?")

# @router.message(
#     Command('new_homework'), 
#     F.reply_to_message.is_not(None).text.as_('homework_text'), 
#     F.reply_to_message.as_("message_with_homework")
# )
# @router.message(
#     States.typing_homework, 
#     F.text.as_('homework_text'), 
#     F.as_('message_with_homework')
# )
# @router.message(States.test_state)
# async def test21(message: Message, state: FSMContext):
#     # is_with_attachment = not not message_with_homework.photo
#     print('мы тут')
#     await state.clear()
#     # saving collected information
    # return await message.reply('ura, %s' % message.text)