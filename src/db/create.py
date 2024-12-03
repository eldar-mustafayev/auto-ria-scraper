import asyncio

from .models.base import Base
from .session import engine


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


asyncio.run(drop_tables())
asyncio.run(create_tables())
