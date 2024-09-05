
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
    def __hash__(self) -> int:
        return int(self.encode())
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} object {self.name!r}>'
    @abstractmethod
    def encode(self) -> str:
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
    __instance = None
    def __new__(cls):
        if cls.__instance:
            return cls.__instance
        instance = super().__new__(cls)
        cls.__instance = instance
        return instance
    def encode(self):
        return str(EmptySubject.code)
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
    def get_groups(self, class_):
        return class_.get_subject_groups(self)


DEFAULT_SUBJECTS_NAMES = [
    'Русский язык', 'Математика', 'Физика', 'Алгебра', 
    'Геометрия', 'Физкультура', 'История', 'ОБЖ', 'Обществознание']
DEFAULT_SUBJECTS = [
    Subject(name) for name in DEFAULT_SUBJECTS_NAMES
]

