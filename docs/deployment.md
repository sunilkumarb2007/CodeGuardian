# CodeGuardian Deployment Guide

## Overview
CodeGuardian is configured for multi-service deployment:
- **Frontend:** Render Static Site (React + Vite)
- **Backend:** Render Web Service (FastAPI Docker container)
- **Database:** Render PostgreSQL (Postgres 17)
- **VS Code Extension:** Packaged `.vsix` attached to GitHub Releases

---

## 1. Quick Deploy via Render Blueprint
1. In the Render Dashboard, click **New +** → **Blueprint**.
2. Connect the `CodeGuardian` GitHub repository.
3. Render will automatically parse `infra/render.yaml` and provision:
   - `codeguardian-web` (Static Site)
   - `codeguardian-api` (Web Service)
   - `codeguardian-db` (Postgres Database)
4. Add the required private environment variables in the Render Dashboard:
   - `SARVAM_API_KEY`: Your Sarvam API authentication key
   - `GITHUB_TOKEN`: GitHub Personal Access Token with repo scope for PR generation

---

## 2. Local Docker Compose Deployment
To run the full stack locally with PostgreSQL:

```bash
# Start PostgreSQL, Redis, and FastAPI backend
docker compose up -d

# Start Frontend Dev Server
cd frontend
npm install
npm run dev
```

Frontend will be accessible on `http://localhost:5173/` and backend API on `http://localhost:8000/`.
