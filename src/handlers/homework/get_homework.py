
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from ..middlewares import GetClassMiddleware
from entities import Class, Subject, Homework, PagedList
from utils import allocate_values_to_nested_list, Weekday
from utils.states import GetHomeworkState
from utils.slot import slot_to_callback, slot_to_string, callback_to_slot




router = Router(name='get_homework')
router.message.middleware(GetClassMiddleware())
router.callback_query.middleware(GetClassMiddleware())


class PagedSubjectList(PagedList):
    def __init__(self, all_subjects: list[list[Subject]], page_size: int):
        super().__init__(all_subjects, page_size)
    def get_current_page_as_keyboard(self, callback_prefix: str) -> InlineKeyboardMarkup:
        page = self.current_page()
        
        page_changing_buttons = []
        if not self.is_page_first():
            page_changing_buttons.append(
                InlineKeyboardButton(text='⬅Назад', callback_data=f'{callback_prefix}_pagedown')
            )
        if not self.is_page_last():
            page_changing_buttons.append(
                InlineKeyboardButton(text='Вперёд➡', callback_data=f'{callback_prefix}_pageup')
            )

        return InlineKeyboardMarkup(inline_keyboard=allocate_values_to_nested_list([
            InlineKeyboardButton(text=subject.name, callback_data=f'{callback_prefix}_{subject.encode()}')
            for subject in page
        ], 2) + [page_changing_buttons])


@router.message(Command('get_homework'))
async def get_homework_start(message: Message, state: FSMContext, class_: Class, weekday: Weekday):
    paged_list = PagedSubjectList(class_.get_subject_list_for_paged_list(weekday), class_.get_lessons_amount())
    current_page_kb = paged_list.get_current_page_as_keyboard('choosedsubjectgethw')
    await state.set_data({'paged_list': paged_list})
    await state.set_state(GetHomeworkState.choosing_subject)
    return await message.reply(
        '<b>Выберте предмет, по которому хотите получить дз</b>',
        reply_markup=current_page_kb
    )

@router.callback_query(
    GetHomeworkState.choosing_subject, F.data.in_(['choosedsubjectgethw_pageup', 'choosedsubjectgethw_pagedown'])
    )
async def page_changing(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split('_')[1]
    paged_list: PagedSubjectList = (await state.get_data())['paged_list']
    match action:
        case 'pageup':
            paged_list.page_up()
        case 'pagedown':
            paged_list.page_down()
    current_page_kb = paged_list.get_current_page_as_keyboard('choosedsubjectgethw')
    return await callback.message.edit_text(
        '<b>Выберте предмет, по которому хотите получить дз</b>',
        reply_markup=current_page_kb
    )

@router.callback_query(
        GetHomeworkState.choosing_subject, 
        F.data.startswith('choosedsubjectgethw_'),              
        F.data.func(lambda x: x.split('_')[1].isnumeric())  # second part of callback_data is numeric
    )
async def choosed_subject_handler(callback: CallbackQuery, state: FSMContext, class_: Class, weekday: Weekday, week: int):
    subject = Subject.decode(callback.data.split('_')[1])
    homeworks = Homework.get_awaible(subject, class_, weekday, week)
    if not homeworks:
        await state.clear()
        last_saved = Homework.get_last_for_subject(subject, class_)
        if last_saved:
            await state.set_data({'last_saved_homework': last_saved})
            return await callback.message.edit_text(
                f'Актуального задания по предмету {subject.name} не сохранено. '
                f'Показать последнее сохранённое? ({slot_to_string(last_saved.slot(week))})',
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text='Показать', callback_data='getlasthomework_1'),
                    InlineKeyboardButton(text='Нет', callback_data='getlasthomework_0')
                ]]))
        else:
            return await callback.message.edit_text(
                f'Актуального задания по предмету {subject.name} не сохранено.'
            )
    slot_to_homework = {hw.slot(week) : hw for hw in homeworks}
    slots = list(slot_to_homework.keys())
    await state.set_data({'slot_to_homework': slot_to_homework})
    await state.set_state(GetHomeworkState.choosing_slot)
    return await callback.message.edit_text(
        '<b>Выберите день</b>',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=slot_to_string(slot), callback_data=slot_to_callback(slot, 'choosedslotgethw'))]
            for slot in slots
        ])
    )
    
@router.callback_query(GetHomeworkState.choosing_slot, F.data.startswith('choosedslotgethw_'))
async def send_homework_handler(callback: CallbackQuery, state: FSMContext, week: int):
    slot = callback_to_slot(callback.data)
    slot_to_homework = (await state.get_data())['slot_to_homework']
    choosed_homework = slot_to_homework[slot]
    await state.clear()
    return await callback.message.edit_text(choosed_homework.get_string(week))

@router.callback_query(F.data.startswith('getlasthomework'))
async def get_last_homework(callback: CallbackQuery, state: FSMContext, week: int):
    if callback.data.split('_')[1] == '0':
        return await callback.message.delete()
    last_saved_homework = (await state.get_data())['last_saved_homework']
    await state.clear()
    return await callback.message.edit_text('❗ <b>Старое</b> ❗\n' + last_saved_homework.get_string(week))

