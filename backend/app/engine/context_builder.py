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
        if not source_files and trace and trace.root_cause_candidate:
            source_files = [f for f in all_files if trace.root_cause_candidate in f.file_path]
            
        # Deduplicate and limit to 10 files
        unique_files = {f.id: f for f in source_files}
        return list(unique_files.values())[:10]
