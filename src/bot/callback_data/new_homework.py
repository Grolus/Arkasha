from aiogram.filters.callback_data import CallbackData
from typing_extensions import Self, Literal
from model import Subject, Slot, WWDate, Weekday

from config.constants import DEFAULT_CALLBACK_DATA_SEPARATOR



class ChoosedSubjectCallback(CallbackData, prefix='subjectchoosedhwset', sep=DEFAULT_CALLBACK_DATA_SEPARATOR):
    subject_id: int
    
    __SUBJECTS = {}

    @classmethod
    def from_subject(cls, subject: Subject) -> Self:
        subject_id = hash(subject.name)
        cls.__SUBJECTS[subject_id] = subject
        return cls(subject_id=subject_id)
    
    def get_subject(self) -> Subject:
        return self.__class__.__SUBJECTS.pop(self.subject_id)



class PagingSubjectListCallback(CallbackData, prefix='subjectlistpage'):
    direction: Literal['up', 'down']


class CancelCallback(CallbackData, prefix='homeworksetcancel', sep=DEFAULT_CALLBACK_DATA_SEPARATOR):
    ...

class CheckOtherSubjectsCallback(CallbackData, prefix='homeworksetcheckothersubjects', sep=DEFAULT_CALLBACK_DATA_SEPARATOR):
    ...


class ChoosedSlotCallback(CallbackData, prefix='slotchoosedhwset', sep=DEFAULT_CALLBACK_DATA_SEPARATOR):
    year: int
    week: int
    weekday_number: int
    position: int

    @classmethod
    def from_slot(cls, slot: Slot) -> Self:
        return cls(
            year=int(slot.wwdate.year),
            week=int(slot.wwdate.week),
            weekday_number=int(slot.wwdate.weekday),
            position=slot.position
        )
    
    def get_slot(self) -> Slot:
        return Slot(
            wwdate=WWDate(
                weekday=Weekday(
                    weekday_number=self.weekday_number
                ),
                week=self.week,
                year=self.year
            ),
            position=self.position
        )

class ShowOtherSlotCallback(CallbackData, prefix='chooseanotherslothwset', sep=DEFAULT_CALLBACK_DATA_SEPARATOR):
    ...

class ChoosedGroupCallback(CallbackData, prefix='hwsetgroup', sep=DEFAULT_CALLBACK_DATA_SEPARATOR):
    group: int
