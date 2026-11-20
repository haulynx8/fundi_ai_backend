from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.diagnosis import Diagnosis
from app.schemas.diagnosis import DiagnosisRequest
from app.services.diagnostic_engine import diagnose

router = APIRouter(
    prefix="/diagnose",
    tags=["Diagnosis"],
)


@router.post("/")
@router.post("", include_in_schema=False)
def create_diagnosis(
    request: DiagnosisRequest,
    db: Session = Depends(get_db),
):
    # Run the diagnostic engine.
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

    # Save the request and its results.
    diagnosis_record = Diagnosis(
        device_id=device.id,
        symptom=request.symptom,
        language=request.language,
        results=jsonable_encoder(matches),
    )
    db.add(diagnosis_record)
    db.commit()
    db.refresh(diagnosis_record)

    return {
        "success": True,
        "device": device.slug,
        "diagnosis": jsonable_encoder(matches),
    }
