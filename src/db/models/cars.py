from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class OriginCountryEnum(PyEnum):
    US = "USA"
    JP = "Japan"
    EU = "Europe"
    KR = "Korea"
    CN = "China"
    RU = "Russia"
    UA = "Ukraine"


class Cars(Base):
    __tablename__ = "cars"

    id: Mapped[int] = mapped_column(primary_key=True)
    price: Mapped[int]
    fueltype: Mapped[str]
    millage: Mapped[str]
    location: Mapped[str]
    gearbox: Mapped[str]
    ua_number: Mapped[str | None]
    vin: Mapped[str | None]
    origin_country = mapped_column(Enum(OriginCountryEnum, values_callable=lambda x: [e.value for e in x]))
    had_accident: Mapped[bool]
    is_sold: Mapped[bool]
    generation: Mapped[str]
    engine: Mapped[str]
    link: Mapped[str]
    brand: Mapped[str]
    model: Mapped[str]
    year: Mapped[int]
    description: Mapped[str | None]
    creation_datetime: Mapped[datetime]
    update_datetime: Mapped[datetime]

    images = relationship("CarImages", back_populates="car")
