from collections.abc import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import CarImages, Cars


async def get_cars_by_ids(session: AsyncSession, ids: Iterable[int], inverse=False) -> Sequence[Cars]:
    if inverse:
        stmt = select(Cars).filter(Cars.id.not_in(ids))
    else:
        stmt = select(Cars).filter(Cars.id.in_(ids))

    result = await session.execute(stmt)
    return result.scalars().all()


async def get_car_images_by_car_ids(session: AsyncSession, car_ids: Iterable[int]) -> Sequence[CarImages]:
    stmt = select(CarImages).filter(CarImages.car_id.in_(car_ids))
    result = await session.execute(stmt)

    return result.scalars().all()
