
from ..database import connection, Base
from typing import Type
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class BaseDAO:
    model: Type[Base] = ...
    
    @classmethod
    async def insert(cls, session: AsyncSession, **values_kwargs) -> int:
        instance = cls.model(**values_kwargs)
        session.add(instance)
        await session.flush()
        return instance.id
        
    @classmethod
    async def insert_many(cls, session, values_dicts: list[dict[str: ...]]):
        instances = [cls.model(**data) for data in values_dicts]
        session.add_all(instances)
        # что возвращать?
        
    @classmethod
    async def get_by_fields(cls, session: AsyncSession, *values_tuples):
        query = select(cls.model).where(*[i == j for i, j in values_tuples])
        # print(query)
        result = await session.execute(query)
        #print(result.all())
        return result.scalars()
        