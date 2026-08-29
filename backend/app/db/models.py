from datetime import datetime
from sqlalchemy import Column, String, Integer, BigInteger, Text, Boolean, Numeric, TIMESTAMP, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
import uuid
import json
from sqlalchemy.types import TypeDecorator, CHAR, String, Text

class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID as PGUUID
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value

class JSONType(TypeDecorator):
    impl = Text
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
            return dialect.type_descriptor(PGJSONB())
        else:
            return dialect.type_descriptor(Text())
    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql' or value is None:
            return value
        return json.dumps(value)
    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql' or value is None:
            return value
        return json.loads(value)

class StringArray(TypeDecorator):
    impl = Text
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import ARRAY as PGARRAY
            return dialect.type_descriptor(PGARRAY(String))
        else:
            return dialect.type_descriptor(Text())
    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql' or value is None:
            return value
        return json.dumps(value)
    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql' or value is None:
            return value
        return json.loads(value)

class UUIDArray(TypeDecorator):
    impl = Text
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import ARRAY as PGARRAY, UUID as PGUUID
            return dialect.type_descriptor(PGARRAY(PGUUID(as_uuid=True)))
        else:
            return dialect.type_descriptor(Text())
    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql' or value is None:
            return value
        return json.dumps([str(v) for v in value])
    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql' or value is None:
            return value
        return [uuid.UUID(v) for v in json.loads(value)]


import uuid
import json
from sqlalchemy.types import TypeDecorator, CHAR, String, Text

class GUID(TypeDecorator):
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID as PGUUID
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value

class JSONType(TypeDecorator):
    impl = Text
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
            return dialect.type_descriptor(PGJSONB())
        else:
            return dialect.type_descriptor(Text())
    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql' or value is None:
            return value
        return json.dumps(value)
    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql' or value is None:
            return value
        return json.loads(value)

class StringArray(TypeDecorator):
    impl = Text
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import ARRAY as PGARRAY
            return dialect.type_descriptor(PGStringArray)
        else:
            return dialect.type_descriptor(Text())
    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql' or value is None:
            return value
        return json.dumps(value)
    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql' or value is None:
            return value
        return json.loads(value)

class GUIDArray(TypeDecorator):
    impl = Text
    cache_ok = True
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import ARRAY as PGARRAY, GUID as PGGUID
            return dialect.type_descriptor(PGARRAY(PGGUID))
        else:
            return dialect.type_descriptor(Text())
    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql' or value is None:
            return value
        return json.dumps([str(v) for v in value])
    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql' or value is None:
            return value
        return [uuid.UUID(v) for v in json.loads(value)]


