from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import health, incidents, orchestration, runs, system, failure_lab, capsules, extension
from app.db.database import engine, Base, get_db
from contextlib import asynccontextmanager

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")
    # Automatically ensure any schema tables are created in PostgreSQL
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title=settings.app_name,
    description="CodeGuardian Autonomous Failure Investigation & Repair Engine API",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS for local development and Render/Vercel/Production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?|https://.*\.onrender\.com|https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Health & Readiness Endpoints
@app.get("/health", tags=["Health"])
def root_health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "version": "1.0.0"
    }

@app.get("/ready", tags=["Health"])
def readiness_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "provider": settings.ai_provider,
            "model": settings.sarvam_model or settings.ai_model
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e)
        }

# Include Routers
app.include_router(health.router, prefix="/api/health", tags=["Health"])
app.include_router(system.router, tags=["System"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(runs.router, prefix="/api/runs", tags=["Runs"])
app.include_router(orchestration.router, prefix="/api/orchestration", tags=["Orchestration"])
app.include_router(failure_lab.router, prefix="/api/failure-lab", tags=["FailureLab"])
app.include_router(capsules.router, prefix="/api", tags=["Capsules"])
app.include_router(extension.router, prefix="/api", tags=["Extension"])
