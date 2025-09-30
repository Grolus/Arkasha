from pydantic import BaseModel

from .lesson import Lesson
from .weekday import Weekday, Slot, WWDate
from .subject import Subject
from enums import GroupNumberEnum

class Timetable(BaseModel):
    timetable_dict: dict[Weekday, list[list[Lesson]]]
    
    def get_relative_slots_for_subject(
        self, 
        subject: Subject, 
        group: GroupNumberEnum, 
        now_wwdate: WWDate
    ) -> list[Slot]:
        slots = []
        sorted_weekday_keys = list(sorted(self.timetable_dict.keys()))
        now_weekday = now_wwdate.weekday
        for i, weekday in enumerate(sorted_weekday_keys):
            if weekday >= now_weekday:
                start_index = i
                break
        else:
            start_index = 0
        
        sorted_weekday_keys = sorted_weekday_keys[start_index:] + sorted_weekday_keys[:start_index]
        group_index = 0 if group == GroupNumberEnum.FIRST else 1 if group == GroupNumberEnum.SECOND else None
        for weekday in sorted_weekday_keys:
            for position, lessons in enumerate(self.timetable_dict[weekday]):
                if len(lessons) == 1:
                    if lessons[0].subject == subject:
                        slots.append(Slot(
                            wwdate=WWDate(weekday=weekday, week=now_wwdate.week + (weekday <= now_weekday), year=now_wwdate.year),
                            position=position
                        ))
                elif not group == GroupNumberEnum.NOT_GROUPED:
                    if lessons[group_index].subject == subject:
                        slots.append(Slot(
                            wwdate=WWDate(weekday=weekday, week=now_wwdate.week + (weekday <= now_weekday), year=now_wwdate.year),
                            position=position
                        ))
        slots.sort(key=lambda s: s.wwdate.year * 365 + s.wwdate.week * 7 + int(s.wwdate.weekday))
        return slots
        
    def get_slots_for_subject(self, subject: Subject, group_number_to_find: int) -> list[(Weekday, int)]: 
        slots = []
        for weekday, timetable in self.timetables.items():
            for position, group_number in timetable.find_positions_of_subject(subject):
                if position != -1 and group_number == group_number_to_find:
                    slots.append((weekday, position))
        slots.sort(lambda x: x[0] * 100 + x[1])
        return slots
