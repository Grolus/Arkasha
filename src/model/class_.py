from pydantic import BaseModel
from .timetable import Timetable
from .subject import Subject

class Class(BaseModel):
    name: str
    creator_username: str
    timetable: Timetable
    
    __subjects: list[Subject] = None
    def get_subjects_list(self):
        if self.__subjects:
            return self.__subjects
        self.__subjects = []
        for day in self.timetable.timetable_dict.values():
            for lesson in day:
                if lesson:
                    self.__subjects.extend([s for s in lesson.subjects])
        self.__subjects = list(set(self.__subjects))
        return self.__subjects
                
        