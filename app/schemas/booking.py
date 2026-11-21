import re
from datetime import date as dt_date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class BookingCreate(BaseModel):
    user_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Juma Mwangi"],
    )
    phone: str = Field(
        ...,
        min_length=9,
        max_length=50,
        examples=["+254712345678"],
    )
    shop_id: int = Field(
        ...,
        gt=0,
        examples=[1],
    )
    date: dt_date = Field(
        ...,
        examples=["2026-11-25"],
    )
    device_category: str | None = Field(
        default=None,
        max_length=50,
        examples=["phone"],
    )
    notes: str | None = Field(
        default=None,
        max_length=1000,
        examples=["Screen replacement needed after accidental drop"],
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        clean = re.sub(r"[\s\-()]", "", v)
        if not re.match(r"^(\+?254|0)[17]\d{8}$", clean) and len(clean) < 9:
            raise ValueError(
                "Invalid phone number format. Please provide a valid phone number (e.g. +254712345678 or 0712345678)"
            )
        return clean


class BookingStatusUpdate(BaseModel):
    status: Literal["pending", "confirmed", "in_progress", "completed", "cancelled"]


class BookingResponse(BaseModel):
    id: int
    user_name: str
    phone: str
    shop_id: int
    date: dt_date
    status: str
    device_category: str | None = None
    notes: str | None = None
    created_at: datetime
    shop_name: str | None = None
    shop_location: str | None = None

    model_config = ConfigDict(from_attributes=True)


class BookingListResponse(BaseModel):
    success: bool = True
    count: int
    bookings: list[BookingResponse]
