from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.routes import health, incidents, demo, orchestration, runs

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="CodeGuardian Engineering Backend",
    version="0.1.0",
)

# Configure CORS for local React development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(demo.router, prefix="/api/demo", tags=["Demo"])
app.include_router(runs.router, prefix="/api/runs", tags=["Runs"])
app.include_router(orchestration.router, prefix="/api/orchestration", tags=["Orchestration"])

@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting {settings.app_name} in {settings.app_env} mode")
