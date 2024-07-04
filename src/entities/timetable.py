
from .subject import Subject, EmptySubject
from storage.tables import LessonTable, SubjectTable

class Timetable:
    def __init__(self, subjects: list[Subject | EmptySubject]):
        self.lessons = (s for s in subjects)
    def __str__(self):
        return '\n'.join([f'{i+1}. {subject.name}' for i, subject in enumerate(self.subject)])
    def __index__(self, index: int):
        return self.lessons[index]
    def __iter__(self):
        return iter(self.lessons)
    def __len__(self):
        return len(self.lessons)
    @classmethod
    def from_table_lessons_list(cls, table_lessons_list: list[LessonTable]):
        ...