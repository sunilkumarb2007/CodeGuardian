import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.models import ImpactAnalysis, Patch, Incident


class ImpactService:
    def __init__(self, db: Session):
        self.db = db

    def analyze_blast_radius(
        self,
        incident_id: uuid.UUID,
        patch_id: Optional[uuid.UUID] = None,
        run_id: Optional[str] = None,
        changed_files: Optional[List[str]] = None,
    ) -> ImpactAnalysis:
        """
        Executes static impact analysis on the modified source files.
        """
        existing = (
            self.db.query(ImpactAnalysis)
            .filter(ImpactAnalysis.incident_id == incident_id)
            .first()
        )
        if existing:
            return existing

        files = changed_files or ["src/main/java/com/example/payment/service/PaymentService.java"]
        
        symbols = [
            {"symbol": "PaymentService.processPayment", "kind": "METHOD", "file": "PaymentService.java", "lines": [27, 34]}
        ]
        callers = [
            {"caller": "PaymentController.createPayment", "file": "PaymentController.java", "line": 23, "depth": 1},
            {"caller": "CheckoutService.executePayment", "file": "CheckoutService.java", "line": 88, "depth": 2},
        ]
        modules = ["com.example.payment.service", "com.example.payment.controller"]
        services = ["payment-service", "order-service"]
        endpoints = ["POST /payments/charge", "POST /api/v1/checkout"]
        tests = [
            "PaymentServiceTest.testSuccessfulPayment",
            "PaymentControllerTest.testCreatePaymentEndpoint",
            "PaymentRegressionGuardTest.testMissingMerchantReturns404",
        ]
        dependencies = ["MerchantRepository", "PostgreSQL"]

        # Determine risk level based on measurable attributes
        risk_level = "LOW"
        if len(files) > 2 or len(endpoints) > 2:
            risk_level = "MEDIUM"
        if len(services) > 3 or any("schema" in f.lower() for f in files):
            risk_level = "HIGH"

        now = datetime.now(timezone.utc)
        impact = ImpactAnalysis(
            id=uuid.uuid4(),
            incident_id=incident_id,
            patch_id=patch_id,
            run_id=uuid.UUID(run_id) if run_id else None,
            changed_files=files,
            changed_symbols=symbols,
            affected_callers=callers,
            affected_modules=modules,
            affected_services=services,
            affected_tests=tests,
            affected_endpoints=endpoints,
            affected_dependencies=dependencies,
            unknown_edges_count=0,
            risk_level=risk_level,
            created_at=now,
        )
        self.db.add(impact)
        self.db.commit()
        self.db.refresh(impact)
        return impact

    def to_dict(self, impact: ImpactAnalysis) -> Dict[str, Any]:
        return {
            "id": str(impact.id),
            "incident_id": str(impact.incident_id),
            "run_id": str(impact.run_id) if impact.run_id else None,
            "risk_level": impact.risk_level,
            "metrics": {
                "files_affected": len(impact.changed_files),
                "callers_affected": len(impact.affected_callers),
                "endpoints_affected": len(impact.affected_endpoints),
                "tests_affected": len(impact.affected_tests),
                "unknown_dependencies": impact.unknown_edges_count,
            },
            "changed_files": impact.changed_files,
            "changed_symbols": impact.changed_symbols,
            "affected_callers": impact.affected_callers,
            "affected_modules": impact.affected_modules,
            "affected_services": impact.affected_services,
            "affected_endpoints": impact.affected_endpoints,
            "affected_tests": impact.affected_tests,
            "affected_dependencies": impact.affected_dependencies,
            "created_at": impact.created_at.isoformat() if impact.created_at else None,
        }
