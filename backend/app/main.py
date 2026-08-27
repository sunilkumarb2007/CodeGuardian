from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import health, incidents, orchestration, runs, system

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")
    yield

app = FastAPI(
    title=settings.app_name,
    description="CodeGuardian Engineering Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(system.router, tags=["System"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(runs.router, prefix="/api/runs", tags=["Runs"])
app.include_router(orchestration.router, prefix="/api/orchestration", tags=["Orchestration"])

