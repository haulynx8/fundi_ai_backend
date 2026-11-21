from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.booking import Booking
from app.models.shop import Shop
from app.schemas.booking import (
    BookingCreate,
    BookingListResponse,
    BookingResponse,
    BookingStatusUpdate,
)

router = APIRouter(
    prefix="/bookings",
    tags=["Repair Bookings"],
)


def format_booking_response(booking: Booking) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        user_name=booking.user_name,
        phone=booking.phone,
        shop_id=booking.shop_id,
        date=booking.date,
        status=booking.status,
        device_category=booking.device_category,
        notes=booking.notes,
        created_at=booking.created_at,
        shop_name=booking.shop.name if booking.shop else None,
        shop_location=booking.shop.location if booking.shop else None,
    )


@router.post("/", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
def create_booking(
    payload: BookingCreate,
    db: Session = Depends(get_db),
):
    """Submit a repair booking request for a chosen shop."""
    shop = db.scalar(select(Shop).where(Shop.id == payload.shop_id))
    if shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Selected repair shop with id {payload.shop_id} does not exist.",
        )

    booking = Booking(
        user_name=payload.user_name.strip(),
        phone=payload.phone.strip(),
        shop_id=payload.shop_id,
        date=payload.date,
        status="pending",
        device_category=payload.device_category.strip().lower() if payload.device_category else None,
        notes=payload.notes.strip() if payload.notes else None,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    return format_booking_response(booking)


@router.get("/", response_model=BookingListResponse)
@router.get("", response_model=BookingListResponse, include_in_schema=False)
def list_bookings(
    shop_id: Annotated[int | None, Query(description="Filter bookings by shop ID")] = None,
    status_filter: Annotated[str | None, Query(alias="status", description="Filter bookings by status")] = None,
    phone: Annotated[str | None, Query(description="Filter bookings by customer phone number")] = None,
    user_name: Annotated[str | None, Query(description="Filter bookings by customer name")] = None,
    db: Session = Depends(get_db),
):
    """List repair bookings with optional shop, status, phone, or name filters."""
    query = select(Booking)

    if shop_id:
        query = query.where(Booking.shop_id == shop_id)
    if status_filter:
        query = query.where(Booking.status == status_filter.strip().lower())
    if phone:
        clean = phone.strip()
        query = query.where(Booking.phone.ilike(f"%{clean}%"))
    if user_name:
        query = query.where(Booking.user_name.ilike(f"%{user_name.strip()}%"))

    bookings = db.scalars(query.order_by(Booking.created_at.desc())).all()
    formatted = [format_booking_response(b) for b in bookings]
    return BookingListResponse(
        success=True,
        count=len(formatted),
        bookings=formatted,
    )


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve details for a specific repair booking by ID."""
    booking = db.scalar(select(Booking).where(Booking.id == booking_id))
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with id {booking_id} was not found.",
        )
    return format_booking_response(booking)


@router.patch("/{booking_id}/status", response_model=BookingResponse)
def update_booking_status(
    booking_id: int,
    payload: BookingStatusUpdate,
    db: Session = Depends(get_db),
):
    """Update status of a repair booking (e.g. confirmed, completed, cancelled)."""
    booking = db.scalar(select(Booking).where(Booking.id == booking_id))
    if booking is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with id {booking_id} was not found.",
        )

    booking.status = payload.status
    db.commit()
    db.refresh(booking)
    return format_booking_response(booking)
