from enum import Enum as PyEnum

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ImageSourceEnum(PyEnum):
    AUTO_RIA = "auto-ria"
    AUCTION = "auction"


class CarImages(Base):
    __tablename__ = "car_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"), index=True)
    source = mapped_column(Enum(ImageSourceEnum, values_callable=lambda x: [e.value for e in x]))
    image_url: Mapped[str]

    car = relationship("Cars", back_populates="images")
