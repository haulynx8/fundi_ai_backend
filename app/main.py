from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health, devices, faults, diagnoses

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered hardware diagnostic API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    health.router,
    prefix="/api"
)

app.include_router(
    devices.router,
    prefix="/api"
)

app.include_router(
    faults.router,
    prefix="/api"
)

app.include_router(
    diagnoses.router,
    prefix="/api"
)

@app.get("/")
def root():
    return {
        "message": "Welcome to Fundi AI API",
        "documentation": "/docs"
    }
