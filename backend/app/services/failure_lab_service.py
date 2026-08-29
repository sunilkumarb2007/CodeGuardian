import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.models import (
    FailureScenario, Incident, Run, RunEvent, FailureDNA, Application, Repository
)
from app.engine.run_state_machine import RunState
from app.services.failure_dna_service import FailureDNAService
from app.services.repair_lab_service import RepairLabService
from app.services.immunization_service import ImmunizationService
from app.services.impact_service import ImpactService

DEFAULT_SCENARIOS = [
    {
        "scenario_id": "null_object_access",
        "name": "Null Object Access (NPE)",
        "category": "Domain Logic",
        "description": "Merchant entity lookup returns null due to missing record, dereferenced without validation in business flow.",
        "failure_signature": {
            "exception": "NullPointerException",
            "endpoint": "POST /payments/charge",
            "http_status": 500,
            "service": "payment-service",
            "failure_point": "PaymentService.java:30",
        },
        "expected_trace": [
            {"service": "Gateway", "duration": "142ms", "status": "success"},
            {"service": "Order Service", "duration": "87ms", "status": "success"},
            {"service": "Payment Service", "duration": "17ms", "status": "failure"},
            {"service": "PostgreSQL", "duration": "TIMEOUT", "status": "timeout"},
        ],
        "expected_root_cause": "Merchant repository lookup yields null record dereferenced at PaymentService.java:30",
    },
    {
        "scenario_id": "database_timeout",
        "name": "Database Lock Timeout",
        "category": "Persistence",
        "description": "PostgreSQL transaction lock contention causes query cancellation after 3000ms threshold.",
        "failure_signature": {
            "exception": "QueryTimeoutException",
            "endpoint": "POST /orders/checkout",
            "http_status": 504,
            "service": "order-service",
            "failure_point": "OrderRepository.java:54",
        },
        "expected_trace": [
            {"service": "Gateway", "duration": "3120ms", "status": "failure"},
            {"service": "Order Service", "duration": "3040ms", "status": "failure"},
            {"service": "PostgreSQL", "duration": "3000ms", "status": "timeout"},
        ],
        "expected_root_cause": "Row-level lock contention on inventory ledger table",
    },
    {
        "scenario_id": "rate_limit_429",
        "name": "Upstream Rate Limit (HTTP 429)",
        "category": "External Dependency",
        "description": "Payment gateway partner throttles traffic burst exceeding 50 req/sec quota limit.",
        "failure_signature": {
            "exception": "RateLimitExceededException",
            "endpoint": "POST /payments/charge",
            "http_status": 429,
            "service": "payment-service",
            "failure_point": "StripeClient.java:92",
        },
        "expected_trace": [
            {"service": "Gateway", "duration": "45ms", "status": "failure"},
            {"service": "Payment Service", "duration": "38ms", "status": "failure"},
            {"service": "Stripe API", "duration": "22ms", "status": "rate_limited"},
        ],
        "expected_root_cause": "Missing token bucket client-side rate limiter and retry backoff",
    },
    {
        "scenario_id": "invalid_payload",
        "name": "Malformed Payload Schema",
        "category": "API Gateway",
        "description": "Client payload omits mandatory currency field, causing serialization failure.",
        "failure_signature": {
            "exception": "HttpMessageNotReadableException",
            "endpoint": "POST /api/v1/transfers",
            "http_status": 400,
            "service": "gateway",
            "failure_point": "TransferController.java:18",
        },
        "expected_trace": [
            {"service": "Gateway", "duration": "4ms", "status": "failure"},
        ],
        "expected_root_cause": "Strict Jackson deserialization failure on missing non-nullable field",
    },
    {
        "scenario_id": "redis_failure",
        "name": "Redis Distributed Lock Failure",
        "category": "Infrastructure",
        "description": "Redis master failover drops distributed run lock lease prematurely.",
        "failure_signature": {
            "exception": "RedisConnectionException",
            "endpoint": "POST /orchestration/run",
            "http_status": 500,
            "service": "orchestration-engine",
            "failure_point": "LockManager.java:44",
        },
        "expected_trace": [
            {"service": "Orchestrator", "duration": "500ms", "status": "failure"},
            {"service": "Redis", "duration": "TIMEOUT", "status": "timeout"},
        ],
        "expected_root_cause": "Socket timeout during sentinel failover election",
    },
]


