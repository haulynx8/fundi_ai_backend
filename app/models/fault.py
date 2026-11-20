
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    ForeignKey,
    DateTime,
    CheckConstraint,
    JSON,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Fault(Base):
    __tablename__ = "faults"

    __table_args__ = (
        CheckConstraint(
            "cost_min <= cost_max",
            name="check_fault_cost_range",
        ),
        CheckConstraint(
            "risk_level IN ('red', 'yellow', 'green')",
            name="check_fault_risk_level",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id"),
        nullable=False,
        index=True,
    )

    fault_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    keywords_en: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    keywords_sw: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    symptoms: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    diagnostic_questions: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    fix_steps: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    cost_min: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    cost_max: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    risk_level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    verification_status: Mapped[str] = mapped_column(
        String(20),
        default="unverified",
        nullable=False,
    )

    source: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    device = relationship("Device", back_populates="faults")
