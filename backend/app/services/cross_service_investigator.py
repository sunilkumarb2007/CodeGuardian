import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class CrossServiceInvestigator:
    """
    Cross-Service Root Cause & Propagation Analyzer.
    Connects GhostTrace causal mapping with Multi-Service Dependency Graphs.
    Distinguishes WHERE the failure appeared (symptom) from WHERE it originated (root cause).
    """

    @classmethod
    def analyze_cross_service_incident(
        cls,
        evidence_events: List[Dict[str, Any]],
        service_graph: Dict[str, Any],
        failure_input: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Reconstructs the end-to-end incident flow across microservices.
        """
        nodes = service_graph.get("nodes", [])
        known_services = [n["name"] for n in nodes if n.get("type") == "service"]
        
        # 1. Identify symptom service (ingress error)
        symptom_service = "Unknown"
        symptom_status = 500
        symptom_endpoint = "Unknown"
        
        if failure_input:
            symptom_service = failure_input.get("service") or failure_input.get("source_service") or "Gateway"
            symptom_status = failure_input.get("http_status") or 500
            symptom_endpoint = failure_input.get("endpoint") or failure_input.get("path") or "/api"

        # 2. Build ordered propagation path from evidence events
        propagation_path = []
        root_cause_candidate = None
        root_cause_file = None
        root_cause_line = None
        root_cause_error = "Unknown error"

        for ev in evidence_events:
            svc_name = ev.get("service") or ev.get("component") or "Unknown"
            status = ev.get("status") or "PASS"
            duration = ev.get("duration") or "0ms"
            is_error = status == "FAIL" or "error" in str(ev.get("message", "")).lower() or ev.get("http_status", 200) >= 500

            propagation_path.append({
                "service": svc_name,
                "status": "FAIL" if is_error else "PASS",
                "http_status": ev.get("http_status", 500 if is_error else 200),
                "duration": duration,
                "message": ev.get("message", ""),
                "is_root_cause": False
            })

            if is_error:
                root_cause_candidate = svc_name
                root_cause_file = ev.get("file") or ev.get("source_file")
                root_cause_line = ev.get("line") or ev.get("source_line")
                root_cause_error = ev.get("message") or ev.get("exception") or "Unhandled runtime exception"

        # If no events found but failure_input exists
        if not propagation_path and failure_input:
            root_cause_candidate = failure_input.get("service") or symptom_service
            root_cause_file = failure_input.get("source_file")
            root_cause_line = failure_input.get("source_line")
            root_cause_error = failure_input.get("message") or "Runtime crash"
            propagation_path.append({
                "service": root_cause_candidate,
                "status": "FAIL",
                "http_status": symptom_status,
                "duration": "0ms",
                "message": root_cause_error,
                "is_root_cause": True
            })

        # Mark the last failing node in the propagation chain as the root cause
        if propagation_path:
            for p in reversed(propagation_path):
                if p["status"] == "FAIL":
                    p["is_root_cause"] = True
                    root_cause_candidate = p["service"]
                    break

        # 3. Calculate affected upstream & downstream services
        upstream_services = []
        downstream_services = []
        edges = service_graph.get("edges", [])

        if root_cause_candidate:
            for edge in edges:
                if edge.get("target") == root_cause_candidate.lower().replace("_", "-"):
                    upstream_services.append(edge.get("source"))
                if edge.get("source") == root_cause_candidate.lower().replace("_", "-"):
                    downstream_services.append(edge.get("target"))

        return {
            "symptom": {
                "service": symptom_service,
                "http_status": symptom_status,
                "endpoint": symptom_endpoint,
                "description": f"HTTP {symptom_status} returned at {symptom_service}"
            },
            "root_cause": {
                "service": root_cause_candidate or symptom_service,
                "file": root_cause_file,
                "line": root_cause_line,
                "error": root_cause_error,
                "confidence": 0.96 if root_cause_file else 0.85
            },
            "propagation_path": propagation_path,
            "upstream_services": list(set(upstream_services)),
            "downstream_services": list(set(downstream_services)),
            "affected_services": list(set([p["service"] for p in propagation_path if p["status"] == "FAIL"])),
            "is_cross_service": len(set([p["service"] for p in propagation_path])) > 1
        }
