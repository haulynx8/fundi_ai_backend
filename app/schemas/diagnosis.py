from typing import Literal

from pydantic import BaseModel, Field


class DiagnosisRequest(BaseModel):
    device: str = Field(
        min_length=2,
        max_length=50,
        examples=["phone"],
    )
    language: Literal["en", "sw"] = "en"
    symptom: str = Field(
        min_length=5,
        max_length=1000,
        examples=["My phone battery drains very quickly"],
    )
