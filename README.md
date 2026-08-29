# CodeGuardian — Autonomous Engineering Failure Investigation & Verified Repair

> **From Failure to Verified Repair.**  
> CodeGuardian reconstructs production failures, pinpoints their root cause, generates a constrained repair, replays the failure in an isolated sandbox, validates the change against deterministic safety gates, requires human sign-off, and delivers a verified GitHub Pull Request with persistent memory immunization.

---

## The 17-Stage Deterministic Repair Pipeline

CodeGuardian executes an evidence-driven, 17-stage deterministic investigation and repair lifecycle:

```
01 Repository       ──► Identifies target GitHub repository and provisions isolated sandbox
02 Inspection       ──► Scans source tree, directory maps, and build configurations
03 Architecture     ──► Detects language runtime, framework, build system, and microservice graph
04 Failure Detection──► Normalizes the observed failure and produces structured fingerprint
05 Evidence         ──► Collects logs, stack traces, HTTP payloads, and telemetry records
06 GhostTrace       ──► Reconstructs causal execution flow from symptom to root cause component
07 Failure Memory   ──► Searches vector memory for previously validated engineering repairs
08 Investigation    ──► Analyzes bounded context with Sarvam AI investigator
09 Patch            ──► Synthesizes minimal, constrained repair candidate
10 Compatibility    ──► Enforces strict safety rules (imports, signatures, path traversal)
11 Replay           ──► Executes original baseline failure vs patched behavior in isolation
12 Build            ──► Compiles patched workspace in container with zero error tolerance
13 Tests            ──► Runs regression test suite against patched workspace
14 Validation       ──► Evaluates deterministic safety gates (Build, Tests, Replay, Safety)
15 Human Approval   ──► Requires explicit human operator approval before any delivery action
16 Delivery         ──► Creates feature branch, commit, and published GitHub Pull Request
17 Memory Update    ──► Persists validated repair knowledge for future incident immunization
```

---

## Target Multi-Service Architecture

```
                 GitHub
                    │
          ┌─────────┴─────────┐
          │                   │
     CodeGuardian          Target Repo
       frontend            (e.g., JavaAPICheck)
          │
          ▼
      FastAPI API
          │
    ┌─────┼─────┐
    │     │     │
 PostgreSQL Sarvam GitHub API
```

- **Frontend (`frontend/`)**: React 19, TypeScript, Vite, Tailwind CSS, Framer Motion (Render Static Site)
- **Backend (`backend/`)**: FastAPI (Python 3.12+), SQLAlchemy 2.0, PostgreSQL 17 (Render Web Service)
- **VS Code Extension (`vscode-extension/`)**: Native VS Code plugin (`.vsix`) with bounded context investigation & capsule replay.
- **AI Investigator**: Sarvam AI (`sarvam-105b`) direct integration for high-accuracy code synthesis.
- **Deployment (`infra/render.yaml`)**: Infrastructure as Code for automated Render Blueprint deployment.

---

## Quickstart

### Prerequisites
- Docker and Docker Compose
- Node.js 20+ and npm
- Python 3.12+

### 1. Local Development Stack (Docker Compose)
```bash
# Start PostgreSQL, Redis, and FastAPI Backend
docker compose up -d

# Verify backend health & readiness
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

### 2. Start Frontend Dev Server
```bash
cd frontend
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## Configuration (`.env`)

Create `backend/.env` based on `backend/.env.example`:

```ini
APP_ENV=development
DEBUG=true
DATABASE_URL=postgresql+psycopg2://codeguardian:codeguardian_password@localhost:5433/codeguardian_db
SARVAM_API_KEY=your_sarvam_api_key
SARVAM_MODEL=sarvam-105b
GITHUB_TOKEN=your_github_token
```

---

## Production Deployment (Render)

1. In Render Dashboard, click **New +** → **Blueprint**.
2. Connect this repository. Render will automatically provision:
   - `codeguardian-web` (Static Site for React/Vite)
   - `codeguardian-api` (FastAPI Web Service)
   - `codeguardian-db` (PostgreSQL Database)
3. Set your secret environment variables (`SARVAM_API_KEY`, `GITHUB_TOKEN`) in the Render Dashboard.

---

## VS Code Extension Packaging

```bash
cd vscode-extension
npm install
npm run compile
npx @vscode/vsce package
```
Generates `codeguardian-vscode-1.0.0.vsix` for distribution via GitHub Releases.

---

## Running Verification Tests

```bash
# Backend unit & integration tests
cd backend
python -m pytest tests/test_ghosttrace.py tests/test_validation_engine.py tests/test_failure_dna.py tests/test_memory_engine.py tests/test_adversarial.py tests/test_delivery_service.py -v

# Frontend build & typecheck
cd frontend
npm run build
```

---

## License
MIT License. Copyright (c) 2026 CodeGuardian.
