
from homework import Subject, DEFAULT_SUBJECTS
from exceptions import SubjectListChangingError, ConfigureError

 
class Bot_configuration():

    _username: str
    _classname: str
    _subjects_list: list[Subject]
    _is_5_days_studytype: bool
    __instances: dict[str: Subject] = {}
    def __new__(cls, username: str):
        if instance := cls.__instances.get(username):
            return instance
        instance = super().__new__(cls)
        cls.__instances[username] = instance
        instance._username = username
        instance._subjects_list = DEFAULT_SUBJECTS.copy()
        return instance

    def classname(self, classname: str):
        self._classname = classname

    def new_subject(self, subject: Subject):
        if subject in self._subjects_list:
            raise SubjectListChangingError(f'Subject "{subject}" already exists in Bot_configuration({self._username})._subjects_list')
        self._subjects_list.append(subject)
    
    def remove_subject(self, subject: Subject):
        if not subject in self._subjects_list:
            raise SubjectListChangingError(f'Bot_configuration.delete_subject(): subject "{subject}" not in subject list!')
        self._subjects_list.remove(subject)
    
    def is_5_days_studytype(self, is_5_days: bool):
        """`True` if studytype - 5 days, else (6 days) - `False`"""
        self._is_5_days_studytype = is_5_days
