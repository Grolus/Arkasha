
from exceptions import SubjectError, DecodingSubjectError
from logers import subject as loger

from abc import abstractmethod

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
        loger.debug(f'Decoding subject with code {coded_subject!r}...')
        if not coded_subject.isnumeric() or 0 > int(coded_subject) > len(Subject._instances):
            if int(coded_subject) == EmptySubject.code:
                return EmptySubject.decode(coded_subject)
            raise DecodingSubjectError('Can`t decode subject "%s"' % coded_subject)
        subject = Subject._instances[int(coded_subject)]
        loger.debug(f'It is {subject}')
        return subject



