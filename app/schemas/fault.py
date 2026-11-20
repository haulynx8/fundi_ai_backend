
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RiskLevel = Literal["red", "yellow", "green"]
VerificationStatus = Literal["unverified", "verified", "rejected"]


class FaultBase(BaseModel):
    device_id: int = Field(gt=0)
    fault_name: str = Field(min_length=2, max_length=150)
    description: str = Field(min_length=10)

    keywords_en: list[str] = Field(default_factory=list)
    keywords_sw: list[str] = Field(default_factory=list)
    symptoms: list[str] = Field(default_factory=list)
    diagnostic_questions: list[str] = Field(default_factory=list)
    fix_steps: list[str] = Field(default_factory=list)

    cost_min: int = Field(ge=0)
    cost_max: int = Field(ge=0)

    risk_level: RiskLevel
    verification_status: VerificationStatus = "unverified"
    source: str | None = Field(default=None, max_length=255)


class FaultCreate(FaultBase):
    pass


class FaultUpdate(BaseModel):
    device_id: int | None = Field(default=None, gt=0)
    fault_name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, min_length=10)

    keywords_en: list[str] | None = None
    keywords_sw: list[str] | None = None
    symptoms: list[str] | None = None
    diagnostic_questions: list[str] | None = None
    fix_steps: list[str] | None = None

    cost_min: int | None = Field(default=None, ge=0)
    cost_max: int | None = Field(default=None, ge=0)

    risk_level: RiskLevel | None = None
    verification_status: VerificationStatus | None = None
    source: str | None = Field(default=None, max_length=255)


class FaultResponse(FaultBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
