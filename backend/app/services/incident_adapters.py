"""
Provider Adapter Architecture for CodeGuardian Autonomous Production Engineer.
Normalizes heterogeneous incident signals from Render, Vercel, AWS, Custom Webhooks,
and OpenTelemetry into a standard NormalizedIncident structure.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


@dataclass
class NormalizedIncident:
    repository: str
    repository_id: Optional[str] = None
    branch: Optional[str] = "main"
    commit_sha: Optional[str] = None
    environment: Optional[str] = "production"
    provider: Optional[str] = "webhook"
    project: Optional[str] = None
    deployment_id: Optional[str] = None
    service: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    exception: Optional[str] = None
    message: Optional[str] = None
    stack_trace: Optional[str] = None
    timestamp: Optional[datetime] = None
    source: Optional[str] = "webhook"
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_payload: Dict[str, Any] = field(default_factory=dict)


class IncidentSourceAdapter:
    """Base class for all incident source adapters."""
    def normalize(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> NormalizedIncident:
        raise NotImplementedError


class CustomWebhookAdapter(IncidentSourceAdapter):
    """Handles direct / standard webhook payloads."""
    def normalize(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> NormalizedIncident:
        ts = payload.get("timestamp")
        if isinstance(ts, str):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                dt = datetime.now(timezone.utc)
        elif isinstance(ts, datetime):
            dt = ts
        else:
            dt = datetime.now(timezone.utc)

        return NormalizedIncident(
            repository=payload.get("repository", ""),
            repository_id=str(payload["repository_id"]) if payload.get("repository_id") else None,
            branch=payload.get("branch", "main"),
            commit_sha=payload.get("commit_sha"),
            environment=payload.get("environment", "production"),
            provider=payload.get("provider", "custom"),
            project=payload.get("project"),
            deployment_id=payload.get("deployment_id"),
            service=payload.get("service"),
            endpoint=payload.get("endpoint"),
            status_code=payload.get("status_code"),
            request_id=payload.get("request_id"),
            trace_id=payload.get("trace_id"),
            span_id=payload.get("span_id"),
            exception=payload.get("exception"),
            message=payload.get("message"),
            stack_trace=payload.get("stack_trace"),
            timestamp=dt,
            source=payload.get("source", "webhook"),
            metadata=payload.get("metadata", {}),
            raw_payload=payload,
        )


class RenderAdapter(IncidentSourceAdapter):
    """
    Normalizes Render deployment failures, alert webhooks, and log events.
    Render sends notifications with event type: 'deploy.failed', 'service.unhealthy', etc.
    """
    def normalize(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> NormalizedIncident:
        service_data = payload.get("service", {})
        deploy_data = payload.get("deploy", {})
        commit_data = deploy_data.get("commit", {})

        repo_url = service_data.get("repo") or payload.get("repoUrl") or payload.get("repository") or ""
        # Extract owner/repo from URL or string
        repo = repo_url
        if "github.com/" in repo_url:
            repo = repo_url.split("github.com/")[-1].replace(".git", "")

        service_name = service_data.get("name") or payload.get("serviceName") or "render-service"
        commit_sha = commit_data.get("id") or deploy_data.get("commitId") or payload.get("commitSha")
        branch = service_data.get("branch") or deploy_data.get("branch") or "main"
        
        event_type = payload.get("type") or payload.get("event") or "deploy.failed"
        
        err = payload.get("error")
        if isinstance(err, dict):
            exception = err.get("name") or err.get("type") or event_type
            message = err.get("message") or payload.get("message") or deploy_data.get("status") or f"Render alert: {event_type}"
            stack = err.get("stackTrace") or err.get("stack") or payload.get("logs") or payload.get("details") or ""
            status_code = err.get("statusCode") or payload.get("status_code", 500)
        elif isinstance(err, str):
            exception = err
            message = payload.get("message") or deploy_data.get("status") or f"Render alert: {event_type}"
            stack = payload.get("logs") or payload.get("details") or ""
            status_code = payload.get("status_code", 500)
        else:
            exception = event_type
            message = payload.get("message") or deploy_data.get("status") or f"Render alert: {event_type}"
            stack = payload.get("logs") or payload.get("details") or ""
            status_code = payload.get("status_code", 500)

        return NormalizedIncident(
            repository=repo,
            branch=branch,
            commit_sha=commit_sha,
            environment=service_data.get("env", "production"),
            provider="render",
            project=service_data.get("serviceDetails", {}).get("parentServiceId"),
            deployment_id=deploy_data.get("id"),
            service=service_name,
            endpoint=payload.get("endpoint"),
            status_code=status_code,
            request_id=payload.get("request_id"),
            trace_id=payload.get("trace_id"),
            exception=exception,
            message=message,
            stack_trace=stack,
            timestamp=datetime.now(timezone.utc),
            source="render",
            metadata={"render_event_type": event_type, "service_id": service_data.get("id")},
            raw_payload=payload,
        )


class VercelAdapter(IncidentSourceAdapter):
    """
    Normalizes Vercel deployment/error events and log drains.
    """
    def normalize(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> NormalizedIncident:
        project_name = payload.get("project", {}).get("name") or payload.get("projectName") or "vercel-app"
        repo_data = payload.get("deployment", {}).get("meta", {})
        repo = repo_data.get("githubRepo") or repo_data.get("repo") or payload.get("repository", "")
        commit_sha = repo_data.get("githubCommitSha") or payload.get("deployment", {}).get("meta", {}).get("commit")

        return NormalizedIncident(
            repository=repo,
            branch=repo_data.get("githubCommitRef", "main"),
            commit_sha=commit_sha,
            environment=payload.get("deployment", {}).get("target", "production"),
            provider="vercel",
            project=project_name,
            deployment_id=payload.get("deployment", {}).get("id"),
            service=project_name,
            endpoint=payload.get("path") or payload.get("url"),
            status_code=payload.get("statusCode", 500),
            request_id=payload.get("requestId") or payload.get("id"),
            exception=payload.get("errorType") or "VercelRuntimeError",
            message=payload.get("errorMessage") or payload.get("message") or "Vercel execution failure",
            stack_trace=payload.get("stack") or payload.get("logs") or "",
            timestamp=datetime.now(timezone.utc),
            source="vercel",
            metadata=payload.get("deployment", {}),
            raw_payload=payload,
        )


class AWSAdapter(IncidentSourceAdapter):
    """
    Normalizes AWS CloudWatch Alarms, SNS notifications, Lambda errors, and ECS events.
    """
    def normalize(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> NormalizedIncident:
        # Check if wrapped in SNS
        msg = payload
        if "Message" in payload and isinstance(payload["Message"], str):
            import json
            try:
                msg = json.loads(payload["Message"])
            except Exception:
                msg = {"message": payload["Message"]}

        alarm_name = msg.get("AlarmName") or payload.get("alarm_name") or "AWS CloudWatch Alarm"
        reason = msg.get("NewStateReason") or msg.get("message") or "AWS Threshold Exceeded"
        service = msg.get("service") or payload.get("service") or msg.get("Namespace") or "aws-service"
        repo = payload.get("repository") or msg.get("repository", "")

        return NormalizedIncident(
            repository=repo,
            branch=payload.get("branch", "main"),
            commit_sha=payload.get("commit_sha"),
            environment=payload.get("environment", "production"),
            provider="aws",
            project=msg.get("AWSAccountId"),
            service=service,
            endpoint=payload.get("endpoint"),
            status_code=payload.get("status_code", 500),
            exception=alarm_name,
            message=reason,
            stack_trace=payload.get("stack_trace") or msg.get("stack_trace", ""),
            timestamp=datetime.now(timezone.utc),
            source="aws",
            metadata={"alarm_name": alarm_name, "raw_aws": msg},
            raw_payload=payload,
        )


class OpenTelemetryAdapter(IncidentSourceAdapter):
    """
    Normalizes OpenTelemetry trace / span error exports.
    """
    def normalize(self, payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> NormalizedIncident:
        service_name = payload.get("resourceSpans", [{}])[0].get("resource", {}).get("attributes", {}).get("service.name") or payload.get("service_name") or "otel-service"
        
        # Extract span error details if present
        span = payload.get("span", {})
        status = span.get("status", {})
        error_msg = status.get("message") or payload.get("error_message") or "OpenTelemetry Error Span"
        trace_id = span.get("traceId") or payload.get("trace_id")
        span_id = span.get("spanId") or payload.get("span_id")
        
        return NormalizedIncident(
            repository=payload.get("repository", ""),
            branch=payload.get("branch", "main"),
            commit_sha=payload.get("commit_sha"),
            environment=payload.get("environment", "production"),
            provider="opentelemetry",
            service=service_name,
            endpoint=span.get("name") or payload.get("endpoint"),
            status_code=payload.get("status_code", 500),
            trace_id=trace_id,
            span_id=span_id,
            exception=payload.get("exception") or "OTelSpanError",
            message=error_msg,
            stack_trace=payload.get("stack_trace", ""),
            timestamp=datetime.now(timezone.utc),
            source="opentelemetry",
            metadata={"trace_id": trace_id, "span_id": span_id},
            raw_payload=payload,
        )


def get_adapter_for_source(source: Optional[str]) -> IncidentSourceAdapter:
    """Factory helper returning appropriate adapter."""
    src = (source or "webhook").lower().strip()
    if src == "render":
        return RenderAdapter()
    elif src == "vercel":
        return VercelAdapter()
    elif src in ("aws", "cloudwatch", "sns"):
        return AWSAdapter()
    elif src in ("opentelemetry", "otel"):
        return OpenTelemetryAdapter()
    return CustomWebhookAdapter()
