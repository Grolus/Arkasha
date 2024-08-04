

from storage.tables import *
from storage.connection import DBConection
from config import DATABASE
from entities import Subject, Timetable, Class
from entities.subject import DEFAULT_SUBJECTS
from utils import Weekday

import logging
import sys
from pprint import pprint



logging.basicConfig(stream=sys.stdout, level=0)
db = DBConection(DATABASE['HOST'], DATABASE['PASSWORD'], DATABASE['DATABASE'], DATABASE['PORT'], DATABASE['USER'])
"""
cfg = Bot_configuration('grolus', '9a')


cfg._subjects_list = DEFAULT_SUBJECTS
cfg._is_5_days_studytype = True
cfg._last_lerning_weekday = 4
cfg._lessons_in_day = 3
cfg._weekday_cursor = Weekday(4)
cfg._all_timetable = [
    Timetable([cfg._subjects_list[(i+j)%cfg._lessons_in_day] for j in range(cfg._lessons_in_day)])
    for i in range(int(cfg._last_lerning_weekday))
]
print(cfg._all_timetable)


ClassTable.save_new_configuration(cfg)
"""
# test bot configuration

"""
res = db.query("SELECT * FROM class WHERE classname='9a'")
print(ClassTable.from_selected(res[0]))
"""
# test BaseTable.from_selected()

AdministratorTable('asfd').get_classes()


