# CodeGuardian for Visual Studio Code

Autonomous Engineering Failure Investigation, Counterfactual Repair Evaluation, and Failure Immunization inside VS Code.

## Features

- **Activity Bar Integration**: Live Incidents, Counterfactual Repair Lab, and Immunization Guards directly in your editor sidebar.
- **Bounded Context Extraction**: Right click any line of code or stack trace to extract AST-bounded context (100 lines radius) and query Failure DNA.
- **Portable Failure Capsules**: Import or preview sealed `.zip` failure archives with zero secrets exposure.
- **Direct Workspace Link**: Jump directly into the full 17-stage CodeGuardian Engineering Dashboard with one click.

## Configuration

- `codeguardian.apiUrl`: Backend API endpoint (default `http://localhost:8000`).
- `codeguardian.dashboardUrl`: Frontend dashboard endpoint (default `http://localhost:5173`).
- `codeguardian.boundedContextRadius`: Line radius extracted above and below selection (default `100`).

## Installation & Build

```bash
cd vscode-extension
npm install
npm run compile
```
