from app.db import models
from app.schemas.memory import MemorySearchResponse

class InvestigationPromptBuilder:
    @staticmethod
    def build_prompt(
        incident: models.Incident,
        evidence: list[models.EvidenceEvent],
        trace: models.FailureTrace,
        memory_response: MemorySearchResponse,
        source_files: list[models.RepositoryFile],
        architecture: dict | None = None
    ) -> str:
        prompt = []
        
        # 1. System Role and Instructions
        prompt.append("=== SYSTEM ROLE ===")
        prompt.append("You are CodeGuardian's source-level investigation engine.")
        prompt.append("OBJECTIVE: Investigate the supplied failure using evidence, reconstructed failure chain, historical memory, and current source code.")
        prompt.append("CONSTRAINTS:")
        prompt.append("- Use only supplied evidence.")
        prompt.append("- Do not invent runtime facts.")
        prompt.append("- Do not invent source files.")
        prompt.append("- Do not assume a historical patch applies automatically. It is merely a historical reference.")
        prompt.append("- Produce a patch candidate only when sufficient source context exists.")
        prompt.append("- Do not claim validation.")
        prompt.append("- Do not claim execution.")
        prompt.append("- Do not claim deployment.")
        
        if architecture:
            lang = (architecture.get("language") or "unknown").upper()
            prompt.append(f"\nCRITICAL ARCHITECTURE CONSTRAINT: You are investigating a repository whose detected language is {lang}.")
            prompt.append(f"Your patch MUST use the detected repository language ({lang}).")
            prompt.append(f"Do not generate code in other languages (e.g. do not generate Python code for a Java repository).")
            prompt.append(f"Only modify files that exist in the supplied repository context.")
            prompt.append(f"The patch must reference actual files from the repository.")
            prompt.append(f"Do not invent filenames, classes, or methods.")
            prompt.append(f"Do not change build systems.")
            prompt.append(f"Do not change unrelated files.")
            prompt.append(f"The patch remains UNVALIDATED until CodeGuardian Replay, Build, Tests and Validation succeed.")
            
        prompt.append("\n=== CONTEXT PRIORITY ===")
        prompt.append("You MUST prioritize context sources in the following order:")
        prompt.append("1. Actual repository architecture (Language, Framework)")
        prompt.append("2. Actual failure output & stack trace")
        prompt.append("3. Actual source code context provided")
        prompt.append("4. GhostTrace result")
        prompt.append("5. Historical FailureMemory")
        prompt.append("\nWARNING: Historical FailureMemory is REFERENCE ONLY. If the historical memory references a different language (e.g. a Python file) but the repository architecture is Java, you MUST ignore the historical memory's language and write a Java patch.")
        
        # 2. Engineering Data
        prompt.append("\n=== ENGINEERING DATA ===")
        if architecture:
            prompt.append("\n[Architecture]")
            prompt.append(f"Language: {architecture.get('language')}")
            prompt.append(f"Framework: {architecture.get('framework')}")
            prompt.append(f"Build System: {architecture.get('build_system')}")
            prompt.append(f"Test Framework: {architecture.get('test_framework')}")
        
        prompt.append("\n[Incident]")
        prompt.append(f"Title: {incident.title}")
        prompt.append(f"Description: {incident.description}")
        prompt.append(f"Status: {incident.status}")
        
        prompt.append("\n[Evidence]")
        for e in evidence:
            prompt.append(f"- [{e.service_name}] {e.event_type} {e.http_method} {e.endpoint} -> {e.status_code} ({e.error_code}): {e.error_message}")
            if e.stack_trace:
                prompt.append(f"  StackTrace: {e.stack_trace}")
                
        prompt.append("\n[GhostTrace]")
        prompt.append(f"Symptom Service: {trace.symptom_service}")
        prompt.append(f"Root Cause Candidate: {trace.root_cause_candidate}")
        prompt.append(f"Reasoning Summary: {trace.reasoning_summary}")
        
        prompt.append("\n[Memory]")
        if memory_response.match_status == "match_found" and memory_response.matches:
            best_match = memory_response.matches[0]
            prompt.append(f"HISTORICAL ENGINEERING KNOWLEDGE FOUND (Match Score: {best_match.similarity_score})")
            prompt.append(f"Previous Error Pattern: {best_match.memory.error_pattern}")
            prompt.append(f"Previous Root Cause: {best_match.memory.root_cause}")
            prompt.append(f"Previous Code Change: {best_match.memory.code_change}")
            prompt.append("Instruction: Use this historical incident as a reference pattern. Determine whether it applies to the current source code and context. Do NOT blindly copy this patch.")
        else:
            prompt.append("No relevant historical memory found.")
            
        prompt.append("\n[Source Files]")
        if not source_files:
            prompt.append("SOURCE_CONTEXT_UNAVAILABLE")
        else:
            for sf in source_files:
                prompt.append(f"\n--- File: {sf.file_path} ---")
                prompt.append(sf.source_snapshot or "Empty file")
                prompt.append("--------------------------")
                
        # 3. Task
        prompt.append("\n=== TASK ===")
        prompt.append("1. Explain the likely root cause.")
        prompt.append("2. Identify the affected source location.")
        prompt.append("3. Explain the causal relationship.")
        prompt.append("4. Compare historical fix if available. Rate applicability (HIGH, MEDIUM, LOW, or REFERENCE_ONLY).")
        prompt.append("5. Propose a repair plan with specific steps, risk assessment, and expected behavior.")
        prompt.append("6. Produce a structured patch candidate.")
        prompt.append("   - IMPORTANT: If your fix changes the expected behavior of the system, you MUST also include a patch for the corresponding unit tests to reflect the new behavior.")
        prompt.append("7. State assumptions.")
        prompt.append("8. State what must be verified later.")
        
        prompt.append("\n=== STRICT GUIDELINES ===")
        prompt.append("- NO CHAIN OF THOUGHT: Do not output private reasoning, 'thinking steps', or 'let me think deeply'. Provide only concise, evidence-backed engineering conclusions.")
        prompt.append("- EXACT SCHEMA: You must return a strict JSON object that perfectly matches the following schema:")
        prompt.append("""
{
  "status": "completed",
  "root_cause": {
    "service": "string",
    "summary": "string",
    "affected_file": "string",
    "location": "string",
    "confidence": 1.0,
    "failure_mechanism": "string"
  },
  "historical_reference": {
    "found": true,
    "memory_status": "string",
    "applicability": "string"
  },
  "repair_plan": {
    "steps": [{"action": "string", "description": "string"}],
    "risk": "string",
    "expected_behavior": "string"
  },
  "patch_candidate": {
    "status": "unvalidated",
    "files_changed": ["string"],
    "diff": "string",
    "explanation": "string"
  },
  "verification_requirements": ["string"],
  "assumptions": ["string"],
  "evidence_used": ["string"]
}
""")
        
        return "\n".join(prompt)
