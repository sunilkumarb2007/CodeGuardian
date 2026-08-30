import re
from typing import List, Tuple
from app.db import models

class InvestigationContextBuilder:
    @staticmethod
    def extract_relevant_source_files(
        evidence: List[models.EvidenceEvent],
        trace: models.FailureTrace,
        all_files: List[models.RepositoryFile]
    ) -> List[models.RepositoryFile]:
        """
        Filters the full repository file list down to only files that are
        relevant to the observed failure based on the stack trace or causal trace.
        Enforces a maximum of 3 files ranked by evidence relevance.
        """
        source_files = []
        seen_paths = set()
        
        def add_file(f: models.RepositoryFile):
            if f and f.file_path not in seen_paths:
                seen_paths.add(f.file_path)
                source_files.append(f)
        
        # 1. Primary: Extract directly from stack trace lines in evidence
        for e in evidence:
            if e.stack_trace:
                # Match Java/Python/Go/TS stack traces, e.g., (ClassName.java:42) or "file.py", line 42
                matches = re.findall(r'[\s\(/]([A-Za-z0-9_\-\.]+\.(?:java|py|ts|tsx|js|go|kt|rs))[:\)]', e.stack_trace)
                for file_name in matches:
                    matching_repo_files = [f for f in all_files if f.file_path.endswith(file_name) or f.file_path.endswith("/" + file_name)]
                    for mf in matching_repo_files:
                        add_file(mf)
        
        # 2. Secondary: Match from GhostTrace root cause candidate / symptom service
        if trace:
            if trace.root_cause_candidate and trace.root_cause_candidate not in ("generic-service", "unknown"):
                candidate_clean = trace.root_cause_candidate.replace("-service", "")
                for f in all_files:
                    if candidate_clean.lower() in f.file_path.lower() and f.file_path.endswith((".java", ".py", ".ts", ".go", ".kt", ".rs")):
                        add_file(f)
            if trace.symptom_service and trace.symptom_service not in ("generic-service", "unknown"):
                symptom_clean = trace.symptom_service.replace("-service", "")
                for f in all_files:
                    if symptom_clean.lower() in f.file_path.lower() and f.file_path.endswith((".java", ".py", ".ts", ".go", ".kt", ".rs")):
                        add_file(f)

        # 3. Tertiary: Filter by evidence service name or error message
        for e in evidence:
            svc = (e.service_name or "").replace("-service", "")
            if svc and svc not in ("generic-service", "unknown"):
                for f in all_files:
                    if svc.lower() in f.file_path.lower() and f.file_path.endswith((".java", ".py", ".ts", ".go", ".kt", ".rs")):
                        add_file(f)

        # Filter out purely generated/test mocks unless needed
        core_files = [f for f in source_files if not any(x in f.file_path.lower() for x in ["mock", "spec", "fixture"])]
        return core_files[:3]
