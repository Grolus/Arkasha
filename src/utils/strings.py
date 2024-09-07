
from entities import Subject, EmptySubject
from .weekday import Weekday

def subject_list_to_str(subject_list: list[Subject | None | list[Subject]], *,
                         html_tags: str='', separator: str='\n', 
                         numbered: bool=False, decorate_numbers: bool=False, start_numbers: int=1,
                         subject_cursor: int=None):
    """Converts list of subjects to string (subjects names separated by '\\n')\n
    :param subject_list: list of subjects to print (If subject_list[i] is None, '...' will be printed)
    :param html_tags: (Optional) html-tags to decorate final string (e. g. `tags='bu'` => `'<b><u>{subjects_to_print}</u></b>)'`"""
    
    subjects_to_print = separator.join(
        [(f'{start_numbers+i}. ' if numbered and not decorate_numbers else '') + format_html_tags(
            ('bu' if subject_cursor == i else html_tags), 
            (f'{start_numbers+i}. ' if numbered and decorate_numbers else '') + 
                (subject.name if isinstance(subject, (Subject, EmptySubject)) 
                    else ' | '.join([sj.name for sj in subject]))
            )
         for i, subject in enumerate(subject_list)]
        )
    return subjects_to_print

def format_answer_timtable_making(weekday: Weekday, timetable: list[Subject | list[Subject]], posttext: str='', cursor: int=None) -> str:
    answer = f'Составляем расписание на <b><u>{weekday.genetive}</u></b>. \n\n' + \
        subject_list_to_str(timetable, html_tags='i', numbered=True, subject_cursor=cursor) + '\n\n' + \
        (posttext or f'Нажимайте на предметы в нужном порядке или на "{EmptySubject.name}", если в этот момент нет урока.')
    return answer

def format_html_tags(html_tags: str, text: str) -> str:
    """Decorating html-tags to right format (e. g. `html_tags='bu'` => `'<b><u>{text}</u></b>)'`"""
    begin = ''.join([f'<{tag}>' for tag in html_tags])
    end = ''.join([f'</{tag}>' for tag in html_tags[::-1]])
    return begin + text + end

def format_answer_changed_subject_list(pretext: str, subjects_list: list[Subject]) -> str:
    '''Compiling answer via sample:\n "`{pretext}`\n\n `subject1` \n`subject2` \n ...\n\nХотите добавить/убрать предмет?"'''
    result = pretext + '\n\n' + subject_list_to_str(subjects_list, html_tags='b') + '\n\nХотите добавить/убрать предмет?'
    return result

def format_answer_start_configure(existing_classes_amount: int):
    return (f'У вас уже есть класс{"ы" if existing_classes_amount > 1 else ""}. ' + \
    f'Хотите изменить {"их" if existing_classes_amount > 1 else "его"} или создать новый?') if existing_classes_amount else \
    f'У вас нет уже созданных классов. Хотите создать новый?'

def slot_to_string(slot: tuple[Weekday, int, bool]):
    weekday, position, is_for_next_week = slot
    return weekday.name.title() + (" следующей недели" if is_for_next_week else "") + f", {position} урок"

def slot_to_callback(slot: tuple[Weekday, int, bool], callback_prefix: str='choosedslot'):
    return f'{callback_prefix}_{int(slot[0])}_{slot[1]}_{int(slot[2])}'

def callback_to_slot(callback_data: str) -> tuple[Weekday, int, bool]:
    _, weekday, pos, is_next_week = callback_data.split('_')
    return Weekday(int(weekday)), int(pos), bool(int(is_next_week))




