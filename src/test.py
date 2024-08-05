
from parsers import parse_subjects, _dist_word_subject
from entities.subject import DEFAULT_SUBJECTS, EmptySubject, Subject
from pprint import pprint

test_case = {
    'задание по обж - учить теорию, принести тетрадь': Subject('ОБЖ'),
    'по русскому ничего интересного, параграф 19 упр. 88': Subject('Русский язык'),
    'номера 123 123 1232453 по алгебре': Subject('Алгебра'),
    'по физре ничего': Subject('Физкультура'),
    'решать задачи из сборник 123 52 1235123 физика': Subject('Физика'),
    'по биологии узнать историю возникновения физических дефектов': Subject('Биология')
}

for arg, res in test_case.items():
    result = parse_subjects(arg, DEFAULT_SUBJECTS + [EmptySubject(), Subject('Биология')])
    print(f'{"+" if res in result else "-"}{"+" if result[0] == res else ""} Test {res.name!r} {arg!r}: {result}')

_dist_word_subject('русскому', 'русский')