class Application(Base):
    __tablename__ = 'applications'

    id = Column(GUID, primary_key=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    environment = Column(String(50), nullable=False)
    repository_url = Column(Text, nullable=True)
    status = Column(String(30), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class Repository(Base):
    __tablename__ = 'repositories'

    id = Column(GUID, primary_key=True, nullable=False)
    application_id = Column(GUID, ForeignKey('applications.id'), nullable=False)
    provider = Column(String(30), nullable=False)
    owner = Column(String(150), nullable=False)
    name = Column(String(200), nullable=False)
    repository_url = Column(Text, nullable=False)
    default_branch = Column(String(100), nullable=False)
    access_status = Column(String(30), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class RepositoryConnection(Base):
    __tablename__ = 'repository_connections'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    repository_id = Column(GUID, ForeignKey('repositories.id'), nullable=True, unique=True)
    provider = Column(String(50), nullable=False, default='github')
    owner = Column(String(150), nullable=False)
    name = Column(String(200), nullable=False)
    repository_url = Column(Text, nullable=False)
    default_branch = Column(String(100), nullable=False, default='main')
    monitoring_enabled = Column(Boolean, nullable=False, default=True)
    automatic_investigation_enabled = Column(Boolean, nullable=False, default=True)
    auto_pr_enabled = Column(Boolean, nullable=False, default=False)
    approval_policy = Column(String(50), nullable=False, default='HUMAN_APPROVAL_REQUIRED')
    notification_policy = Column(JSONType, nullable=False, default=dict)
    webhook_secret = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)


class RepositoryFile(Base):
    __tablename__ = 'repository_files'

    id = Column(GUID, primary_key=True, nullable=False)
    repository_id = Column(GUID, ForeignKey('repositories.id'), nullable=False)
    file_path = Column(Text, nullable=False)
    language = Column(String(50), nullable=True)
    file_hash = Column(String(128), nullable=True)
    source_snapshot = Column(Text, nullable=True)
    # Classifies files for context priority: SOURCE, TEST, CONFIGURATION, DOCUMENTATION
    # DOCUMENTATION files are non-authoritative and must not be used for patch generation.
    file_role = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class Incident(Base):
    __tablename__ = 'incidents'

    id = Column(GUID, primary_key=True, nullable=False)
    incident_number = Column(BigInteger, nullable=False)
    application_id = Column(GUID, ForeignKey('applications.id'), nullable=False)
    repository_id = Column(GUID, ForeignKey('repositories.id'), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    endpoint = Column(String(500), nullable=True)
    http_method = Column(String(20), nullable=True)
    observed_status_code = Column(Integer, nullable=True)
    symptom_service = Column(String(150), nullable=True)
    root_cause_service = Column(String(150), nullable=True)
    root_cause_summary = Column(Text, nullable=True)
    error_fingerprint = Column(String(255), nullable=True)
    request_id = Column(String(255), nullable=True)
    first_seen_at = Column(TIMESTAMP, nullable=True)
    last_seen_at = Column(TIMESTAMP, nullable=True)
    status = Column(String(40), nullable=False)
    resolution_status = Column(String(40), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class EvidenceEvent(Base):
    __tablename__ = 'evidence_events'

    id = Column(GUID, primary_key=True, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    service_name = Column(String(150), nullable=True)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    request_id = Column(String(255), nullable=True)
    endpoint = Column(String(500), nullable=True)
    http_method = Column(String(20), nullable=True)
    status_code = Column(Integer, nullable=True)
    error_code = Column(String(100), nullable=True)
    error_message = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)
    event_metadata = Column('metadata', JSONType, nullable=False)
    raw_payload = Column(JSONType, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)


class FailureTrace(Base):
    __tablename__ = 'failure_traces'

    id = Column(GUID, primary_key=True, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    trace_version = Column(Integer, nullable=False)
    symptom_service = Column(String(150), nullable=True)
    root_cause_candidate = Column(String(150), nullable=True)
    confidence = Column(Numeric(5, 4), nullable=True)
    reasoning_summary = Column(Text, nullable=True)
    correlation_method = Column(JSONType, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)


class FailureTraceNode(Base):
    __tablename__ = 'failure_trace_nodes'

    id = Column(GUID, primary_key=True, nullable=False)
    failure_trace_id = Column(GUID, ForeignKey('failure_traces.id'), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    service_name = Column(String(150), nullable=False)
    endpoint = Column(String(500), nullable=True)
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    node_type = Column(String(40), nullable=True)
    evidence_ids = Column(UUIDArray, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)


class FailureTraceEdge(Base):
    __tablename__ = 'failure_trace_edges'

    id = Column(GUID, primary_key=True, nullable=False)
    failure_trace_id = Column(GUID, ForeignKey('failure_traces.id'), nullable=False)
    from_node_id = Column(GUID, ForeignKey('failure_trace_nodes.id'), nullable=False)
    to_node_id = Column(GUID, ForeignKey('failure_trace_nodes.id'), nullable=False)
    relationship_type = Column(String(50), nullable=False)
    correlation_strength = Column(Numeric(5, 4), nullable=True)
    evidence_ids = Column(UUIDArray, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)


class Investigation(Base):
    __tablename__ = 'investigations'

    id = Column(GUID, primary_key=True, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    failure_trace_id = Column(GUID, ForeignKey('failure_traces.id'), nullable=True)
    model_provider = Column(String(50), nullable=True)
    model_name = Column(String(100), nullable=True)
    investigation_type = Column(String(50), nullable=False)
    root_cause = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    affected_files = Column(JSONType, nullable=False)
    affected_lines = Column(JSONType, nullable=False)
    proposed_fix = Column(Text, nullable=True)
    evidence_summary = Column(Text, nullable=True)
    memory_used = Column(Boolean, nullable=False)
    confidence = Column(Numeric(5, 4), nullable=True)
    raw_response = Column(JSONType, nullable=True)
    status = Column(String(40), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class FailureMemory(Base):
    __tablename__ = 'failure_memories'

    id = Column(GUID, primary_key=True, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    application_id = Column(GUID, ForeignKey('applications.id'), nullable=False)
    error_pattern = Column(Text, nullable=False)
    error_fingerprint = Column(String(255), nullable=True)
    root_cause = Column(Text, nullable=False)
    affected_files = Column(JSONType, nullable=False)
    code_change = Column(Text, nullable=True)
    patch_summary = Column(Text, nullable=True)
    validation_result = Column(JSONType, nullable=True)
    pull_request_history = Column(JSONType, nullable=True)
    searchable_text = Column(Text, nullable=False)
    memory_status = Column(String(30), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class MemoryMatch(Base):
    __tablename__ = 'memory_matches'

    id = Column(GUID, primary_key=True, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    memory_id = Column(GUID, ForeignKey('failure_memories.id'), nullable=False)
    similarity_score = Column(Numeric(5, 4), nullable=True)
    match_reason = Column(Text, nullable=True)
    matched_error_pattern = Column(Boolean, nullable=False)
    matched_root_cause = Column(Boolean, nullable=False)
    matched_affected_files = Column(Boolean, nullable=False)
    matched_code_context = Column(Boolean, nullable=False)
    verification_status = Column(String(40), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)


class Patch(Base):
    __tablename__ = 'patches'

    id = Column(GUID, primary_key=True, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    investigation_id = Column(GUID, ForeignKey('investigations.id'), nullable=True)
    memory_match_id = Column(GUID, ForeignKey('memory_matches.id'), nullable=True)
    patch_number = Column(Integer, nullable=False)
    branch_name = Column(String(255), nullable=True)
    commit_message = Column(Text, nullable=True)
    diff = Column(Text, nullable=False)
    affected_files = Column(JSONType, nullable=False)
    generation_reason = Column(Text, nullable=True)
    status = Column(String(40), nullable=False)
    generated_by = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class ValidationRun(Base):
    __tablename__ = 'validation_runs'

    id = Column(GUID, primary_key=True, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    patch_id = Column(GUID, ForeignKey('patches.id'), nullable=False)
    build_passed = Column(Boolean, nullable=True)
    tests_passed = Column(Boolean, nullable=True)
    replay_passed = Column(Boolean, nullable=True)
    original_failure_reproduced = Column(Boolean, nullable=True)
    repair_verified = Column(Boolean, nullable=True)
    exit_code = Column(Integer, nullable=True)
    build_output = Column(Text, nullable=True)
    test_output = Column(Text, nullable=True)
    replay_output = Column(Text, nullable=True)
    validation_summary = Column(Text, nullable=True)
    status = Column(String(40), nullable=False)
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)


class RepairAttempt(Base):
    __tablename__ = 'repair_attempts'

    id = Column(GUID, primary_key=True, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    patch_id = Column(GUID, ForeignKey('patches.id'), nullable=True)
    validation_run_id = Column(GUID, ForeignKey('validation_runs.id'), nullable=True)
    attempt_number = Column(Integer, nullable=False)
    failure_reason = Column(Text, nullable=True)
    repair_action = Column(Text, nullable=True)
    status = Column(String(40), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)


class ReplayRun(Base):
    __tablename__ = 'replay_runs'

    id = Column(GUID, primary_key=True, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    patch_id = Column(GUID, ForeignKey('patches.id'), nullable=True)
    replay_type = Column(String(30), nullable=False)
    endpoint = Column(String(500), nullable=True)
    http_method = Column(String(20), nullable=True)
    expected_status_code = Column(Integer, nullable=True)
    actual_status_code = Column(Integer, nullable=True)
    expected_behavior = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)
    reproduced_failure = Column(Boolean, nullable=True)
    execution_output = Column(Text, nullable=True)
    environment = Column(JSONType, nullable=False)
    status = Column(String(40), nullable=False)
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)


class PullRequest(Base):
    __tablename__ = 'pull_requests'

    id = Column(GUID, primary_key=True, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    patch_id = Column(GUID, ForeignKey('patches.id'), nullable=False)
    repository_id = Column(GUID, ForeignKey('repositories.id'), nullable=False)
    provider = Column(String(30), nullable=False)
    branch_name = Column(String(255), nullable=False)
    base_branch = Column(String(255), nullable=False)
    external_pr_number = Column(Integer, nullable=True)
    external_pr_url = Column(Text, nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    validation_summary = Column(Text, nullable=True)
    status = Column(String(40), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class IncidentStatusHistory(Base):
    __tablename__ = 'incident_status_history'

    id = Column(GUID, primary_key=True, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    previous_status = Column(String(40), nullable=True)
    new_status = Column(String(40), nullable=False)
    reason = Column(Text, nullable=True)
    status_metadata = Column('metadata', JSONType, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)


# ==============================================================================
# DEMO MODELS (For deterministic IDE presentation)
# ==============================================================================

class DemoRun(Base):
    __tablename__ = 'demo_runs'

    id = Column(String(50), primary_key=True, nullable=False)  # Using the string run_id generated by DemoRunner
    scenario_id = Column(String(100), nullable=False)
    repository_id = Column(GUID, ForeignKey('repositories.id'), nullable=True)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=True)
    mode = Column(String(30), nullable=False, default='demo')
    status = Column(String(40), nullable=False)
    current_stage = Column(String(50), nullable=False)
    started_at = Column(TIMESTAMP, nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)
    approval_state = Column(String(40), nullable=True)
    delivery_state = Column(String(40), nullable=True)
    presentation_sequence = Column(JSONType, nullable=True)


class DemoEvent(Base):
    __tablename__ = 'demo_events'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    run_id = Column(String(50), ForeignKey('demo_runs.id'), nullable=False)
    sequence = Column(Integer, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    event_type = Column(String(50), nullable=False) # e.g. 'tool', 'system', 'observation'
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    command = Column(String(255), nullable=True)
    output = Column(Text, nullable=True)
    status = Column(String(40), nullable=False)
    related_entity_type = Column(String(50), nullable=True)
    related_entity_id = Column(String(100), nullable=True)


class DemoAction(Base):
    __tablename__ = 'demo_actions'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    run_id = Column(String(50), ForeignKey('demo_runs.id'), nullable=False)
    action_id = Column(String(100), nullable=False)
    label = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_panel = Column(String(100), nullable=True)
    response_data = Column(JSONType, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)


class Run(Base):
    __tablename__ = 'runs'
    id = Column(GUID, primary_key=True)
    repository_id = Column(GUID, ForeignKey('repositories.id'), nullable=True)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=True)
    current_stage = Column(String, nullable=True)
    state = Column(String, nullable=False)
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)
    terminal_at = Column(TIMESTAMP, nullable=True)

class RunEvent(Base):
    __tablename__ = 'run_events'
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(GUID, ForeignKey('runs.id'))
    sequence = Column(Integer, nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    event_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    command = Column(Text, nullable=True)
    output = Column(Text, nullable=True)
    status = Column(String, nullable=False)
    related_entity_type = Column(String, nullable=True)
    related_entity_id = Column(String, nullable=True)

class RunAction(Base):
    __tablename__ = 'run_actions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(GUID, ForeignKey('runs.id'))
    event_id = Column(Integer, ForeignKey('run_events.id'))
    action_type = Column(String, nullable=False)
    payload = Column(JSONType, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)


# ==============================================================================
# ADVANCED PRODUCT EXPANSION MODELS
# ==============================================================================

class FailureDNA(Base):
    __tablename__ = 'failure_dna'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    run_id = Column(GUID, ForeignKey('runs.id'), nullable=True)
    trigger = Column(String(255), nullable=True)
    request_method = Column(String(20), nullable=True)
    request_endpoint = Column(String(500), nullable=True)
    http_status = Column(Integer, nullable=True)
    exception_class = Column(String(255), nullable=True)
    normalized_message = Column(Text, nullable=True)
    propagation_chain = Column(JSONType, nullable=False, default=list)
    failure_point = Column(String(255), nullable=True)
    dependency_type = Column(String(100), nullable=True)
    fingerprint = Column(String(255), nullable=False, index=True)
    recurrence_count = Column(Integer, nullable=False, default=1)
    resolved_count = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False)
    updated_at = Column(TIMESTAMP, nullable=False)


class RepairCandidate(Base):
    __tablename__ = 'repair_candidates'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    run_id = Column(GUID, ForeignKey('runs.id'), nullable=True)
    candidate_label = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    patch_diff = Column(Text, nullable=False)
    assumptions = Column(JSONType, nullable=True)
    expected_behavior = Column(Text, nullable=True)
    is_recommended = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, nullable=False)


class RepairEvaluation(Base):
    __tablename__ = 'repair_evaluations'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    candidate_id = Column(GUID, ForeignKey('repair_candidates.id'), nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    run_id = Column(GUID, ForeignKey('runs.id'), nullable=True)
    safety_status = Column(String(40), nullable=False)  # PASS, FAILED, NOT_MEASURED
    build_status = Column(String(40), nullable=False)
    tests_status = Column(String(40), nullable=False)
    replay_status = Column(String(40), nullable=False)
    semantic_risk = Column(String(40), nullable=False)  # LOW, MEDIUM, HIGH, NOT_MEASURED
    blast_radius_risk = Column(String(40), nullable=False)  # LOW, MEDIUM, HIGH, NOT_MEASURED
    final_status = Column(String(40), nullable=False)  # ACCEPTED, REJECTED, EVALUATING
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)


class RegressionGuard(Base):
    __tablename__ = 'regression_guards'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    repository_id = Column(GUID, ForeignKey('repositories.id'), nullable=True)
    fingerprint = Column(String(255), nullable=False, index=True)
    test_path = Column(Text, nullable=False)
    test_name = Column(String(255), nullable=False)
    test_code = Column(Text, nullable=False)
    validation_status = Column(String(40), nullable=False)  # PASSED, FAILED, PENDING
    source_commit = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)
    failure_scenario = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)


class ImpactAnalysis(Base):
    __tablename__ = 'impact_analyses'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    patch_id = Column(GUID, ForeignKey('patches.id'), nullable=True)
    run_id = Column(GUID, ForeignKey('runs.id'), nullable=True)
    changed_files = Column(JSONType, nullable=False, default=list)
    changed_symbols = Column(JSONType, nullable=False, default=list)
    affected_callers = Column(JSONType, nullable=False, default=list)
    affected_modules = Column(JSONType, nullable=False, default=list)
    affected_services = Column(JSONType, nullable=False, default=list)
    affected_tests = Column(JSONType, nullable=False, default=list)
    affected_endpoints = Column(JSONType, nullable=False, default=list)
    affected_dependencies = Column(JSONType, nullable=False, default=list)
    unknown_edges_count = Column(Integer, nullable=False, default=0)
    risk_level = Column(String(30), nullable=False)  # LOW, MEDIUM, HIGH
    created_at = Column(TIMESTAMP, nullable=False)


class FailureCapsule(Base):
    __tablename__ = 'failure_capsules'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    incident_id = Column(GUID, ForeignKey('incidents.id'), nullable=False)
    run_id = Column(GUID, ForeignKey('runs.id'), nullable=True)
    fingerprint = Column(String(255), nullable=False)
    version = Column(String(30), nullable=False, default='1.0.0')
    manifest = Column(JSONType, nullable=False)
    redactions_applied = Column(JSONType, nullable=False, default=list)
    capsule_path = Column(Text, nullable=True)
    size_bytes = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, nullable=False)


class FailureScenario(Base):
    __tablename__ = 'failure_scenarios'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    scenario_id = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    fixture_repository = Column(Text, nullable=True)
    failure_signature = Column(JSONType, nullable=False)
    expected_trace = Column(JSONType, nullable=False)
    expected_root_cause = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False)


class RepositoryIntelligence(Base):
    __tablename__ = 'repository_intelligences'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    repository_id = Column(GUID, ForeignKey('repositories.id'), nullable=True)
    commit_sha = Column(String(100), nullable=True, index=True)
    architecture_type = Column(String(50), nullable=False, default='SINGLE_APPLICATION')  # MONOREPO, MICROSERVICES, SINGLE_APPLICATION, MODULAR_MONOLITH
    services_inventory = Column(JSONType, nullable=False, default=list)
    service_graph = Column(JSONType, nullable=False, default=dict)
    dependency_graph = Column(JSONType, nullable=False, default=dict)
    symbol_index = Column(JSONType, nullable=False, default=dict)
    endpoint_index = Column(JSONType, nullable=False, default=list)
    config_manifest = Column(JSONType, nullable=False, default=list)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)


class ConfigurationDrift(Base):
    __tablename__ = 'configuration_drifts'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    run_id = Column(GUID, ForeignKey('runs.id'), nullable=True, index=True)
    service_name = Column(String(100), nullable=False)
    key_name = Column(String(255), nullable=False)
    source_file = Column(String(255), nullable=True)
    environment = Column(String(50), nullable=False, default='production')
    desired_state = Column(String(255), nullable=False)  # e.g., PRESENT, NON_EMPTY
    observed_state = Column(String(255), nullable=False)  # e.g., MISSING, DRIFTED
    status = Column(String(40), nullable=False)  # MISSING, DRIFT, INCOMPATIBLE, VERIFIED
    recovery_proposal = Column(Text, nullable=True)
    is_recovered = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)


class ApprovalDecision(Base):
    __tablename__ = 'approval_decisions'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    run_id = Column(GUID, ForeignKey('runs.id'), nullable=False, index=True)
    actor = Column(String(100), nullable=False)
    decision = Column(String(40), nullable=False)  # APPROVED_FOR_PR, APPROVED_FOR_MERGE, REJECTED
    policy_evaluation = Column(JSONType, nullable=False, default=dict)
    risk_level = Column(String(30), nullable=False, default='LOW')
    auto_merge_eligible = Column(Boolean, nullable=False, default=False)
    auto_merge_reason = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)


class NotificationItem(Base):
    __tablename__ = 'notification_items'

    id = Column(GUID, primary_key=True, default=uuid.uuid4, nullable=False)
    run_id = Column(GUID, ForeignKey('runs.id'), nullable=True, index=True)
    notification_type = Column(String(50), nullable=False)  # APPROVAL_REQUIRED, VALIDATION_PASSED, PR_CREATED, MERGE_READY, REPAIR_FAILED
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(255), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.utcnow)


