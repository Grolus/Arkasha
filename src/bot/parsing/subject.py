from model.subject import Subject
from logers import parse_loger

import Levenshtein as lev

def _flip_dict(d: dict) -> dict:
    return {v: k for k, v in d.items()}

def parse_subject(text: str) -> Subject:
    parse_loger.debug(f'Parsing Subject: {text}')
    return Subject(name=text.strip().capitalize() if len(text) > 4 else text.strip().upper())

def get_most_similar_subjects_with_distantions(text: str, avaible_subjects: list[Subject], amount: int) -> dict[int: Subject]:
    to_return_amount = min(amount, len(avaible_subjects))
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
    result_dict = {}
    while len(result_dict.keys()) < to_return_amount:
        min_dist = float('inf')
        min_dist_sj = None
        for sj_name, dist in dinstances.items():
            if dist < min_dist:
                min_dist = dist
                min_dist_sj = sj_name
        result_dict[min_dist] = Subject(min_dist_sj)
        del dinstances[min_dist_sj]
    return result_dict


def parse_subjects_from_text(text: str, avaible_subjects: list[Subject], candidates_amount: int=3) -> list[Subject]:
    """Returns list of 3 subjects"""
    
    subjects_with_distantions = get_most_similar_subjects_with_distantions(
        text, avaible_subjects, candidates_amount
    )
    return [
        subjects_with_distantions[k] 
        for k in sorted(subjects_with_distantions.keys())
    ]
    

def _dist_word_subject(word: str, subject_name: str):
    dist = lev.distance(word.lower(), subject_name.lower(), weights=(1, 1, len(word)))
    if len(subject_name) < 5 and dist > 1:
        return float('inf')
    return dist

def _split_to_words(text: str) -> list[str]:
    import re
    words = re.findall(r'[\w-]+', text)
    return words
