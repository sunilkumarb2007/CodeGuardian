# CODEGUARDIAN DEVELOPMENT RULE

FastAPI is manually started.

CodeGuardian application code never starts Uvicorn.

Automated agents must not launch long-running server processes.

Automated tests must not endlessly poll orchestration runs.

End-to-end testing should use bounded execution.
