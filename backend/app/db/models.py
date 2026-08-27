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


class RepositoryFile(Base):
    __tablename__ = 'repository_files'

    id = Column(GUID, primary_key=True, nullable=False)
    repository_id = Column(GUID, ForeignKey('repositories.id'), nullable=False)
    file_path = Column(Text, nullable=False)
    language = Column(String(50), nullable=True)
    file_hash = Column(String(128), nullable=True)
    source_snapshot = Column(Text, nullable=True)
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
