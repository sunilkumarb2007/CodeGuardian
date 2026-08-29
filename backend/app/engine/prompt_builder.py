from app.db import models
from app.schemas.memory import MemorySearchResponse
from typing import List, Optional

class InvestigationPromptBuilder:
    @staticmethod
    def build_prompt(
        incident: models.Incident,
        evidence: list[models.EvidenceEvent],
        trace: models.FailureTrace,
        memory_response: MemorySearchResponse,
        source_files: list[models.RepositoryFile],
        architecture: dict | None = None,
        prior_failure_evidence: Optional[List[dict]] = None
    ) -> str:
        prompt = []
        
        # 1. System Role and Task
        prompt.append("You are CodeGuardian automated program repair engine.")
        prompt.append("Return ONLY valid JSON matching the supplied schema.")
        prompt.append("Do not include markdown.")
        prompt.append("Do not include commentary.")
        prompt.append("Do not repeat the source code.")
        prompt.append("Keep every explanation concise.")
        prompt.append("The diff must be complete.")
        prompt.append("If a repair cannot be produced safely, return a valid no_repair_available result rather than incomplete JSON.")
        
        lang = (architecture.get("language") or "Java") if architecture else "Java"
        prompt.append(f"\nLanguage: {lang}")
        prompt.append(f"Incident: {incident.title} - {incident.description}")
        
        # Evidence (bounded)
        prompt.append("\n[Evidence]")
        for e in evidence[:3]:
            prompt.append(f"- {e.service_name} {e.event_type} {e.error_message}")
            if e.stack_trace:
                # Truncate stack trace to first 5 lines to preserve token budget
                stack_lines = [line.strip() for line in e.stack_trace.strip().splitlines() if line.strip()][:5]
                prompt.append("  Stack:\n    " + "\n    ".join(stack_lines))
                
        # GhostTrace root cause candidate
        if trace and trace.root_cause_candidate:
            prompt.append(f"\nGhostTrace Candidate: {trace.root_cause_candidate} ({trace.reasoning_summary or ''})")

        # Memory match if relevant
        if memory_response and getattr(memory_response, "match_status", None) == "direct_match":
            prompt.append("\n[Historical Memory Match: Confirmed fix exists in memory]")

        # Prior failure feedback if any
        if prior_failure_evidence:
            prompt.append("\n[Prior Attempt Feedback]")
            for pf in prior_failure_evidence[-2:]:
                prompt.append(f"- Attempt {pf.get('attempt')}: {pf.get('stage')} error: {pf.get('error')}")

        # Source files (strictly bounded to failing source context)
        prompt.append("\n[Source Code]")
        for sf in source_files[:2]:
            prompt.append(f"File: {sf.file_path}")
            content = sf.source_snapshot or "Empty"
            lines = content.splitlines()
            if len(lines) > 40:
                target_line = 30
                for e in evidence:
                    if e.stack_trace and ":" in e.stack_trace:
                        import re
                        m = re.search(r":(\d+)\)", e.stack_trace)
                        if m:
                            target_line = int(m.group(1))
                            break
                start_l = max(0, target_line - 15)
                end_l = min(len(lines), target_line + 15)
                content = f"// lines {start_l + 1}-{end_l}\n" + "\n".join(lines[start_l:end_l])
            prompt.append(content)
            prompt.append("---")

        # Required Minimal JSON output format
        target_file = source_files[0].file_path if source_files else "PaymentService.java"
        prompt.append("\nReturn strictly this compact JSON object with no wrapping text:")
        prompt.append(f"""{{
  "root_cause": "Null dereference when merchant is not found in repository",
  "root_cause_service": "payment-service",
  "affected_file": "{target_file}",
  "line": 30,
  "repair_summary": "Add null check for merchant",
  "diff": "--- a/{target_file}\\n+++ b/{target_file}\\n@@ -24,3 +24,5 @@\\n+        if (merchant == null) {{\\n+            throw new IllegalStateException(\\"Merchant not found\\");\\n+        }}",
  "confidence": 1.0
}}""")

        return "\n".join(prompt)
