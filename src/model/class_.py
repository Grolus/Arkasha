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
                    self.__subjects.extend([s.subject for s in lesson])
        self.__subjects = list(set(self.__subjects))
        return self.__subjects
    
    def get_if_subject_grouped(self, subject: Subject) -> bool:
        for day in self.timetable.timetable_dict.values():
            for lessons in day:
                if len(lessons) > 1 and subject in [l.subject for l in lessons]:
                    print(f'{subject.name} is grouped')
                    return True
        print(f'{subject.name} is not grouped')
        return False
                
        