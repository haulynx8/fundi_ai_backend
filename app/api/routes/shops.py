from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.shop import Shop
from app.schemas.shop import ShopCreate, ShopListResponse, ShopResponse

router = APIRouter(
    prefix="/shops",
    tags=["Repair Shops"],
)


def format_shop_response(shop: Shop) -> ShopResponse:
    return ShopResponse(
        id=shop.id,
        name=shop.name,
        location=shop.location,
        phone=shop.phone,
        services=shop.services or [],
        rating=shop.rating,
        price_range=shop.price_range,
        phone_url=f"tel:{shop.phone}",
        booking_url=f"tel:{shop.phone}",
        created_at=shop.created_at,
    )


@router.get("/", response_model=ShopListResponse)
def list_shops(
    location: Annotated[str | None, Query(description="Filter by location/neighborhood")] = None,
    service: Annotated[str | None, Query(description="Filter by offered service keyword")] = None,
    db: Session = Depends(get_db),
):
    """Retrieve all available repair shops with optional location and service filters."""
    query = select(Shop)

    if location:
        query = query.where(Shop.location.ilike(f"%{location.strip()}%"))

    shops = db.scalars(query.order_by(Shop.rating.is_(None), Shop.rating.desc(), Shop.name.asc())).all()

    # Filter in Python if service keyword is specified
    if service:
        svc_lower = service.strip().lower()
        shops = [
            s for s in shops
            if any(svc_lower in str(x).lower() for x in (s.services or []))
        ]

    formatted_shops = [format_shop_response(s) for s in shops]
    return ShopListResponse(
        success=True,
        count=len(formatted_shops),
        shops=formatted_shops,
    )


@router.get("/{shop_id}", response_model=ShopResponse)
def get_shop(
    shop_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve details for a specific repair shop by ID."""
    shop = db.scalar(select(Shop).where(Shop.id == shop_id))
    if shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repair shop with id {shop_id} was not found.",
        )
    return format_shop_response(shop)


@router.post("/", response_model=ShopResponse, status_code=status.HTTP_201_CREATED)
def create_shop(
    payload: ShopCreate,
    db: Session = Depends(get_db),
):
    """Register a new repair shop in the directory."""
    shop = Shop(
        name=payload.name.strip(),
        location=payload.location.strip(),
        phone=payload.phone.strip(),
        services=payload.services,
        rating=payload.rating,
        price_range=payload.price_range,
    )
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return format_shop_response(shop)
