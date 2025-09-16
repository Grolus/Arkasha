from database.dao.add_methods import insert_class
from asyncio import run

class_id = run(insert_class('testclassname', 'grolus'))

print(class_id, '- id нового класса в бд')