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

        # Required Schema-Shaped JSON output template with placeholders ONLY
        target_file = source_files[0].file_path if source_files else "<repository-relative-file-path>"
        prompt.append("\nReturn strictly this compact JSON object with no wrapping text:")
        prompt.append(f"""{{
  "root_cause": "<concise summary of actual failure mechanism based on evidence>",
  "root_cause_service": "<actual service where defect exists>",
  "affected_file": "{target_file}",
  "line": 1,
  "repair_summary": "<concise explanation of the fix>",
  "diff": "--- a/{target_file}\\n+++ b/{target_file}\\n@@ -<start_line>,<count> +<start_line>,<count> @@\\n <context_line>\\n+<added_line>\\n-<removed_line>",
  "confidence": 1.0
}}""")
        prompt.append("\nDirectives:")
        prompt.append("- Never invent a file name. Use only files present in the supplied source context.")
        prompt.append("- Never invent a service name. Derive it strictly from the evidence.")
        prompt.append("- Never invent a source location, line number, or symbol. Derive it from the stack trace and source code.")
        prompt.append("- Never invent an endpoint, error, or stack trace.")
        prompt.append("- Never infer a patch from an example or template; derive it strictly from the actual defect.")
        prompt.append("- Use only supplied repository evidence.")
        prompt.append("- If evidence is insufficient or no safe repair can be determined, return no_repair_available.")
        prompt.append("- Every changed file must be justified by the supplied source context.")
        prompt.append("- The unified diff must be complete, syntactically valid, and bounded to the affected file.")

        return "\n".join(prompt)
