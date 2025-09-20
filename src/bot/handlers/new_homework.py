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
    ChoosedGroupCallback,
    PagingSubjectListCallback
)
from ..string import format_relative_slot_string
from ..parsing.subject import parse_subjects_from_text
from ..public import get_prompt_from_file

from model import Class, WWDate, Slot, Subject, Weekday, Homework
from model.paged_list import PagedList, allocate_values_to_nested_list
from service import homework_service as service
from enums import GroupNumberEnum

router = Router(name="new_homework")
router.message.middleware(GetClassMiddleware())
router.callback_query.middleware(GetClassMiddleware())

class States(StatesGroup):
    typing_homework = State()
    choosing_subject = State()
    choosing_slot = State()
    choosing_group = State()


class DataPart(str, Enum):
    text = 'text'
    paged_subject_list = 'paged_subject_list'
    subject = 'subject'
    group = 'group'
    message_url = 'message_url'

def get_text(filename: str) -> str:
    """Returns text from `public/homework_set/{filename}.txt`"""
    return get_prompt_from_file('new_homework/' + filename + '.txt')
    
def get_button_text(filename: str) -> str:
    """Returns text from `public/homework_set/button/{filename}.txt"""
    return get_text('button/' + filename)


class PagedSubjectList(PagedList):
    def __init__(self, all_subjects: list[list[Subject]], page_size: int):
        super().__init__(all_subjects, page_size)
    def get_current_page_as_keyboard(self) -> InlineKeyboardMarkup:
        page = self.current_page()
        
        page_changing_buttons = []
        if not self.is_page_first():
            page_changing_buttons.append(
                InlineKeyboardButton(text=get_button_text('list_backward'), callback_data=PagingSubjectListCallback(direction='down').pack())
            )
        if not self.is_page_last():
            page_changing_buttons.append(
                InlineKeyboardButton(text=get_button_text('list_forward'), callback_data=PagingSubjectListCallback(direction='up').pack())
            )

        return InlineKeyboardMarkup(inline_keyboard=allocate_values_to_nested_list([
            InlineKeyboardButton(text=subject.name, callback_data=ChoosedSubjectCallback.from_subject(subject).pack())
            for subject in page
        ], 3) + [page_changing_buttons] + [[InlineKeyboardButton(text=get_button_text('cancel'), callback_data=CancelCallback().pack())]])



# Хендлер никак не может влиять на данные (только читать), пока операция не будет завершена.
# Следовательно, вызов операции записи потребуется один раз - в самом конце (в конце каждого варианта)

@router.callback_query(CancelCallback().filter())
async def cancel_hwset(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    return await callback.message.edit_text(get_text('canceled'))

@router.message(Command("new_homework"), F.reply_to_message.is_(None))
async def new_homework_setting(message: Message, state: FSMContext, class_: Class):
    await state.set_state(States.typing_homework)
    return await message.answer(get_text('start'))

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
        get_text('choose_subject').format(homework_text=homework_text, full_name=message.from_user.full_name),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=sj.name, callback_data=ChoosedSubjectCallback.from_subject(sj).pack()) for sj in subject_condidates],
            [InlineKeyboardButton(text=get_button_text('no_subject'), callback_data=CheckOtherSubjectsCallback().pack())],
            [InlineKeyboardButton(text=get_button_text('cancel'), callback_data=CancelCallback().pack())]
        ]))

@router.callback_query(States.choosing_subject, CheckOtherSubjectsCallback.filter())
async def choose_another_subject(callback: CallbackQuery, state: FSMContext, class_: Class, weekday: Weekday):
    paged_list = PagedSubjectList(class_.get_subject_list_for_paged_list(weekday), 9)
    text = (await state.get_data())[DataPart.text]
    await state.update_data({DataPart.paged_subject_list: paged_list})
    return await callback.message.edit_text(
        f'Получено задание:\n<i>{text}</i>\n\n<b>{callback.from_user.full_name}</b>, выберите предмет для сохранения задания:',
        reply_markup=paged_list.get_current_page_as_keyboard()
    )

