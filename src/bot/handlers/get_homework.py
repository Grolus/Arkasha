
from enum import Enum

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state, State, StatesGroup
from aiogram.filters import Command

from ..middlewares import GetClassMiddleware
from ..public import get_prompt_from_file
from ..string import format_relative_slot_string
from ..callback_data.new_homework import (
    PagingSubjectListCallback,
    ChoosedSubjectCallback,
    ChoosedGroupCallback,
    ChoosedSlotCallback
)
from ..callback_data.get_homework import (
    CancelCallback,
    ShowLastHomeworkCallback,
)

from enums import GroupNumberEnum
from model import Class, Subject, Homework, WWDate
from model.paged_list import PagedList, allocate_values_to_nested_list
from service import homework_service as service


class GetHomeworkState(StatesGroup):
    choosing_subject = State()
    choosing_group = State()
    choosing_slot = State()

router = Router(name='get_homework')
router.message.middleware(GetClassMiddleware())
router.callback_query.middleware(GetClassMiddleware())

def get_text(name: str) -> str:
    return get_prompt_from_file('get_homework/%s.txt' % name)

def get_button_text(name: str) -> str:
    return get_text('button/' + name)

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

class DataPart(Enum):
    paged_list = 'paged_list'
    subject = 'subject'
    group = 'group'
    last_saved_homework = 'last_saved_homework'
    slot_to_homework = 'slot_to_homework'

@router.callback_query(any_state, CancelCallback.filter())
async def cancel_homework_getting(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    return await callback.message.delete()

@router.message(Command('get_homework'))
async def get_homework_start(message: Message, state: FSMContext, class_: Class):
    paged_list = PagedSubjectList(class_.get_subjects_list(), 9)
    current_page_kb = paged_list.get_current_page_as_keyboard()
    await state.set_data({DataPart.paged_list: paged_list})
    await state.set_state(GetHomeworkState.choosing_subject)
    return await message.reply(
        get_text('start'),
        reply_markup=current_page_kb
    )

@router.callback_query(GetHomeworkState.choosing_subject, PagingSubjectListCallback.filter())
async def page_changing(callback: CallbackQuery, state: FSMContext):
    direction = PagingSubjectListCallback.unpack(callback.data).direction
    paged_list: PagedSubjectList = (await state.get_data())[DataPart.paged_list]
    match direction:
        case 'up':
            paged_list.page_up()
        case 'down':
            paged_list.page_down()
    current_page_kb = paged_list.get_current_page_as_keyboard()
    return await callback.message.edit_reply_markup(
        reply_markup=current_page_kb
    )


@router.callback_query(
        GetHomeworkState.choosing_subject, 
        ChoosedSubjectCallback.filter()
    )
async def choosed_subject_with_group_handler(callback: CallbackQuery, state: FSMContext, class_: Class, wwdate: WWDate):
    subject = ChoosedSubjectCallback.unpack(callback.data).get_subject()
    await state.update_data({DataPart.subject: subject})
    if class_.get_if_subject_grouped(subject):
        await state.set_state(GetHomeworkState.choosing_group)
        return await callback.message.edit_text(
            get_text('choose_group').format(subject_name=subject.name),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text=get_button_text('group').format(number=i+1), 
                    callback_data=ChoosedGroupCallback(group=i+1).pack()
                )
                for i in range(2)
            ],
            [InlineKeyboardButton(text=get_button_text('cancel'), callback_data=CancelCallback().pack())]])
        )
    else:
        group = GroupNumberEnum.NOT_GROUPED
        await state.update_data({DataPart.group: group})
        homeworks = await service.get_awaible_homeworks(class_, subject, group, wwdate)
        if not homeworks:
            await state.clear()
            last_saved = await service.get_last_saved_homework(subject, group, class_)
            if last_saved:
                await state.update_data({DataPart.last_saved_homework: last_saved})
                return await callback.message.edit_text(
                    get_text('no_homework_shot_last').format(
                        subject_name=subject.name,
                        slot_string=format_relative_slot_string(wwdate, last_saved.slot)
                    ),
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(
                            text=get_button_text('show_last_yes'), 
                            callback_data=ShowLastHomeworkCallback(show=True).pack
                        ),
                        InlineKeyboardButton(
                            text=get_button_text('show_last_no'), 
                            callback_data=ShowLastHomeworkCallback(show=False).pack()
                        )
                    ]]))
            else:
                return await callback.message.edit_text(
                    get_text('no_homework').format(subject_name=subject.name)
                )
        slot_to_homework = {hw.slot : hw for hw in homeworks}
        slots = list(slot_to_homework.keys())
        await state.update_data({DataPart.slot_to_homework: slot_to_homework})
        await state.set_state(GetHomeworkState.choosing_slot)
        return await callback.message.edit_text(
            get_text('choose_slot'),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text=format_relative_slot_string(wwdate, slot), callback_data=ChoosedSlotCallback.from_slot(slot).pack()
                )]
                for slot in slots
            ])
        )

