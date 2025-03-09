from model import Lesson, Subject, Timetable, Weekday

fake = Timetable(timetable_dict={
    Weekday(0): {
        0: Lesson(subjects=[Subject('Алгебра')]),
        1: Lesson(subjects=[Subject('Английский язык'), Subject('ИКТ')]),
        2: Lesson(subjects=[Subject('Физика')])
    },
    Weekday(2): {
        0: Lesson(subjects=[Subject('Геометрия')]),
        2: Lesson(subjects=[Subject('Биология')])
    }
})

def test_parse_timtable():
    text = "пОнедельник: Алгебра, (Английский язык, ИКТ), Физика\nср: Геометрия, ОКНО, Биология"
    assert fake == Timetable.parse(text)