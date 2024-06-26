
def weekday_up(weekday: int, d: int=1, week: int=None):
    """Changes `weekday` for value `d` (can be positive or negative). If `week` exsist, changes it."""
    new_weekday = (weekday + d) % 7
    d_week = (weekday + d) // 7
    if week is None:
        return new_weekday
    return new_weekday, week + d_week



