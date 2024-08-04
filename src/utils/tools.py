import datetime

def allocate_values_to_nested_list(values: list, length_of_nested_list: int):
    new_list = []
    for i, value in enumerate(values):
        if i % length_of_nested_list == 0:
            new_list.append([])
        new_list[-1].append(value)
    return new_list

def get_now_week(dt: datetime.datetime) -> int:
    return (
        datetime.datetime(dt.year, 1, 1).weekday() + 
        dt.timetuple().tm_yday
    ) // 7 - 1

