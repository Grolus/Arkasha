
from model import Lesson, Subject

lessons = [
    Lesson(subjects=[Subject('русский язык')]),
    Lesson(subjects=[Subject('ОБЖ')]),
    Lesson(subjects=[Subject('Английский язык'), Subject('ИКТ')])
]

def test_parse_lesson():
    cases = [
        ('русский язык', lessons[0]),
        ('ОБЖ', lessons[1]),
        ('(Английский язык, ИКТ)', lessons[2])
    ]
    for text, result in cases:
        assert result == Lesson.parse(text)

