# CodeGuardian frontend

React + TypeScript + Vite + Tailwind interface for CodeGuardian's autonomous engineering
failure investigation pipeline.

## Run locally

```bash
npm install
npm run dev
```

The dev server proxies `/api` to the FastAPI backend. Override the target with
`VITE_BACKEND_ORIGIN` (default `http://127.0.0.1:8000`) in a `.env` file, or set
`VITE_API_BASE_URL` to call an absolute backend origin from a built bundle.

```bash
npm run build   # typecheck + production build
npm run lint    # oxlint
```

## Backend contract

The UI is driven entirely by the Demo Mode API. Nothing is simulated in the browser:
when the backend does not report a field, the interface renders an explicit
"not reported" state instead of a placeholder value.

| Method | Endpoint | Used for |
| --- | --- | --- |
| POST | `/api/demo/run` | start a run for a repository URL |
| GET | `/api/demo/runs/{run_id}` | poll run status, stages and events |
| GET | `/api/demo/runs/{run_id}/result` | final investigation payload |
| POST | `/api/demo/runs/{run_id}/approve` | human approval of the validated patch |
| POST | `/api/demo/runs/{run_id}/reject` | human rejection of the patch |

Polling is bounded (1.2s interval, hard cap) and stops on `completed`, `failed`,
`rejected` and `waiting_for_approval`. The pipeline never advances past the human
approval gate without an explicit click.

Responses are read through tolerant normalizers (`src/api/normalize.ts`) that accept
snake_case or camelCase and several common field spellings, so the UI keeps working if
the backend payload differs slightly from the documented shape.

## Structure

```
src/api          request client, response normalizers, domain types
src/hooks        bounded polling hook for a run
src/components   layout, primitives, investigation panels
src/pages        Landing, Investigation workspace
```
