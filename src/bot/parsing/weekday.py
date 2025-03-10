
from model import Weekday
from exceptions import ParsingError
from logers import parse_loger

def parse_weekday(text: str) -> Weekday:
    parse_loger.debug(f"Parsing Weekday: {text}")
    for wd_num in range(7):
        wd = Weekday(wd_num)
        for wd_string in wd._all_variants():
            # print(f"comparing {text} with {wd_string}: {text.lower() == wd_string}")
            if text.lower() == wd_string:
                return wd
    raise ParsingError(text, Weekday)