@router.callback_query(States.choosing_subject, PagingSubjectListCallback.filter())
async def subject_list_rolling(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    paged_list = data[DataPart.paged_subject_list]
    action = callback.data.split('_')[1]
    match action:
        case 'pageup':
            paged_list.page_up()
        case 'pagedown':
            paged_list.page_down()
    return await callback.message.edit_reply_markup(reply_markup=paged_list.get_current_page_as_keyboard())

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
        await state.set_state(States.choosing_slot)
        return await callback.message.edit_text(
            get_text('choose_slot').format(subject_name=choosed_subject.name, homework_text=homework_text),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=format_relative_slot_string(wwdate, closest_slot), 
                    callback_data=ChoosedSlotCallback.from_slot(closest_slot).pack()
                )],
                [InlineKeyboardButton(text=get_button_text('choose_another_slot'), callback_data=ShowOtherSlotCallback().pack())]
            ])
        )
    else:
        # какая группа нужна?
        await state.set_state(States.choosing_group)
        return await callback.message.edit_text(
            get_text('choose_group').format(subject_name=choosed_subject.name),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text=get_button_text('group').format(number=i), callback_data=ChoosedGroupCallback(i+1).pack())
                for i in range(groups)
            ],
            [InlineKeyboardButton(text=get_button_text('cancel'), callback_data=CancelCallback().pack())]])
        )


@router.callback_query(States.choosing_group, ChoosedGroupCallback.filter())
async def choose_group(callback: CallbackQuery, state: FSMContext, class_: Class, wwdate: WWDate):

    # get group
    group_number = ChoosedGroupCallback.unpack(callback.data).group
    group = GroupNumberEnum.FIRST if group_number == 1 else GroupNumberEnum.SECOND

    # save group
    await state.update_data({
        DataPart.group: group
    })

    # answer
    data = await state.get_data()
    subject, text = data[DataPart.subject], data[DataPart.text]
    closest_slot: Slot = service.get_closest_slot(class_, wwdate, subject)
    await state.set_state(States.choosing_slot)
    return await callback.message.edit_text(
        get_text('choose_slot').format(subject_name=subject.name, homework_text=text),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=format_relative_slot_string(wwdate, closest_slot), 
                    callback_data=ChoosedSlotCallback.from_slot(closest_slot).pack()
                )],
                [InlineKeyboardButton(text=get_button_text('choose_another_slot'), callback_data=ShowOtherSlotCallback().pack())]
            ])
    )

@router.callback_query(States.choosing_slot, F.data == 'chooseanotherslothwset')
async def choose_slot_to_save(callback: CallbackQuery, state: FSMContext, class_: Class, wwdate: WWDate):
    data = await state.get_data()
    subject = data[DataPart.subject]
    homework_text = data[DataPart.text]
    group_number = data[DataPart.group]
    awaible_slots = class_.timetable.get_relative_slots_for_subject(subject, group_number, wwdate)
    await state.set_state(States.choosing_slot)
    
    return await callback.message.edit_text(
        f'Получено задание по предмету <i>{subject.name}</i>:\n{homework_text}\n\nВыберите урок для сохранения...',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=format_relative_slot_string(wwdate, slot), 
                callback_data=ChoosedSlotCallback(
                    weekday_number=slot.wwdate.weekday.weekday_number, 
                    week=slot.wwdate.week, 
                    year=slot.wwdate.year, 
                    position=slot.position
                )
            )]
            for slot in awaible_slots
            
        ] + [[InlineKeyboardButton(text='Отменить', callback_data='cancel_hwset')]])
    )


@router.callback_query(States.choosing_slot, ChoosedSlotCallback.filter())
async def complete_homework(callback: CallbackQuery, state: FSMContext, class_: Class, week: int):
    slot = ChoosedSlotCallback.unpack(callback.data).get_slot()
    weekday, position, is_for_next_week = slot.to_tuple()
    data = await state.get_data()
    subject = data[DataPart.subject]
    text = data[DataPart.text]
    group = data[DataPart.group]
    message_url = data[DataPart.message_url]
    print(f'{message_url=}')
    collected_homework = Homework(
        subject=subject, text=text, class_=class_, slot=slot, group=group
    )
    await service.save_homework(collected_homework)

    await state.clear()
    return await callback.message.edit_text(
        get_text(
            'complete'
            if not message_url else
            'complete_with_attachment'
        ).format(
            subject_name=subject.name, 
            slot_string=format_relative_slot_string(slot), 
            homework_text=text, 
            full_name=callback.from_user.full_name
        )
    )


