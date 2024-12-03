from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.settings import settings

# execution_options = {"isolation_level": "SERIALIZABLE"}

engine = create_async_engine(settings.ASYNC_SQLITE_URL)
LocalAsyncSession = async_sessionmaker(engine, expire_on_commit=False)
