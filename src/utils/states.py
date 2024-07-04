
from aiogram.fsm.state import StatesGroup, State


class ConfigureState(StatesGroup):
    edit_or_new_class_choosing = State()
    typing_class_name = State()
    choosing_days_of_study = State()
    changing_subjects_list = State()
    waiting_for_new_subject = State()
    waiting_for_removed_subject = State()
    choosing_timetable_way = State()
    waiting_for_day_length = State()
    making_timetable = State()
    ending_timetable = State()

class EditConfigureState(StatesGroup):
    choosing_value_to_edit = State()
    setting_new_classname = State()
    changing_subject_list = State()
    changing_admin_list = State()
    choosing_day_for_timetable_change = State()