@router.callback_query(GetHomeworkState.choosing_group, ChoosedGroupCallback.filter())
async def group_choosed(callback: CallbackQuery, state: FSMContext, class_: Class, wwdate: WWDate):
    match ChoosedGroupCallback.unpack(callback.data).group:
        case 1:
            group = GroupNumberEnum.FIRST
        case 2:
            group = GroupNumberEnum.SECOND
        case _:
            raise
    await state.update_data({DataPart.group: group})
    subject = (await state.get_data())[DataPart.subject]
    homeworks = await service.get_awaible_homeworks(class_, subject, group, wwdate)
    if not homeworks:
        await state.clear()
        last_saved = await service.get_last_saved_homework(subject, group, class_)
        if last_saved:
            await state.update_data({DataPart.last_saved_homework: last_saved})
            return await callback.message.edit_text(
                get_text('no_homework_show_last').format(
                    subject_name=subject.name,
                    slot_string=format_relative_slot_string(wwdate, last_saved.slot)
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        text=get_button_text('show_last_yes'), 
                        callback_data=ShowLastHomeworkCallback(show=True).pack
                    ),
                    InlineKeyboardButton(
                        text=get_button_text('show_last_no'), 
                        callback_data=ShowLastHomeworkCallback(show=False).pack()
                    )
                ]]))
        else:
            return await callback.message.edit_text(
                get_text('no_homework').format(subject.name)
            )
    slot_to_homework = {hw.slot : hw for hw in homeworks}
    slots = list(slot_to_homework.keys())
    await state.update_data({DataPart.slot_to_homework: slot_to_homework})
    await state.set_state(GetHomeworkState.choosing_slot)
    return await callback.message.edit_text(
        get_text('choose_slot'),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=format_relative_slot_string(wwdate, slot), callback_data=ChoosedSlotCallback.from_slot(slot).pack()
            )]
            for slot in slots
        ])
    )
    
@router.callback_query(GetHomeworkState.choosing_slot, ChoosedSlotCallback.filter())
async def send_homework_handler(callback: CallbackQuery, state: FSMContext, wwdate: WWDate):
    slot = ChoosedSlotCallback.unpack(callback.data).get_slot()
    slot_to_homework = (await state.get_data())[DataPart.slot_to_homework]
    choosed_homework = slot_to_homework[slot]
    await state.clear()
    return await callback.message.edit_text(
        get_text('homework').format(
            subject_name=choosed_homework.subject.name, 
            homework_text=choosed_homework.text,
            slot_string=format_relative_slot_string(wwdate, choosed_homework.slot)
        )
        if not choosed_homework.attachment_url else
        get_text('homework_with_attachment').format(
            subject_name=choosed_homework.subject.name, 
            homework_text=choosed_homework.text,
            attachment_url=choosed_homework.attachment_url,
            slot_string=format_relative_slot_string(wwdate, choosed_homework.slot)
        )
    )

@router.callback_query(ShowLastHomeworkCallback.filter())
async def get_last_homework(callback: CallbackQuery, state: FSMContext, wwdate: WWDate):
    if not ShowLastHomeworkCallback.unpack(callback.data).show:
        return await callback.message.delete()
    last_saved_homework = (await state.get_data())[DataPart.last_saved_homework]
    await state.clear()
    return await callback.message.edit_text(
        get_text('homework_legacy').format(
            subject_name=last_saved_homework.subject.name, 
            homework_text=last_saved_homework.text,
            slot_string=format_relative_slot_string(wwdate, last_saved_homework.slot)
        )
        if not last_saved_homework.attachment_url else
        get_text('homework_legacy_with_attachment').format(
            subject_name=last_saved_homework.subject.name, 
            homework_text=last_saved_homework.text,
            attachment_url=last_saved_homework.attachment_url,
            slot_string=format_relative_slot_string(wwdate, last_saved_homework.slot)
        )
    )

