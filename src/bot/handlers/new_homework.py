from enum import Enum

from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..middlewares import GetClassMiddleware
from ..callback_data.new_homework import (
    ChoosedSubjectCallback,
    CancelCallback,
    CheckOtherSubjectsCallback,
    ChoosedSlotCallback,
    ShowOtherSlotCallback,
    ChoosedGroupCallback
)
from ..string import format_relative_slot_string
from ..parsing.subject import parse_subjects_from_text

from model import Class, WWDate, Slot
from service import homework_service as service

router = Router(name="new_homework")
router.message.middleware(GetClassMiddleware())
router.callback_query.middleware(GetClassMiddleware())

class States(StatesGroup):
    typing_homework = State()
    choosing_subject = State()
    choosing_closest_slot = State()
    choosing_group = State()


class DataPart(str, Enum):
    text = 'text'
    paged_subject_list = 'paged_subject_list'
    subject = 'subject'
    group = 'group'
    message_url = 'message_url'


# Хендлер никак не может влиять на данные (только читать), пока операция не будет завершена.
# Следовательно, вызов операции записи потребуется один раз - в самом конце (в конце каждого варианта)

@router.callback_query(CancelCallback().filter())
async def cancel_hwset(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    return await callback.message.edit_text('Задание не сохранено')

@router.message(Command("new_homework"), F.reply_to_message.is_(None))
async def new_homework_setting(message: Message, state: FSMContext, class_: Class):
    await state.set_state(States.typing_homework)
    return await message.answer("Введите задание, которое хотите сохранить. Вы можете указать предмет в сообщении или выбрать его позже. При необходимости вы можете приложить любые фото/файлы")

@router.message(
    Command('new_homework'), 
    F.reply_to_message.is_not(None).text.as_('homework_text'), 
    F.reply_to_message.as_("message_with_homework")
)
@router.message(
    States.typing_homework, 
    F.text.as_('homework_text'), 
    F.as_('message_with_homework')
)
async def got_text(message: Message, state: FSMContext, class_: Class, homework_text: str, message_with_homework: Message):
    is_with_attachment = not not message_with_homework.photo

    # saving collected information
    await state.set_data({
        DataPart.text: homework_text,
        DataPart.message_url: 
            message_with_homework.get_url() if is_with_attachment else None
    })

    # answering
    subject_condidates = parse_subjects_from_text(homework_text, class_.get_subjects_list, 3)
    await state.set_state(States.choosing_subject)
    return await message.reply(
        f'Получено задание:\n<i>{homework_text}</i>\n\n<b>{message.from_user.full_name}</b>, выберите предмет для сохранения задания:',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=sj.name, callback_data=ChoosedSubjectCallback.from_subject(sj).pack()) for sj in subject_condidates],
            [InlineKeyboardButton(text='Предмета нет в списке', callback_data=CheckOtherSubjectsCallback().pack())],
            [InlineKeyboardButton(text='Отменить', callback_data=CancelCallback().pack())]
        ]))

@router.callback_query(States.choosing_subject, ChoosedSubjectCallback.filter())
async def subject_choosed(callback: CallbackQuery, state: FSMContext, class_: Class, wwdate: WWDate):
    
    # saving subject
    choosed_subject = ChoosedSubjectCallback.unpack(callback.data).get_subject()
    await state.update_data({
        DataPart.subject: choosed_subject
    })
    
    # группа?
    groups = service.get_subject_groups(class_, choosed_subject)
    if groups == 1:
        await state.update_data({
            DataPart.group: 1 
        })
        # сохранить на ближайший слот?
        closest_slot: Slot = service.get_closest_slot(class_, wwdate, choosed_subject)
        homework_text = (await state.get_data())[DataPart.text]
        await state.set_state(States.choosing_closest_slot)
        return await callback.message.edit_text(
            f'Получено задание по предмету <i>{choosed_subject.name}</i>:\n{homework_text}\n\nСохранить задание на ближайший урок?',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=format_relative_slot_string(wwdate, closest_slot), 
                    callback_data=ChoosedSlotCallback.from_slot(closest_slot).pack()
                )],
                [InlineKeyboardButton(text='Выбрать другой урок ➡', callback_data=ShowOtherSlotCallback().pack())]
            ])
        )
    else:
        # какая группа нужна?
        await state.set_state(States.choosing_group)
        return await callback.message.edit_text(
            f'Выберите группу для сохранения задания по предмету <i>{choosed_subject.name}</i>',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=f'{i+1} группа', callback_data=ChoosedGroupCallback(i+1).pack())
                for i in range(groups)
            ],
            [InlineKeyboardButton(text='Отменить', callback_data=CancelCallback().pack())]])
        )

@router.callback_query(States.choosing_group, ChoosedGroupCallback.filter())
async def choose_group(callback: CallbackQuery, state: FSMContext, class_: Class, wwdate: WWDate):

    # get group
    group = ChoosedGroupCallback.unpack(callback.data).group

    # save group
    await state.update_data({
        DataPart.group: group
    })

    # answer
    data = await state.get_data()
    subject, text = data[DataPart.subject], data[DataPart.text]
    closest_slot: Slot = service.get_closest_slot(class_, wwdate, subject)
    await state.set_state(States.choosing_closest_slot)
    return await callback.message.edit_text(
        f'Получено задание по предмету <i>{subject.name}</i>:\n{text}\n\nСохранить задание на ближайший урок?',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=format_relative_slot_string(wwdate, closest_slot), 
                    callback_data=ChoosedSlotCallback.from_slot(closest_slot).pack()
                )],
                [InlineKeyboardButton(text='Выбрать другой урок ➡', callback_data=ShowOtherSlotCallback().pack())]
            ])
    )

