
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.fault import FaultCreate, FaultUpdate, FaultResponse
from app.services import fault_service

router = APIRouter(prefix="/faults", tags=["Faults"])


@router.post(
    "",
    response_model=FaultResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_fault(
    fault_data: FaultCreate,
    db: Session = Depends(get_db),
):
    try:
        return fault_service.create_fault(db, fault_data)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )


@router.get("", response_model=list[FaultResponse])
def list_faults(
    device_id: int | None = Query(default=None, gt=0),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return fault_service.get_faults(db, device_id, skip, limit)


@router.get("/{fault_id}", response_model=FaultResponse)
def retrieve_fault(
    fault_id: int,
    db: Session = Depends(get_db),
):
    fault = fault_service.get_fault(db, fault_id)

    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")

    return fault


@router.put("/{fault_id}", response_model=FaultResponse)
def edit_fault(
    fault_id: int,
    fault_data: FaultUpdate,
    db: Session = Depends(get_db),
):
    fault = fault_service.get_fault(db, fault_id)

    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")

    try:
        return fault_service.update_fault(db, fault, fault_data)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.delete("/{fault_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_fault(
    fault_id: int,
    db: Session = Depends(get_db),
):
    fault = fault_service.get_fault(db, fault_id)

    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")

    fault_service.delete_fault(db, fault)
