# CodeGuardian Backend

This is the FastAPI backend foundation for CodeGuardian, designed to interface with the existing PostgreSQL database.

## Prerequisites
- Python 3.11+
- PostgreSQL database (`codeguardian_db`)

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment configuration:
   Copy `.env.example` to `.env` and configure your database credentials.

## Running the Server

Start the FastAPI server using Uvicorn:
```bash
uvicorn app.main:app --reload
```

## Endpoints
- **Health**: `GET /health`, `GET /health/database`
- **Incidents**: `GET /api/incidents`
- **Incident Details**: `GET /api/incidents/{id}`
- **Evidence**: `GET /api/incidents/{id}/evidence`
- **GhostTrace**: `GET /api/incidents/{id}/trace`
- **Failure Memory**: `GET /api/incidents/{id}/memory`

## API Documentation
Once running, interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Current Phase 2 Scope
- Foundational architecture (Clean Architecture)
- Database schema mapping
- Core API reading operations for incidents, evidence, trace, and memory.
- Business rule architectural placeholders.

*Intentionally not implemented yet: Gemini AI, Docker isolation, GitHub PR creation, Frontend React.*
