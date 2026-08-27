# CodeGuardian — Autonomous Engineering Failure Investigation

> **From Failure to Verified Repair.**  
> CodeGuardian reconstructs production failures, finds their root cause, generates a constrained repair, replays the failure, validates the change, and prepares delivery only after deterministic proof.

---

## The 17-Stage Deterministic Repair Pipeline

CodeGuardian executes an evidence-driven, 17-stage deterministic investigation and repair lifecycle:

```
01 Repository       ──► Identifies target GitHub repository and provisions isolated workspace
02 Inspection       ──► Scans source tree and configuration maps
03 Architecture     ──► Detects language, framework, build system, and test runner strategies
04 Failure Detection──► Normalizes the observed failure and produces a structured fingerprint
05 Evidence         ──► Collects logs, stack traces, HTTP payloads, and execution metadata
06 GhostTrace       ──► Reconstructs causal execution flow to locate root cause component
07 Failure Memory   ──► Searches vector memory for previously validated engineering repairs
08 Investigation    ──► Analyzes bounded context with the configured AI investigator
09 Patch            ──► Synthesizes a minimal, constrained repair candidate
10 Compatibility    ──► Enforces strict safety rules (imports, signatures, path traversal)
11 Replay           ──► Executes original failure vs patched behavior in isolation
12 Build            ──► Compiles patched workspace in sandbox container
13 Tests            ──► Runs regression test suite against patched workspace
14 Validation       ──► Evaluates deterministic safety gates (Build, Tests, Replay, Safety)
15 Human Approval   ──► Requires explicit human approval before any delivery action
16 Delivery         ──► Creates feature branch, commit, and GitHub Pull Request
17 Memory Update    ──► Persists validated repair knowledge for future incident reuse
```

---

## Architecture & Technology Stack

- **Frontend / IDE Workspace**: React 19, TypeScript, Vite, Tailwind CSS, Framer Motion
  - Operational top bar, repository selector, 17-stage pipeline rail, interactive service map, execution timeline, and persistent AutoFix AI agent panel.
- **Backend API & Engine**: FastAPI (Python 3.12+), SQLAlchemy 2.0, PostgreSQL, Redis distributed lock manager & heartbeat monitor.
- **Investigation & Verification**: OpenRouter AI investigation provider with monotonic deadlines, isolated Git sandboxes, and automated Maven/Gradle test execution.

---

## Quickstart

### Prerequisites
- Docker and Docker Compose
- Node.js 20+ and npm
- Python 3.12+ (if running natively)

### 1. Start Infrastructure & Backend (Docker)
```bash
docker compose up -d
```
Verify health:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/system/status
```

### 2. Start Frontend (Vite Dev Server)
```bash
cd frontend
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

## Running Tests

### Backend Test Suite (Pytest)
```bash
docker compose exec backend pytest
```

### Frontend Typecheck & Build
```bash
cd frontend
npm run build
```

---

## License
MIT License. Copyright (c) 2026 CodeGuardian.
