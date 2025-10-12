from database.dao.dao import HomeworkDAO
from database.database import connection
from asyncio import run


@connection
async def test(session):
    
    for homework in await HomeworkDAO.get_all_homeworks_for_day(session, 2, 0, 39, 2025):
        if homework:
            print(f'{homework.lesson.position}.')
    

print(run(test()))

