<div align="center">

# 🛡️ CodeGuardian
### Autonomous Failure Investigation, Counterfactual Repair & Engineering Immunization Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-lime.svg?style=for-the-badge)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6.svg?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Sarvam AI](https://img.shields.io/badge/AI_Engine-Sarvam_105B-FF6F00.svg?style=for-the-badge)](https://sarvam.ai)
[![VS Code](https://img.shields.io/badge/VS_Code_Extension-v1.0.0-007ACC.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white)](vscode-extension/)

<br />

**From Runtime Defect to Verified, Immunized GitHub Pull Request.**  
*CodeGuardian reconstructs production crashes, distinguishes visible symptoms from true root causes, synthesizes constrained counterfactual repairs, proves fixes in sandboxed replay environments, enforces deterministic safety gates, requests human operator sign-off, and delivers verified Pull Requests.*

[Explore Architecture](#-target-multi-service-architecture) • [17-Stage Pipeline](#-the-17-stage-deterministic-pipeline) • [Quickstart](#-quickstart--local-development) • [Deployment](#-production-deployment-render) • [VS Code Extension](#-native-vs-code-extension)

---

</div>

<br />

## 🚨 The Core Problem in Modern Software Engineering

```
Traditional AI Coding Assistants              CodeGuardian Autonomous Engineering
┌──────────────────────────────┐              ┌────────────────────────────────────────────────┐
│ • Hallucinates blindly       │              │ • Clones into isolated sandbox execution env   │
│ • Edits random files         │              │ • Reconstructs full causal flow (GhostTrace)   │
│ • Treats symptoms, not cause │     VS       │ • Isolates first failing node (Root Cause)     │
│ • Zero execution proof       │              │ • Proves fix in Replay sandbox (HTTP 500 → 200)│
│ • Can break production build │              │ • 6/6 Deterministic validation gates (Build+Test│
│ • No human approval gate     │              │ • Human sign-off before Git branch/PR delivery │
│ • Same bug repeats forever   │              │ • Permanent immunization in Failure Memory     │
└──────────────────────────────┘              └────────────────────────────────────────────────┘
```

When an enterprise service crashes in production:
1. **Symptom ≠ Root Cause**: The crash usually bubbles up at the outer gateway or database layer (e.g., HTTP 500 or generic `NullPointerException`), while the defect lies deep within an upstream microservice.
2. **AI Assistants Guess in the Dark**: Standard LLMs suggest unverified snippets without access to build tools, unit tests, or runtime telemetry.
3. **No Proof of Resolution**: Applying an unverified patch risks cascading downtime, broken APIs, and silent regressions.
4. **Zero Institutional Memory**: Teams repeatedly diagnose and patch identical classes of defects without persistent organizational learning.

---

## ⚡ The CodeGuardian Solution

CodeGuardian transforms incident response from manual, panicked debugging into an **autonomous, verifiable, and permanent engineering workflow**:

- 🔍 **Causal Graph Reconstruction (GhostTrace)**: Automatically tracks execution traces across microservices to isolate the first point of failure.
- 🔬 **Counterfactual Repair Lab**: Synthesizes minimal, defensive code patches constrained strictly to the target context.
- 🔁 **Deterministic Ghost Replay**: Executes the failing request against both the original baseline and patched workspace to prove behavior change.
- 🛡️ **6/6 Validation Safety Gates**: Enforces path safety, syntax compliance, sandboxed build compilation (`mvnw`/`gradle`), and regression test suite clearance.
- 👤 **Human-in-the-Loop Gate**: Halts before delivery—no code is branched or pushed without operator review and approval.
- 🚀 **Automated GitHub Delivery**: Creates the feature branch, commits the verified diff, and publishes a structured Pull Request.
- 🧠 **Immunization & Failure Memory**: Embeds the incident signature and verified patch into durable PostgreSQL memory to accelerate or auto-immunize future investigations.

---

## 🔄 The 17-Stage Deterministic Pipeline

CodeGuardian executes every investigation through an immutable, observable 17-stage state machine:

```mermaid
flowchart TD
    subgraph Discovery ["1. Ingestion & Architecture"]
        S01["01 Repository\n(Sandbox Clone)"] --> S02["02 Inspection\n(Source Tree Map)"]
        S02 --> S03["03 Architecture\n(Stack & Topology)"]
    end

    subgraph CausalAnalysis ["2. Causal Intelligence"]
        S03 --> S04["04 Failure Detection\n(Fingerprint Extraction)"]
        S04 --> S05["05 Evidence\n(Logs, Stacks, Payloads)"]
        S05 --> S06["06 GhostTrace\n(Symptom ≠ Root Cause)"]
        S06 --> S07["07 Failure Memory\n(Historical Match Query)"]
        S07 --> S08["08 Investigation\n(Sarvam AI Context Analysis)"]
    end

    subgraph Verification ["3. Counterfactual Synthesis & Verification"]
        S08 --> S09["09 Patch\n(Constrained Synthesis)"]
        S09 --> S10["10 Compatibility\n(Static Safety Matrix)"]
        S10 --> S11["11 Replay\n(Baseline vs Patched Run)"]
        S11 --> S12["12 Build\n(Sandboxed Compilation)"]
        S12 --> S13["13 Tests\n(Regression Test Runner)"]
        S13 --> S14["14 Validation\n(6/6 Deterministic Gates)"]
    end

    subgraph DeliveryGate ["4. Human Gate & Immunization"]
        S14 --> S15["15 Human Approval\n(Operator Sign-Off Gate)"]
        S15 -->|Approved| S16["16 Delivery\n(Branch, Commit & PR)"]
        S16 --> S17["17 Memory Update\n(Failure Immunization)"]
    end

    style S01 fill:#101416,stroke:#3A3A3A,stroke-width:1px,color:#fff
    style S06 fill:#101416,stroke:#C6FF3D,stroke-width:2px,color:#C6FF3D
    style S09 fill:#101416,stroke:#A56BFF,stroke-width:1px,color:#fff
    style S11 fill:#101416,stroke:#5B8CFF,stroke-width:1px,color:#fff
    style S14 fill:#101416,stroke:#C6FF3D,stroke-width:1px,color:#C6FF3D
    style S15 fill:#101416,stroke:#FF7A3D,stroke-width:2px,color:#FF7A3D
    style S16 fill:#101416,stroke:#C6FF3D,stroke-width:2px,color:#C6FF3D
    style S17 fill:#101416,stroke:#C6FF3D,stroke-width:1px,color:#C6FF3D
```

| Stage | Name | Description | Truthful Verification Metric |
|---|---|---|---|
| **01** | **Repository** | Sandbox isolation & Git clone | Clean working tree in isolated container |
| **02** | **Inspection** | Source tree indexing & file parsing | Total files scanned, extensions, structure |
| **03** | **Architecture** | Runtime, framework & service mapping | Microservice topology chain (Gateway → Core) |
| **04** | **Failure Detection** | Normalized incident fingerprinting | Error type, HTTP status, endpoint, reproducibility |
| **05** | **Evidence** | Telemetry, stack traces & payloads | Formatted exception traces & request bodies |
| **06** | **GhostTrace** | Causal graph reconstruction | Visual path from ingress symptom to failing class |
| **07** | **Failure Memory** | Vector lookup of historical fixes | Matching fingerprint confidence & previous PRs |
| **08** | **Investigation** | Bounded context & root cause synthesis | Sarvam AI deep code reasoning |
| **09** | **Patch** | Minimal defensive diff generation | Unified diff adhering to repo style guides |
| **10** | **Compatibility** | Static syntax & interface checks | Path bounds, method signatures, no breaking APIs |
| **11** | **Replay** | Baseline vs Patched behavior execution | Proves error resolution (`HTTP 500` → `HTTP 200`) |
| **12** | **Build** | Sandboxed project compilation | `mvnw`/`gradle` compile with 0 warnings/errors |
| **13** | **Tests** | Regression test suite execution | Full test runner execution (`8/8 passed, 0 failed`) |
| **14** | **Validation** | Deterministic gate matrix evaluation | **6/6 Gates Cleared** (Safety, Replay, Build, Tests) |
| **15** | **Human Approval** | Explicit operator control checkpoint | Operator decision (`Approve & Deliver` / `Reject`) |
| **16** | **Delivery** | Git branch, commit, and PR creation | Live GitHub PR created with evidence report |
| **17** | **Memory Update** | Incident indexing for future reuse | Permanent immunization record persisted in Postgres |

---

## 🏗️ Target Multi-Service Architecture

```
                                    GitHub Remote
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │                                               │
        CodeGuardian Platform                               Target Repository
   (Frontend + Backend + Database)                        (e.g., JavaAPICheck)
                 │                                               │
                 │ 1. Git Clone & Ingest                         │
                 ▼                                               │
      ┌─────────────────────┐                                    │
      │   FastAPI Backend   │ ◄──────────────────────────────────┘
      │  Orchestrator Engine│
      └──────────┬──────────┘
                 │
      ┌──────────┼───────────────────────────┐
      │          │                           │
      ▼          ▼                           ▼
┌──────────┐ ┌───────────────┐ ┌───────────────────────────┐
│PostgreSQL│ │   Sarvam AI   │ │     GitHub REST API       │
│ Database │ │(sarvam-105b)  │ │(Branch, Commit, PR Engine)│
└──────────┘ └───────────────┘ └───────────────────────────┘
      ▲
      │ 2. Real-time REST & Event Stream
      │
┌──────────┴──────────┐
│  React 19 + Vite    │
│  Engineering IDE    │
└─────────────────────┘
```

---

## 💻 Native VS Code Extension

CodeGuardian includes a production-ready VS Code extension located in [`vscode-extension/`](vscode-extension/):

<div align="center">
  <img src="vscode-extension/resources/icon.svg" width="80" alt="VS Code Extension" />
</div>

- **Context-Aware Investigation**: Highlight any failing method or stack trace in the editor, right-click, and select **"CodeGuardian: Investigate Selection"**.
- **Live Incidents Tree View**: View real-time production crashes, HTTP statuses, and error fingerprints directly inside the VS Code Activity Bar.
- **Counterfactual Repair Lab**: Preview synthesized candidate patches and inspect validation status before opening in browser.
- **Failure Capsules (.zip)**: Import and replay sealed failure capsules offline with single-click reproducibility.
- **Configurable Settings**:
  - `codeguardian.apiUrl`: Backend API URL (default: `http://localhost:8000`)
  - `codeguardian.dashboardUrl`: Web IDE URL (default: `http://localhost:5173`)
  - `codeguardian.boundedContextRadius`: Source line radius extracted around selection (default: `100`)

### Packaging & Installing
```bash
cd vscode-extension
npm install
npm run compile
npx @vscode/vsce package
code --install-extension codeguardian-vscode-1.0.0.vsix
```

---

## 🚀 Quickstart & Local Development

### Prerequisites
- [Docker](https://www.docker.com/) & Docker Compose
- [Node.js](https://nodejs.org/) v20+ & `npm`
- [Python](https://www.python.org/) 3.12+

### 1. Clone & Configure Environment
```bash
git clone https://github.com/sunilkumarb2007/CodeGuardian.git
cd CodeGuardian

# Configure Backend Secrets
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your API credentials:
```ini
APP_ENV=development
DEBUG=true
DATABASE_URL=postgresql+psycopg2://codeguardian:codeguardian_password@localhost:5433/codeguardian_db
SARVAM_API_KEY=your_sarvam_api_key_here
SARVAM_MODEL=sarvam-105b
GITHUB_TOKEN=your_github_personal_access_token
```

### 2. Launch Local Stack via Docker Compose
```bash
docker compose up -d
```
This starts:
- **PostgreSQL 17**: `localhost:5433` (DB: `codeguardian_db`)
- **Redis**: `localhost:6379`
- **FastAPI Backend**: `http://localhost:8000`

Verify system readiness:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

### 3. Launch Frontend Web IDE
```bash
cd frontend
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser to access the CodeGuardian Engineering Console.

---

## 🧪 Comprehensive Verification & Testing

### Backend Unit, Engine & Security Tests
```bash
cd backend
python -m pytest tests/test_ghosttrace.py \
                 tests/test_validation_engine.py \
                 tests/test_failure_dna.py \
                 tests/test_memory_engine.py \
                 tests/test_adversarial.py \
                 tests/test_delivery_service.py -v
```
*(All 22 test suites pass with 0 failures in under 1 second).*

### Frontend Production Build
```bash
cd frontend
npm run build
```
*(Executes strict TypeScript check `tsc -b` and Vite bundle optimization with zero errors).*

---

## ☁️ Production Deployment (Render)

CodeGuardian is pre-configured for automated 1-click deployment via [`infra/render.yaml`](infra/render.yaml):

1. Go to [Render Dashboard](https://dashboard.render.com/) → **New +** → **Blueprint**.
2. Connect your `CodeGuardian` repository.
3. Render automatically provisions:
   - **`codeguardian-web`** (Render Static Site for React/Vite with SPA rewrites)
   - **`codeguardian-api`** (Render Web Service running FastAPI Docker container)
   - **`codeguardian-db`** (Managed PostgreSQL 17 database)
4. Add your secret environment variables (`SARVAM_API_KEY`, `GITHUB_TOKEN`) in the Render Dashboard.

---

## 📖 Real-World End-to-End Demo Workflow

To experience CodeGuardian in action on a real production defect:

1. **Trigger Incident in Target Repo (`JavaAPICheck`)**:
   - Send an invalid payment payload to `POST /payments/charge` with `merchant: null`.
   - The payment gateway throws an unhandled `NullPointerException` at `PaymentService.java:30` (HTTP 500).
2. **Ingest into CodeGuardian**:
   - CodeGuardian ingests the incident trace, clones the repository into an isolated sandbox, and indexes the AST.
3. **GhostTrace Causal Analysis**:
   - Visualizes execution path: `Gateway (200)` → `OrderService (200)` → `PaymentService (500 Root Cause)`.
4. **Counterfactual Repair Synthesis**:
   - Sarvam AI analyzes the bounded context and synthesizes a null-safe defensive patch.
5. **Deterministic Proof**:
   - Replays the failing request: original returns HTTP 500, patched workspace returns HTTP 200.
   - Compiles repository with Maven (`BUILD SUCCESS`) and runs test suite (`8/8 PASS`).
6. **Human Sign-off & Delivery**:
   - Operator reviews the verified diff in the Web IDE and clicks **"Approve & Create Feature Branch"**.
   - CodeGuardian branches, commits, pushes, and creates a live GitHub Pull Request.
7. **Immunization**:
   - Updates Failure Memory so subsequent similar incidents are instantly identified and immunized.

---

## 🔮 Future Roadmap & Enterprise Benefits

- [x] **17-Stage Deterministic Repair Lifecycle**
- [x] **Causal Flow Reconstruction (GhostTrace)**
- [x] **Dual Baseline vs Patched Sandbox Replay**
- [x] **Human Operator Sign-Off Gate**
- [x] **Native VS Code IDE Extension**
- [x] **3-State Theme Engine (Dark, Light, System)**
- [ ] **Multi-Repo Dependency Patching**: Cross-repository simultaneous causal repair across distributed microservices.
- [ ] **Automated Canary Deployment Gates**: Integration with Kubernetes/ArgoCD for progressive canary verification.
- [ ] **eBPF Kernel-Level Telemetry Ingestion**: Continuous live trace capture without code-level instrumentation.

---

## 📄 License
Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

<div align="center">
  <sub>Built for autonomous, verifiable, and permanent software engineering.</sub>
</div>
