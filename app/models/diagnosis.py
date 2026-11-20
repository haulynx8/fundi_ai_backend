
from datetime import datetime, timezone

from sqlalchemy import (
    String,
    Text,
    ForeignKey,
    DateTime,
    JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        nullable=False,
        index=True
    )

    symptom: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    language: Mapped[str] = mapped_column(
        String(10),
        default="en",
        nullable=False
    )

    results: Mapped[list] = mapped_column(
        JSON,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    device = relationship(
        "Device",
        back_populates="diagnoses"
    )
