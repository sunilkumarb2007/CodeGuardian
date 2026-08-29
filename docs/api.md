# CodeGuardian API Reference

## Base URLs
- **Development:** `http://localhost:8000`
- **Production:** `https://codeguardian-api.onrender.com`

---

## Endpoints

### 1. Health & Readiness
- `GET /health`: Returns service health status and environment.
- `GET /ready`: Verifies database connectivity and AI provider availability.

### 2. Incidents
- `POST /api/incidents`: Ingests an active incident payload for investigation.
- `GET /api/incidents`: Lists recent incidents.
- `GET /api/incidents/{incident_id}`: Retrieves specific incident details.

### 3. Runs & Pipeline Execution
- `POST /api/runs`: Initiates a 17-stage autonomous investigation run.
- `GET /api/runs/{run_id}`: Fetches complete run record, stage states, evidence, and verification metrics.
- `GET /api/runs/{run_id}/events`: Streams or lists chronological `RunEvent` records.

### 4. Human Approval & Delivery Gate
- `POST /api/orchestration/runs/{run_id}/decide`: Submits operator approval or rejection for candidate repair.
- `POST /api/orchestration/runs/{run_id}/files/{file_id}/decision`: Submits per-file approval status.

### 5. VS Code Extension & Capsules
- `GET /api/extension/download`: Downloads latest `.vsix` extension package.
- `POST /api/capsules/import`: Imports sealed offline failure capsule.
- `GET /api/capsules/{run_id}/export`: Exports incident diagnosis capsule.
