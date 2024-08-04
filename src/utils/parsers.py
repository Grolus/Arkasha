
from entities import Subject, EmptySubject
from.weekday import Weekday
import Levenshtein as lev

def parse_one_subject(word: str, subjects: list[Subject]):
    if EmptySubject() in subjects:
        subjects.remove(EmptySubject())
    min_dist = float('inf')
    min_dist_subject = None
    for sj in subjects:
        dist = _dist_word_subject(word, sj.name)
        if dist < min_dist:
            min_dist = dist
            min_dist_subject = sj
    return min_dist_subject

def parse_subjects(text: str, subjects: list[Subject]) -> list[Subject]:
    """Returns list of 3 subjects"""
    to_return_amount = min(3, len(subjects))
    words = _split_to_words(text)
    subject_names = [sj.name for sj in subjects if isinstance(sj, Subject)]
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

def parse_weekdays(text: str) -> list[Weekday]:
    text = text.lower().replace(' ', '')
    parts = text.split(',')
    weekdays = []
    for part in parts:
        if '-' in part:
            wd_range = _weekday_range(*map(_word_to_weekday, part.split('-')))
            weekdays.extend([wd for wd in wd_range if not wd in weekdays])
        else:
            wd = _word_to_weekday(part)
            if not wd in weekdays:
                weekdays.append(wd)
    weekdays.sort(key=lambda x: int(x))
    return weekdays

def _dist_word_subject(word: str, subject_name: str):
    dist = lev.distance(word.lower(), subject_name.lower(), weights=(1, 1, len(word)))
    if len(subject_name) < 5 and dist > 1:
        return float('inf')
    #print(f'{word} <> {subject_name} {dist}')
    return dist

def _word_to_weekday(word: str):
    for wd in [Weekday(i) for i in range(7)]:
        if word in wd._all_variants():
            return wd
    raise ValueError(f'word_to_weekday: word {word} not parsable as weekday')

def _weekday_range(from_: Weekday, to: Weekday):
    if int(from_) > int(to):
        from_, to = to, from_
    if from_ == to:
        return from_
    return list(map(Weekday, range(int(from_), int(to)))) + [to]

def _split_to_words(text: str) -> list[str]:
    raw_words = text.split()
    words = []
    for raw_word in raw_words:
        if raw_word.isalpha():
            words.append(raw_word)
    return words
