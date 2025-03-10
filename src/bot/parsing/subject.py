from model.subject import Subject
from logers import parse_loger


def parse_subject(text: str) -> Subject:
    parse_loger.debug(f'Parsing Subject: {text}')
    return Subject(name=text.strip())
