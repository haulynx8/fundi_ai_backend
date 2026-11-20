
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.fault import Fault
from app.schemas.fault import FaultCreate, FaultUpdate


def create_fault(db: Session, fault_data: FaultCreate) -> Fault:
    device = db.get(Device, fault_data.device_id)

    if not device:
        raise ValueError("Device not found")

    if fault_data.cost_min > fault_data.cost_max:
        raise ValueError("Minimum cost cannot exceed maximum cost")

    fault = Fault(**fault_data.model_dump())

    db.add(fault)
    db.commit()
    db.refresh(fault)

    return fault


def get_fault(db: Session, fault_id: int) -> Fault | None:
    return db.get(Fault, fault_id)


def get_faults(
    db: Session,
    device_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Fault]:
    statement = select(Fault)

    if device_id is not None:
        statement = statement.where(Fault.device_id == device_id)

    statement = statement.offset(skip).limit(limit)

    return list(db.scalars(statement).all())


def update_fault(
    db: Session,
    fault: Fault,
    fault_data: FaultUpdate,
) -> Fault:
    updates = fault_data.model_dump(exclude_unset=True)

    new_device_id = updates.get("device_id", fault.device_id)

    if new_device_id is not None and not db.get(Device, new_device_id):
        raise ValueError("Device not found")

    new_min = updates.get("cost_min", fault.cost_min)
    new_max = updates.get("cost_max", fault.cost_max)

    if new_min is not None and new_max is not None and new_min > new_max:
        raise ValueError("Minimum cost cannot exceed maximum cost")

    for field, value in updates.items():
        setattr(fault, field, value)

    db.commit()
    db.refresh(fault)

    return fault


def delete_fault(db: Session, fault: Fault) -> None:
    db.delete(fault)
    db.commit()
