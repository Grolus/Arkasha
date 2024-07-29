
from exceptions import SubjectError, DecodingSubjectError

from abc import abstractmethod

__all__ = (
    'Subject',
    'EmptySubject',
    'DEFAULT_SUBJECTS'
)


class BaseSubject:
    name: str
    def __str__(self):
        return self.name
    @abstractmethod
    def encode(self):
        ...
    @staticmethod
    @abstractmethod
    def decode(coded_subject: str):
        ...
    
    @classmethod
    def from_table_value(cls, table_subject):
        name = table_subject.values.subjectname
        return cls(name)


class EmptySubject(BaseSubject):
    name = 'Ничего'
    code = -1

    def encode(self):
        return EmptySubject.code
    @staticmethod
    def decode(coded_subject: str):
        return EmptySubject()

class Subject(BaseSubject):
    _instances = []
    def __new__(cls, name):
        for instance in cls._instances:
            if name == instance.name:
                return instance
        instance = super().__new__(cls)
        instance.name = name
        cls._instances.append(instance)
        return instance
    def encode(self) -> str:
        return str(Subject._instances.index(self))
    @staticmethod
    def decode(coded_subject: str):
        if not coded_subject.isnumeric() or 0 > int(coded_subject) > len(Subject._instances):
            if int(coded_subject) == EmptySubject.code:
                return EmptySubject.decode(coded_subject)
            raise DecodingSubjectError('Can`t decode subject "%s"' % coded_subject)
        subject = Subject._instances[int(coded_subject)]
        return subject


DEFAULT_SUBJECTS_NAMES = [
    'Русский язык', 'Математика', 'Физика', 'Алгебра', 
    'Геометрия', 'Физическая культура', 'История', 'ОБЖ', 'Обществознание']
DEFAULT_SUBJECTS = [
    Subject(name) for name in DEFAULT_SUBJECTS_NAMES
]

