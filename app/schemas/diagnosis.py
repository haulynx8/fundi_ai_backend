from typing import Any, Literal

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


class EstimatedCost(BaseModel):
    min: int
    max: int
    currency: str = "KES"


class FaultMatch(BaseModel):
    fault: str
    match_score: int
    risk_level: str
    estimated_cost: EstimatedCost
    fix_steps: list[str]
    safety_warning: str | None = None
    requires_technician: bool = False

    # Frontend compatibility & display fields
    title: str | None = None
    confidence: int | None = None
    confidence_score: int | None = None
    risk: str | None = None
    severity: str | None = None
    cost: str | None = None
    cost_estimate: str | None = None
    currency: str = "KES"
    steps: list[str] | None = None
    description: str | None = None


class FollowUpOption(BaseModel):
    label: str
    indicates: str | None = None


class FollowUpQuestion(BaseModel):
    question: str
    options: list[FollowUpOption]


class DiagnosisResponse(BaseModel):
    success: bool = True
    diagnosis_id: int
    device: str
    language: str
    symptom: str
    requires_technician: bool = False
    safety_warning: str | None = None
    follow_up_question: FollowUpQuestion | None = None
    diagnosis: list[FaultMatch]
    results: list[FaultMatch] = Field(default_factory=list)
    suggested_shops: list[Any] = Field(default_factory=list)
