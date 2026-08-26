"""Deterministic agent script for Demo Mode.

Each stage expands into several engineering events (command, output, finding,
next action). No language model is involved: the sequence is prepared and the
values are filled from the data the stage actually produced.
"""

from typing import Any, Dict, List, Optional

SERVICE_FILE = "payment-service/src/main/java/com/codeguardian/paymentservice/PaymentProcessingService.java"
REPOSITORY_FILE = "payment-service/src/main/java/com/codeguardian/paymentservice/DemoPaymentRepository.java"
CONTROLLER_FILE = "payment-service/src/main/java/com/codeguardian/paymentservice/PaymentController.java"


def _event(
    event_type: str,
    title: str,
    *,
    command: Optional[str] = None,
    output: Optional[str] = None,
    description: Optional[str] = None,
    duration_ms: int = 800,
    related_file: Optional[str] = None,
    next_action: Optional[str] = None,
    status: str = "completed",
) -> Dict[str, Any]:
    return {
        "type": event_type,
        "title": title,
        "command": command,
        "output": output,
        "description": description,
        "duration_ms": duration_ms,
        "related_file": related_file,
        "next_action": next_action,
        "status": status,
    }


def build_stage_events(stage: str, results: Dict[str, Any]) -> List[Dict[str, Any]]:
    inspection = results.get("inspection") or {}
    architecture = results.get("architecture") or {}
    incident = results.get("failure_detection") or {}
    evidence = results.get("evidence") or []
    trace = results.get("ghosttrace") or {}
    memory = results.get("memory") or {}
    investigation = results.get("investigation") or {}
    patch = results.get("patch") or {}
    changed_files = results.get("changed_files") or []
    replay = results.get("replay") or {}
    build = results.get("build") or {}
    tests = results.get("tests") or {}
    validation = results.get("validation") or {}
    delivery = results.get("delivery") or {}
    memory_update = results.get("memory_update") or {}
    stack_trace = results.get("stack_trace") or {}
    repository = results.get("repository") or {}

    if stage == "repository":
        return [
            _event(
                "system",
                "Investigation started",
                description="Preparing the prepared repository context.",
                duration_ms=600,
                next_action="Resolve the repository target.",
            ),
            _event(
                "tool",
                "Resolve repository",
                command="inspect repository",
                output="\n".join(
                    filter(
                        None,
                        [
                            f"Repository: {repository.get('name')}",
                            f"URL: {repository.get('url')}",
                            f"Default branch: {repository.get('default_branch')}",
                            f"Access: {repository.get('access_status')}",
                        ],
                    )
                ),
                duration_ms=900,
                next_action="Index the source tree.",
            ),
        ]

    if stage == "inspection":
        files = inspection.get("files") or []
        return [
            _event(
                "tool",
                "Index source tree",
                command="index source tree",
                output=f"{inspection.get('files_scanned', len(files))} files indexed",
                duration_ms=1100,
                next_action="Detect the application architecture.",
            ),
            _event(
                "observation",
                "Repository map built",
                description="Services discovered: gateway, order-service, payment-service.",
                duration_ms=500,
                next_action="Detect language, framework and build tool.",
            ),
        ]

    if stage == "architecture":
        return [
            _event(
                "tool",
                "Detect architecture",
                command="detect architecture",
                output="\n".join(
                    filter(
                        None,
                        [
                            architecture.get("language"),
                            architecture.get("framework"),
                            architecture.get("build_tool"),
                        ],
                    )
                ),
                duration_ms=800,
                next_action="Look for a reported failure.",
            )
        ]

    if stage == "failure_detection":
        return [
            _event(
                "evidence",
                "Failure discovered",
                command="detect failure",
                output="\n".join(
                    filter(
                        None,
                        [
                            f"HTTP {incident.get('observed_status_code')}",
                            incident.get("fingerprint"),
                            incident.get("symptom_service"),
                            f"{incident.get('http_method')} {incident.get('endpoint')}",
                        ],
                    )
                ),
                duration_ms=1000,
                next_action="Collect correlated evidence.",
            )
        ]

    if stage == "evidence":
        return [
            _event(
                "tool",
                "Collect failure evidence",
                command="collect failure evidence",
                output=f"{len(evidence)} evidence events correlated by request id {incident.get('request_id')}",
                duration_ms=1000,
                next_action="Analyse the captured stack trace.",
            ),
            _event(
                "tool",
                "Analyse stack trace",
                command="analyze stack trace",
                output=(stack_trace.get("content") or "No stack trace captured").splitlines()[0]
                if stack_trace.get("content")
                else "No stack trace captured",
                related_file=SERVICE_FILE,
                duration_ms=900,
                next_action="Reconstruct the request path.",
            ),
        ]

    if stage == "ghosttrace":
        nodes = trace.get("nodes") or []
        path = " -> ".join(
            [node.get("service_name") or node.get("node_type") or "?" for node in nodes]
        )
        return [
            _event(
                "trace",
                "Reconstruct failure graph",
                command="reconstruct failure graph",
                output=path or "No trace nodes reported",
                duration_ms=1300,
                next_action="Separate symptom from root cause.",
            ),
            _event(
                "observation",
                "Symptom is not the root cause",
                description=(
                    f"Symptom service {trace.get('symptom_service')}; "
                    f"root cause candidate {trace.get('root_cause_candidate')}."
                ),
                duration_ms=600,
                next_action="Search verified failure memory.",
            ),
        ]

    if stage == "memory":
        similarity = memory.get("similarity")
        return [
            _event(
                "memory",
                "Search verified memory",
                command="search verified memory",
                output=(
                    f"1 verified match ({round(similarity * 100)}% similarity)"
                    if memory.get("match_found") and similarity is not None
                    else ("1 verified match" if memory.get("match_found") else "No verified match")
                ),
                duration_ms=1000,
                next_action="Open the implicated source files.",
            )
        ]

    if stage == "investigation":
        return [
            _event(
                "source",
                "Open implicated source",
                command=f"open {SERVICE_FILE}",
                output="Repository lookup result is dereferenced before validation.",
                description="The root stack trace frame points at charge() in this file.",
                related_file=SERVICE_FILE,
                duration_ms=1200,
                next_action="Inspect the repository lookup.",
            ),
            _event(
                "source",
                "Open repository lookup",
                command=f"open {REPOSITORY_FILE}",
                output="findByOrderId() can return null for unknown orders.",
                description="The repository lookup feeds the variable that is dereferenced.",
                related_file=REPOSITORY_FILE,
                duration_ms=900,
                next_action="Confirm the request context.",
            ),
            _event(
                "source",
                "Open request entry point",
                command=f"open {CONTROLLER_FILE}",
                output="POST /payments/charge routes into PaymentProcessingService.charge().",
                description="The controller establishes the failing request context.",
                related_file=CONTROLLER_FILE,
                duration_ms=800,
                next_action="State the root cause.",
            ),
            _event(
                "investigation",
                "Root cause identified",
                description=investigation.get("root_cause"),
                output="\n".join(
                    filter(
                        None,
                        [
                            f"OBSERVATION: {investigation.get('observation')}"
                            if investigation.get("observation")
                            else None,
                            f"EVIDENCE: {investigation.get('evidence')}"
                            if investigation.get("evidence")
                            else None,
                            f"HYPOTHESIS: {investigation.get('hypothesis')}"
                            if investigation.get("hypothesis")
                            else None,
                            f"DECISION: {investigation.get('decision')}"
                            if investigation.get("decision")
                            else None,
                        ],
                    )
                ),
                duration_ms=1400,
                next_action="Prepare a minimal repair.",
            ),
        ]

    if stage == "patch":
        return [
            _event(
                "patch",
                "Prepare repair",
                command="prepare repair",
                output=f"{len(changed_files)} file(s) changed on {patch.get('branch_name')}",
                related_file=(changed_files[0].get("path") if changed_files else None),
                duration_ms=1300,
                next_action="Hand the changed files to review.",
            ),
            _event(
                "review",
                "Change ready for review",
                output="\n".join(item.get("name", "") for item in changed_files) or "No changed files",
                status="waiting",
                duration_ms=400,
                next_action="Verify patch compatibility.",
            ),
        ]

    if stage == "compatibility":
        compatibility = results.get("compatibility") or {}
        return [
            _event(
                "tool",
                "Verify patch compatibility",
                command="verify patch compatibility",
                output="\n".join(
                    filter(
                        None,
                        [
                            f"Language: {compatibility.get('language')}",
                            f"Source context: {compatibility.get('source_context')}",
                            f"Path safety: {compatibility.get('path_safety')}",
                            f"Secrets: {compatibility.get('secrets')}",
                        ],
                    )
                ),
                duration_ms=800,
                next_action="Replay the original failure.",
            )
        ]

    if stage == "replay":
        original = replay.get("original") or {}
        patched = replay.get("patched") or {}
        return [
            _event(
                "replay",
                "Replay original",
                command="replay original",
                output=f"HTTP {original.get('actual_status_code')} / {original.get('result')}",
                duration_ms=1200,
                next_action="Replay the patched execution.",
            ),
            _event(
                "replay",
                "Replay patched",
                command="replay patched",
                output=f"HTTP {patched.get('actual_status_code')} / {patched.get('result')}",
                duration_ms=1200,
                next_action="Verify the build.",
            ),
        ]

    if stage == "build":
        return [
            _event(
                "tool",
                "Verify build",
                command=build.get("command") or "verify build",
                output=build.get("output"),
                duration_ms=1000,
                next_action="Run the test suite.",
            )
        ]

    if stage == "tests":
        summary = tests.get("summary") or {}
        return [
            _event(
                "tool",
                "Verify tests",
                command="verify tests",
                output=tests.get("output")
                or ", ".join(f"{key}: {value}" for key, value in summary.items()),
                duration_ms=1000,
                next_action="Run the validation gates.",
            )
        ]

    if stage == "validation":
        gates = validation.get("gates") or []
        passed = sum(1 for gate in gates if gate.get("result") == "PASS")
        return [
            _event(
                "validation",
                "Validate repair",
                command="validate repair",
                output=f"{passed}/{len(gates)} gates passed" if gates else "No gates reported",
                duration_ms=1100,
                next_action="Request human approval.",
            )
        ]

    if stage == "approval":
        return [
            _event(
                "approval",
                "Waiting for human approval",
                description="Delivery is blocked until a reviewer approves the patch.",
                status="waiting",
                duration_ms=0,
                next_action="Reviewer decision required.",
            )
        ]

    if stage == "delivery":
        git_events = [
            _event(
                "delivery",
                entry["command"],
                command=entry["command"],
                output=entry["output"],
                duration_ms=700,
                next_action="Continue the delivery workflow.",
            )
            for entry in (delivery.get("git_commands") or [])
        ]
        return git_events + [
            _event(
                "delivery",
                "Prepare pull request",
                command="prepare pull request",
                output="\n".join(
                    filter(
                        None,
                        [
                            f"Base: {delivery.get('base')}",
                            f"Compare: {delivery.get('branch')}",
                            f"Commit: {delivery.get('commit_short_sha')}",
                            delivery.get("pull_request"),
                        ],
                    )
                ),
                duration_ms=900,
                next_action="Update engineering memory.",
            )
        ]

    if stage == "memory_update":
        return [
            _event(
                "memory",
                "Update engineering memory",
                command="update engineering memory",
                output="\n".join(
                    filter(
                        None,
                        [
                            memory_update.get("error_fingerprint"),
                            f"Status: {memory_update.get('status')}",
                        ],
                    )
                ),
                duration_ms=800,
                next_action="Investigation complete.",
            )
        ]

    return []
