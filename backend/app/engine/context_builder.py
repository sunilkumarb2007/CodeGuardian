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
        Enforces a maximum of 10 files.
        """
        source_files = []
        
        # 1. Filter by stack trace in evidence
        for e in evidence:
            if e.stack_trace:
                # Example matcher for Java stack trace: at com.example.Class.method(Class.java:42)
                java_trace_match = re.search(r'\(([\w\.]+\.java):\d+\)', e.stack_trace)
                if java_trace_match:
                    file_name = java_trace_match.group(1)
                    source_files.extend([f for f in all_files if f.file_path.endswith(file_name)])
        
        # 2. Filter by trace root cause candidate if no stack trace match
        if not source_files and trace and trace.root_cause_candidate and trace.root_cause_candidate != "generic-service":
            source_files = [f for f in all_files if trace.root_cause_candidate in f.file_path]

        # 3. Filter by incident description / evidence service if still empty
        if not source_files:
            for e in evidence:
                target_service = e.service_name.replace("-service", "") if e.service_name else ""
                if target_service:
                    source_files.extend([f for f in all_files if target_service.lower() in f.file_path.lower() and f.file_path.endswith((".java", ".ts", ".py", ".go"))])

        # 4. Also include related test files for coordinated repair
        test_files = [f for f in all_files if ("test" in f.file_path.lower() or "spec" in f.file_path.lower()) and any(sf.file_path.split("/")[-1].replace(".java", "") in f.file_path for sf in source_files)]
        source_files.extend(test_files[:2])

        # 5. If still empty, select only core service files (up to 3)
        if not source_files:
            source_files = [f for f in all_files if f.file_path.endswith((".java", ".py", ".ts")) and not any(x in f.file_path.lower() for x in ["test", "mock", "stub"])][:3]
            
        # Deduplicate and limit to 2 focused source files
        unique_files = {f.id: f for f in source_files if not any(x in f.file_path.lower() for x in ["test", "mock", "spec"])}
        return list(unique_files.values())[:2]
