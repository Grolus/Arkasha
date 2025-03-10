
def split_with_ignoring(
    text_to_split: str, 
    separator: str = " ", 
    area_to_ignore_borders: str = '()'
):
    """
    Разделяет текст на части по односимвольному разделителю, но может игнорировать части, ограниченные опредёлнными символами\n
    :param text_to_split: Строка для разделения
    :param separator: Разделитель (только единичный символ)
    :param area_to_ignore_borders: Символы, ограничивающие область для игнорирования разделителей. 
        Параметр должен содержать четное количество символов.
        На примере скобок: `"()[]{}<>"` (для игнорирования выражений в скобках при разделении)

    For example:
    
        parts = split_with_ignoring(
            "1, 2, (3, 4, 5), 6, [7]",
            ",",
            "()[]"
        )
        assert parts == ["1", "2", "(3, 4, 5)", "6", "[7]"]
    """
    result_parts = []
    ignore_level = 0
    cur_part = ''
    for ch in text_to_split:
        cur_part += ch
        # print(f'{result_parts=}, {cur_part=}')
        for left_border in area_to_ignore_borders[::2]:
            if ch == left_border:
                ignore_level += 1
                break

        for right_border in area_to_ignore_borders[1::2]:
            if ch == right_border:
                ignore_level -= 1
                break

        if ch == separator and ignore_level == 0:
            result_parts.append(cur_part[:-1] if len(cur_part) > 1 else '')
            cur_part = ''
    result_parts.append(cur_part)
    return result_parts

def strip_of_brackets(text_to_strip: str, brackets: str='()'):
    if text_to_strip.startswith(brackets[0]):
        return strip_of_brackets(text_to_strip[1:])
    if text_to_strip.endswith(brackets[1]):
        return strip_of_brackets(text_to_strip[:-1])
    return text_to_strip

