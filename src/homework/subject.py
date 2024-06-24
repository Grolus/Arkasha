
from exceptions import SubjectError, DecodingSubjectError

class Subject():
    _instances = []
    def __new__(cls, name):
        for instance in cls._instances:
            if name == instance.name:
                return instance
        instance = super().__new__(cls)
        instance.name = name
        cls._instances.append(instance)
        return instance
    def __str__(self):
        return self.name
    def encode(self) -> str:
        return str(Subject._instances.index(self))
    @staticmethod
    def decode(coded_subject: str):
        if not coded_subject.isnumeric() or 0 > int(coded_subject) > len(Subject._instances):
            raise DecodingSubjectError('Can`t decode subject "%s"' % coded_subject)
        return Subject._instances[int(coded_subject)]



