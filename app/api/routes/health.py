
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "application": "Fundi AI",
        "version": "0.1.0"
    }


@router.get("/health/db")
def database_health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))

        return {
            "status": "connected",
            "database": "MySQL",
            "message": "Database connection successful"
        }

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        ) from error
