"""
Main Application Entry Point.

Sets up:
- FastAPI instance with documentation metadata
- CORS middleware
- Database table creation on startup
- Static files route (/media) for safely serving leaf images
- All API routers (Auth, Users, Predict, Diseases, History, Feedback)
- Global health check endpoint
"""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import engine, Base
from app.services.ml_service import ml_service
from app import schemas

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("canecare.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Runs database schema migrations/creation automatically on startup.
    """
    logger.info("Initializing CaneCare AI database tables...")
    # Ensure SQLite tables exist
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    logger.info(f"CaneCare AI running in ML Mode: {'REAL' if ml_service.is_real_model else 'MOCK'}")
    yield
    logger.info("CaneCare AI backend shutting down.")


# Initialize FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for CaneCare AI: Sugarcane Leaf Disease Prediction, Advisory & Health Management.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded leaf images safely through static file mount
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory=settings.UPLOAD_DIR), name="media")


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------
@app.get(
    "/api/v1/health",
    response_model=schemas.HealthResponse,
    tags=["System Health"],
    summary="API Health Check",
    description="Check the server status, active app version, and whether real or mock ML is in use."
)
def health_check():
    return schemas.HealthResponse(
        status="ok",
        app_version=settings.VERSION,
        model_mode="real" if ml_service.is_real_model else "mock"
    )


# ---------------------------------------------------------------------------
# Include API Routers
# ---------------------------------------------------------------------------
from app.routers import auth, users, predict, diseases, history, feedback, shops

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(predict.router)
app.include_router(diseases.router)
app.include_router(history.router)
app.include_router(feedback.router)
app.include_router(shops.router)


@app.get("/", include_in_schema=False)
def root():
    return {
        "message": "Welcome to CaneCare AI Backend API. Visit /docs for the interactive Swagger UI.",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

