from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import health, devices, faults, diagnoses, shops, bookings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered hardware diagnostic API"
)

# Allow configured frontend URL plus standard local frontend dev origins
cors_origins = list(set([
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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

app.include_router(
    shops.router,
    prefix="/api"
)

app.include_router(
    bookings.router,
    prefix="/api"
)

@app.get("/")
def root():
    return {
        "message": "Welcome to Fundi AI API",
        "documentation": "/docs"
    }
