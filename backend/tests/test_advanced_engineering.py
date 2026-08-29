import os
import pytest
from app.services.repository_intelligence_service import RepositoryIntelligenceService
from app.services.cross_service_investigator import CrossServiceInvestigator
from app.services.config_guardian_service import ConfigurationGuardianService
from app.services.companion_service import CompanionService
from app.services.approval_policy_engine import ApprovalPolicyEngine
from app.services.notification_service import NotificationService

def test_multi_service_discovery_and_classification(tmp_path):
    # Setup mock microservice repository
    gateway = tmp_path / "gateway"
    gateway.mkdir()
    (gateway / "pom.xml").write_text("<project><dependencies><dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency></dependencies></project>")
    (gateway / "Dockerfile").write_text("FROM openjdk:17\nEXPOSE 8080\n")

    payment = tmp_path / "payment-service"
    payment.mkdir()
    (payment / "pom.xml").write_text("<project><dependencies><dependency><groupId>org.postgresql</groupId><artifactId>postgresql</artifactId></dependency></dependencies></project>")
    (payment / "application.properties").write_text("server.port=8082\nspring.datasource.url=jdbc:postgresql://localhost:5432/payments\n")

    intelligence = RepositoryIntelligenceService.analyze_repository(str(tmp_path))
    
    assert intelligence["architecture_type"] in ["MICROSERVICES", "MONOREPO"]
    assert len(intelligence["services_inventory"]) == 2
    
    svc_names = [s["service_name"] for s in intelligence["services_inventory"]]
    assert "gateway" in svc_names
    assert "payment-service" in svc_names
    
    # Check port & db discovery
    payment_svc = next(s for s in intelligence["services_inventory"] if s["service_name"] == "payment-service")
    assert "PostgreSQL" in payment_svc["databases"]
    assert 8082 in payment_svc["ports"]

def test_cross_service_root_cause_isolation():
    service_graph = {
        "nodes": [
            {"id": "gateway", "name": "Gateway", "type": "service"},
            {"id": "order-service", "name": "OrderService", "type": "service"},
            {"id": "payment-service", "name": "PaymentService", "type": "service"}
        ],
        "edges": [
            {"source": "gateway", "target": "order-service", "type": "http_request"},
            {"source": "order-service", "target": "payment-service", "type": "http_request"}
        ]
    }

    evidence_events = [
        {"service": "Gateway", "status": "PASS", "http_status": 200, "duration": "45ms"},
        {"service": "OrderService", "status": "PASS", "http_status": 200, "duration": "60ms"},
        {
            "service": "PaymentService",
            "status": "FAIL",
            "http_status": 500,
            "duration": "120ms",
            "file": "PaymentService.java",
            "line": 30,
            "message": "NullPointerException: merchant cannot be null"
        }
    ]

    analysis = CrossServiceInvestigator.analyze_cross_service_incident(
        evidence_events=evidence_events,
        service_graph=service_graph,
        failure_input={"service": "Gateway", "http_status": 500}
    )

    assert analysis["symptom"]["service"] == "Gateway"
    assert analysis["root_cause"]["service"] == "PaymentService"
    assert analysis["root_cause"]["file"] == "PaymentService.java"
    assert analysis["root_cause"]["line"] == 30
    assert analysis["is_cross_service"] is True

def test_config_guardian_drift_detection(tmp_path):
    svc_dir = tmp_path / "payment-service"
    svc_dir.mkdir()
    
    # Template requires PAYMENT_TIMEOUT and DATABASE_URL
    (svc_dir / ".env.example").write_text("PAYMENT_TIMEOUT=5000\nDATABASE_URL=postgresql://localhost:5432/db\nAPI_SECRET_KEY=replace_me\n")
    
    # Observed env only has DATABASE_URL
    observed = {"DATABASE_URL": "postgresql://real_db:5432/db"}

    audit = ConfigurationGuardianService.audit_service_configuration(
        repo_path=str(tmp_path),
        service_path="payment-service",
        service_name="payment-service",
        observed_env=observed
    )

    assert audit["status"] == "DRIFT_DETECTED"
    assert audit["drifts_detected"] == 2
    
    drift_keys = [item["key_name"] for item in audit["items"]]
    assert "PAYMENT_TIMEOUT" in drift_keys
    assert "API_SECRET_KEY" in drift_keys
    
    # Verify secret is flagged and recovery proposal contains NO secrets
    secret_item = next(item for item in audit["items"] if item["key_name"] == "API_SECRET_KEY")
    assert secret_item["is_secret"] is True
    assert "never commit secret values" in secret_item["recovery_proposal"].lower()

def test_companion_bounded_context_pack(tmp_path):
    svc_dir = tmp_path / "order-service"
    svc_dir.mkdir()
    (svc_dir / "OrderService.java").write_text("public class OrderService {\n  public void placeOrder() {}\n}\n")
    (svc_dir / "OrderController.java").write_text("public class OrderController {\n  public void postOrder() {}\n}\n")

    pack = CompanionService.assemble_context_pack(
        repo_path=str(tmp_path),
        scope_type="service",
        target_path="order-service"
    )

    assert pack["files_count"] == 2
    assert pack["lines_count"] > 0
    assert pack["scope_type"] == "service"
    assert len(pack["files"]) == 2

def test_companion_explain_mode():
    context_pack = {
        "files": [{"path": "PaymentService.java", "lines": 45, "content": "class PaymentService {}"}]
    }
    explanation = CompanionService.explain_code(context_pack, symbol_name="processPayment")
    
    assert explanation["symbol"] == "processPayment"
    assert len(explanation["potential_failure_points"]) > 0
    assert len(explanation["recommended_guards"]) > 0

def test_approval_policy_evaluation():
    # Low-risk valid patch -> Auto-merge eligible
    low_risk = ApprovalPolicyEngine.evaluate_merge_policy(
        validation_results={"all_passed": True, "status": "VALIDATED"},
        changed_files_count=1,
        affected_services_count=1,
        replay_status="PASS",
        risk_level="LOW"
    )
    assert low_risk["is_auto_merge_eligible"] is True
    assert low_risk["policy_mode"] == "AUTO_MERGE_ELIGIBLE"

    # High-risk / multi-file patch -> Requires human approval
    high_risk = ApprovalPolicyEngine.evaluate_merge_policy(
        validation_results={"all_passed": True, "status": "VALIDATED"},
        changed_files_count=5,
        affected_services_count=3,
        replay_status="PASS",
        risk_level="HIGH"
    )
    assert high_risk["is_auto_merge_eligible"] is False
    assert high_risk["policy_mode"] == "HUMAN_APPROVAL_REQUIRED"
    assert len(high_risk["blocking_reasons"]) > 0

def test_notification_lifecycle():
    notif = NotificationService.emit_notification(
        run_id="run-test-101",
        notification_type="APPROVAL_REQUIRED",
        title="Repair Ready for Approval",
        message="PaymentService patch verified. Human sign-off required.",
        action_url="/runs/run-test-101"
    )

    assert notif["notification_type"] == "APPROVAL_REQUIRED"
    assert NotificationService.get_unread_count() >= 1

    # Mark read
    NotificationService.mark_as_read(notif["id"])
    notifications = NotificationService.get_notifications()
    target = next(n for n in notifications if n["id"] == notif["id"])
    assert target["is_read"] is True
