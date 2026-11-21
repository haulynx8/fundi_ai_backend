from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ShopBase(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=150,
        examples=["Luthuli Tech Hub & Phone Care"],
    )
    location: str = Field(
        ...,
        min_length=2,
        max_length=255,
        examples=["Luthuli Avenue, Nairobi CBD"],
    )
    phone: str = Field(
        ...,
        min_length=7,
        max_length=50,
        examples=["+254712345001"],
    )
    services: list[str] = Field(
        default_factory=list,
        examples=[["Phone screen replacement", "Battery replacement", "Charging port repair"]],
    )
    rating: float | None = Field(
        default=None,
        ge=1.0,
        le=5.0,
        examples=[4.8],
    )
    price_range: str | None = Field(
        default=None,
        max_length=50,
        examples=["KSh 1,500 - 6,000"],
    )


class ShopCreate(ShopBase):
    pass


class ShopResponse(ShopBase):
    id: int
    phone_url: str = Field(default="", examples=["tel:+254712345001"])
    booking_url: str = Field(default="", examples=["tel:+254712345001"])
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShopListResponse(BaseModel):
    success: bool = True
    count: int
    shops: list[ShopResponse]
