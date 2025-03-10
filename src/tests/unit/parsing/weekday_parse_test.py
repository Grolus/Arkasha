
from model import Weekday
from bot.parsing.weekday import parse_weekday

def test_parse_weekday():
    cases = [
        ('Понедельник', Weekday(0)),
        ('пн', Weekday(0)),
        ('среду', Weekday(2)),
        ('воскресение', Weekday(6)),
        ('ЧТ', Weekday(3)),
        ('пЯтницей', Weekday(4)),
        ('Tuesday', Weekday(1))
    ]
    for string, wd in cases:
        assert wd == parse_weekday(string)
