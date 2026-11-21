from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.diagnosis import Diagnosis
from app.models.shop import Shop
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResponse
from app.services.diagnostic_engine import diagnose, generate_follow_up_question

router = APIRouter(
    prefix="/diagnose",
    tags=["Diagnosis"],
)


@router.post("/", response_model=DiagnosisResponse)
@router.post("", response_model=DiagnosisResponse, include_in_schema=False)
def create_diagnosis(
    request: DiagnosisRequest,
    db: Session = Depends(get_db),
):
    # Run Diagnostic Engine 2.0
    device, matches = diagnose(
        db=db,
        device_slug=request.device,
        language=request.language,
        symptom=request.symptom,
    )

    # Reject unknown device categories.
    if device is None:
        raise HTTPException(
            status_code=404,
            detail=f"Device category '{request.device}' was not found.",
        )

    # Encode and persist diagnosis record
    encoded_matches = jsonable_encoder(matches)
    diagnosis_record = Diagnosis(
        device_id=device.id,
        symptom=request.symptom,
        language=request.language,
        results=encoded_matches,
    )
    db.add(diagnosis_record)
    db.commit()
    db.refresh(diagnosis_record)

    # Derive diagnostic intelligence additions: follow-up question, safety & escalation
    follow_up = generate_follow_up_question(device.slug, matches, request.symptom)
    has_red = any(m.get("risk_level") == "red" for m in matches)
    has_yellow = any(m.get("risk_level") == "yellow" for m in matches)
    requires_tech = has_red or has_yellow
    safety_warning = (
        "CRITICAL: High hazard hardware fault suspected. Power down device and consult a technician."
        if has_red else (
            "Hardware servicing or component replacement recommended." if has_yellow else None
        )
    )

    # Include top recommended repair shops for users whose issue requires repair
    shops = db.scalars(
        select(Shop).order_by(Shop.rating.is_(None), Shop.rating.desc(), Shop.name.asc()).limit(3)
    ).all()
    suggested_shops = [
        {
            "id": s.id,
            "name": s.name,
            "location": s.location,
            "phone": s.phone,
            "services": s.services or [],
            "rating": s.rating,
            "price_range": s.price_range,
            "phone_url": f"tel:{s.phone}",
            "booking_url": f"tel:{s.phone}",
        }
        for s in shops
    ]

    return {
        "success": True,
        "diagnosis_id": diagnosis_record.id,
        "device": device.slug,
        "language": request.language,
        "symptom": request.symptom,
        "requires_technician": requires_tech,
        "safety_warning": safety_warning,
        "follow_up_question": follow_up,
        "diagnosis": encoded_matches,
        "results": encoded_matches,
        "suggested_shops": suggested_shops,
    }
