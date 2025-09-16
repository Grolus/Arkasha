
from ..database import connection, Base

class BaseDAO:
    model = ...
    
    @classmethod
    async def insert(cls, session, **values_kwargs) -> int:
        instance = cls.model(**values_kwargs)
        session.add(instance)
        await session.commit()
        return instance.id
        
    @classmethod
    async def insert_many(cls, session, values_dicts: list[dict[str: ...]]):
        instances = [cls.model(**data) for data in values_dicts]
        session.add_all(instances)
        await session.commit()
        # что возвращать?
        
        
