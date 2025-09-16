
from sqlalchemy import Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncAttrs
from config.settings import settings


engine = create_async_engine(url=settings.get_db_url())

AsyncSessionMaker = async_sessionmaker(engine, expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True 
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    
def connection(func):
    async def wrapper(*args, **kwargs):
        async with AsyncSessionMaker() as session:
            try:
                return await func(*args, session=session, **kwargs)
            except Exception as ex:
                await session.rollback()
                raise ex
            finally:
                await session.close()
    return wrapper


    