from model.subject import Subject
from logers import parse_loger
import Levenshtein as lev

def parse_subject(text: str) -> Subject:
    parse_loger.debug(f'Parsing Subject: {text}')
    return Subject(name=text.strip().capitalize() if len(text) > 4 else text.strip().upper())

def parse_subjects_from_text(text: str, avaible_subjects: list[Subject], candidates_amount: int=3) -> list[Subject]:
    """Returns list of 3 subjects"""
    to_return_amount = min(candidates_amount, len(avaible_subjects))
    words = _split_to_words(text)
    subject_names = [sj.name for sj in avaible_subjects if isinstance(sj, Subject)]
    dinstances = {}
    for word in words:
        for sj_name in subject_names:
            for sj_name_word in sj_name.split():
                dist = _dist_word_subject(word, sj_name_word)
                if (existed := dinstances.get(sj_name)) is not None:
                    dinstances[sj_name] = min(existed, dist)
                else:
                    dinstances[sj_name] = dist
    subjects_to_return = []
    while len(subjects_to_return) < to_return_amount:
        min_dist = float('inf')
        min_dist_sj = None
        for sj_name, dist in dinstances.items():
            if dist < min_dist:
                min_dist = dist
                min_dist_sj = sj_name
        subjects_to_return.append(min_dist_sj)
        del dinstances[min_dist_sj]
    return [Subject(sj_name) for sj_name in subjects_to_return]

def _dist_word_subject(word: str, subject_name: str):
    dist = lev.distance(word.lower(), subject_name.lower(), weights=(1, 1, len(word)))
    if len(subject_name) < 5 and dist > 1:
        return float('inf')
    return dist

def _split_to_words(text: str) -> list[str]:
    import re
    words = re.findall(r'[\w-]+', text)
    return words