class FailureLabService:
    def __init__(self, db: Session):
        self.db = db

    def seed_default_scenarios(self):
        """
        Seeds standard deterministic demonstration scenarios if not already present.
        """
        for sc in DEFAULT_SCENARIOS:
            existing = (
                self.db.query(FailureScenario)
                .filter(FailureScenario.scenario_id == sc["scenario_id"])
                .first()
            )
            if not existing:
                record = FailureScenario(
                    id=uuid.uuid4(),
                    scenario_id=sc["scenario_id"],
                    name=sc["name"],
                    category=sc["category"],
                    description=sc["description"],
                    fixture_repository="https://github.com/sunilkumarb2007/JavaAPICheck",
                    failure_signature=sc["failure_signature"],
                    expected_trace=sc["expected_trace"],
                    expected_root_cause=sc["expected_root_cause"],
                    created_at=datetime.now(timezone.utc),
                )
                self.db.add(record)
        self.db.commit()

    def list_scenarios(self) -> List[Dict[str, Any]]:
        self.seed_default_scenarios()
        scenarios = self.db.query(FailureScenario).all()
        return [
            {
                "id": str(s.id),
                "scenario_id": s.scenario_id,
                "name": s.name,
                "category": s.category,
                "description": s.description,
                "failure_signature": s.failure_signature,
                "expected_trace": s.expected_trace,
                "expected_root_cause": s.expected_root_cause,
            }
            for s in scenarios
        ]

    def execute_controlled_scenario(self, scenario_id: str) -> Dict[str, Any]:
        """
        Executes a controlled simulation scenario creating authentic database records
        and advancing deterministically through the 17-stage lifecycle.
        """
        self.seed_default_scenarios()
        scenario = (
            self.db.query(FailureScenario)
            .filter(FailureScenario.scenario_id == scenario_id)
            .first()
        )
        if not scenario:
            scenario_def = DEFAULT_SCENARIOS[0]
        else:
            scenario_def = {
                "scenario_id": scenario.scenario_id,
                "name": scenario.name,
                "category": scenario.category,
                "description": scenario.description,
                "failure_signature": scenario.failure_signature,
                "expected_trace": scenario.expected_trace,
                "expected_root_cause": scenario.expected_root_cause,
            }

        now = datetime.now(timezone.utc)
        run_id = str(uuid.uuid4())
        incident_id = uuid.uuid4()

        app = self.db.query(Application).first()
        if not app:
            app = Application(
                id=uuid.uuid4(),
                name="PaymentServiceApp",
                environment="development",
                status="active",
                created_at=now,
                updated_at=now,
            )
            self.db.add(app)
            self.db.flush()

        repo = self.db.query(Repository).first()
        if not repo:
            repo = Repository(
                id=uuid.uuid4(),
                application_id=app.id,
                provider="github",
                owner="sunilkumarb2007",
                name="JavaAPICheck",
                repository_url="https://github.com/sunilkumarb2007/JavaAPICheck",
                default_branch="main",
                access_status="authorized",
                created_at=now,
                updated_at=now,
            )
            self.db.add(repo)
            self.db.flush()

        # Create Incident record
        sig = scenario_def["failure_signature"]
        incident = Incident(
            id=incident_id,
            incident_number=1042,
            application_id=app.id,
            repository_id=repo.id,
            title=f"{scenario_def['name']} in {sig.get('service', 'payment-service')}",
            description=scenario_def["description"],
            endpoint=sig.get("endpoint", "POST /payments/charge"),
            http_method="POST",
            observed_status_code=sig.get("http_status", 500),
            symptom_service=sig.get("service", "payment-service"),
            root_cause_service=sig.get("service", "payment-service"),
            root_cause_summary=scenario_def["expected_root_cause"],
            error_fingerprint=sig.get("exception", "NULL_OBJECT_ACCESS"),
            request_id="req-demo-1",
            first_seen_at=now,
            last_seen_at=now,
            status="active",
            resolution_status="investigating",
            created_at=now,
            updated_at=now,
        )
        self.db.add(incident)
        self.db.flush()

        # Create Run record
        run = Run(
            id=run_id,
            repository_id=repo.id,
            incident_id=incident.id,
            current_stage="14_validation",
            state=RunState.WAITING_FOR_APPROVAL.value,
            created_at=now,
            updated_at=now,
        )
        self.db.add(run)
        self.db.commit()

        # Seed Failure DNA
        dna_svc = FailureDNAService(self.db)
        dna_svc.extract_or_create_dna(
            incident_id=incident_id,
            run_id=run_id,
            trigger=scenario_def["description"],
            request_method="POST",
            request_endpoint=sig.get("endpoint"),
            http_status=sig.get("http_status"),
            exception_class=sig.get("exception"),
            normalized_message=scenario_def["expected_root_cause"],
            failure_point=sig.get("failure_point"),
            dependency_type="DATABASE",
        )

        # Seed Counterfactual Candidates
        repair_svc = RepairLabService(self.db)
        repair_svc.generate_counterfactual_candidates(
            incident_id=incident_id,
            run_id=run_id,
        )

        # Seed Impact Analysis
        impact_svc = ImpactService(self.db)
        impact_svc.analyze_blast_radius(
            incident_id=incident_id,
            run_id=run_id,
        )

        # Seed Immunization Regression Guard
        imm_svc = ImmunizationService(self.db)
        imm_svc.synthesize_regression_guard(
            incident_id=incident_id,
            repository_id=repo.id,
            fingerprint=sig.get("exception", "NULL_OBJECT_ACCESS"),
        )

        return {
            "run_id": run_id,
            "incident_id": str(incident_id),
            "scenario_id": scenario_def["scenario_id"],
            "status": "RUNNING",
            "current_stage": "15_human_approval",
            "message": f"Controlled scenario '{scenario_def['name']}' initialized across all deterministic engines.",
        }
