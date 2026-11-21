from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Shop(Base):
    __tablename__ = "shops"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True
    )

    location: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )

    phone: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    services: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )

    rating: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        default=None
    )

    price_range: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default=None
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    bookings = relationship(
        "Booking",
        back_populates="shop",
        cascade="all, delete-orphan"
    )
