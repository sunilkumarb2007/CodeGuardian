CREATE TABLE applications (
	id UUID NOT NULL, 
	name VARCHAR(150) NOT NULL, 
	description TEXT, 
	environment VARCHAR(50) NOT NULL, 
	repository_url TEXT, 
	status VARCHAR(30) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE repositories (
	id UUID NOT NULL, 
	application_id UUID NOT NULL, 
	provider VARCHAR(30) NOT NULL, 
	owner VARCHAR(150) NOT NULL, 
	name VARCHAR(200) NOT NULL, 
	repository_url TEXT NOT NULL, 
	default_branch VARCHAR(100) NOT NULL, 
	access_status VARCHAR(30) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(application_id) REFERENCES applications (id)
);

CREATE TABLE incidents (
	id UUID NOT NULL, 
	incident_number BIGINT NOT NULL, 
	application_id UUID NOT NULL, 
	repository_id UUID, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	endpoint VARCHAR(500), 
	http_method VARCHAR(20), 
	observed_status_code INTEGER, 
	symptom_service VARCHAR(150), 
	root_cause_service VARCHAR(150), 
	root_cause_summary TEXT, 
	error_fingerprint VARCHAR(255), 
	request_id VARCHAR(255), 
	first_seen_at TIMESTAMP WITHOUT TIME ZONE, 
	last_seen_at TIMESTAMP WITHOUT TIME ZONE, 
	status VARCHAR(40) NOT NULL, 
	resolution_status VARCHAR(40) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(application_id) REFERENCES applications (id), 
	FOREIGN KEY(repository_id) REFERENCES repositories (id)
);

CREATE TABLE repository_files (
	id UUID NOT NULL, 
	repository_id UUID NOT NULL, 
	file_path TEXT NOT NULL, 
	language VARCHAR(50), 
	file_hash VARCHAR(128), 
	source_snapshot TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(repository_id) REFERENCES repositories (id)
);

CREATE TABLE evidence_events (
	id UUID NOT NULL, 
	incident_id UUID NOT NULL, 
	service_name VARCHAR(150), 
	event_type VARCHAR(50) NOT NULL, 
	timestamp TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	request_id VARCHAR(255), 
	endpoint VARCHAR(500), 
	http_method VARCHAR(20), 
	status_code INTEGER, 
	error_code VARCHAR(100), 
	error_message TEXT, 
	stack_trace TEXT, 
	source VARCHAR(100), 
	metadata JSONB NOT NULL, 
	raw_payload JSONB, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(incident_id) REFERENCES incidents (id)
);

CREATE TABLE failure_memories (
	id UUID NOT NULL, 
	incident_id UUID NOT NULL, 
	application_id UUID NOT NULL, 
	error_pattern TEXT NOT NULL, 
	error_fingerprint VARCHAR(255), 
	root_cause TEXT NOT NULL, 
	affected_files JSONB NOT NULL, 
	code_change TEXT, 
	patch_summary TEXT, 
	validation_result JSONB, 
	pull_request_history JSONB, 
	searchable_text TEXT NOT NULL, 
	memory_status VARCHAR(30) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(incident_id) REFERENCES incidents (id), 
	FOREIGN KEY(application_id) REFERENCES applications (id)
);

CREATE TABLE failure_traces (
	id UUID NOT NULL, 
	incident_id UUID NOT NULL, 
	trace_version INTEGER NOT NULL, 
	symptom_service VARCHAR(150), 
	root_cause_candidate VARCHAR(150), 
	confidence NUMERIC(5, 4), 
	reasoning_summary TEXT, 
	correlation_method JSONB NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(incident_id) REFERENCES incidents (id)
);

CREATE TABLE incident_status_history (
	id UUID NOT NULL, 
	incident_id UUID NOT NULL, 
	previous_status VARCHAR(40), 
	new_status VARCHAR(40) NOT NULL, 
	reason TEXT, 
	metadata JSONB NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(incident_id) REFERENCES incidents (id)
);

CREATE TABLE failure_trace_nodes (
	id UUID NOT NULL, 
	failure_trace_id UUID NOT NULL, 
	sequence_number INTEGER NOT NULL, 
	service_name VARCHAR(150) NOT NULL, 
	endpoint VARCHAR(500), 
	status_code INTEGER, 
	error_message TEXT, 
	node_type VARCHAR(40), 
	evidence_ids UUID[], 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(failure_trace_id) REFERENCES failure_traces (id)
);

CREATE TABLE investigations (
	id UUID NOT NULL, 
	incident_id UUID NOT NULL, 
	failure_trace_id UUID, 
	model_provider VARCHAR(50), 
	model_name VARCHAR(100), 
	investigation_type VARCHAR(50) NOT NULL, 
	root_cause TEXT, 
	explanation TEXT, 
	affected_files JSONB NOT NULL, 
	affected_lines JSONB NOT NULL, 
	proposed_fix TEXT, 
	evidence_summary TEXT, 
	memory_used BOOLEAN NOT NULL, 
	confidence NUMERIC(5, 4), 
	raw_response JSONB, 
	status VARCHAR(40) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(incident_id) REFERENCES incidents (id), 
	FOREIGN KEY(failure_trace_id) REFERENCES failure_traces (id)
);

CREATE TABLE memory_matches (
	id UUID NOT NULL, 
	incident_id UUID NOT NULL, 
	memory_id UUID NOT NULL, 
	similarity_score NUMERIC(5, 4), 
	match_reason TEXT, 
	matched_error_pattern BOOLEAN NOT NULL, 
	matched_root_cause BOOLEAN NOT NULL, 
	matched_affected_files BOOLEAN NOT NULL, 
	matched_code_context BOOLEAN NOT NULL, 
	verification_status VARCHAR(40) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(incident_id) REFERENCES incidents (id), 
	FOREIGN KEY(memory_id) REFERENCES failure_memories (id)
);

CREATE TABLE failure_trace_edges (
	id UUID NOT NULL, 
	failure_trace_id UUID NOT NULL, 
	from_node_id UUID NOT NULL, 
	to_node_id UUID NOT NULL, 
	relationship_type VARCHAR(50) NOT NULL, 
	correlation_strength NUMERIC(5, 4), 
	evidence_ids UUID[], 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(failure_trace_id) REFERENCES failure_traces (id), 
	FOREIGN KEY(from_node_id) REFERENCES failure_trace_nodes (id), 
	FOREIGN KEY(to_node_id) REFERENCES failure_trace_nodes (id)
);

CREATE TABLE patches (
	id UUID NOT NULL, 
	incident_id UUID NOT NULL, 
	investigation_id UUID, 
	memory_match_id UUID, 
	patch_number INTEGER NOT NULL, 
	branch_name VARCHAR(255), 
	commit_message TEXT, 
	diff TEXT NOT NULL, 
	affected_files JSONB NOT NULL, 
	generation_reason TEXT, 
	status VARCHAR(40) NOT NULL, 
	generated_by VARCHAR(50) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(incident_id) REFERENCES incidents (id), 
	FOREIGN KEY(investigation_id) REFERENCES investigations (id), 
	FOREIGN KEY(memory_match_id) REFERENCES memory_matches (id)
);

CREATE TABLE pull_requests (
	id UUID NOT NULL, 
	incident_id UUID NOT NULL, 
	patch_id UUID NOT NULL, 
	repository_id UUID NOT NULL, 
	provider VARCHAR(30) NOT NULL, 
	branch_name VARCHAR(255) NOT NULL, 
	base_branch VARCHAR(255) NOT NULL, 
	external_pr_number INTEGER, 
	external_pr_url TEXT, 
	title VARCHAR(255) NOT NULL, 
	description TEXT, 
	validation_summary TEXT, 
	status VARCHAR(40) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(incident_id) REFERENCES incidents (id), 
	FOREIGN KEY(patch_id) REFERENCES patches (id), 
	FOREIGN KEY(repository_id) REFERENCES repositories (id)
);

CREATE TABLE replay_runs (
	id UUID NOT NULL, 
	incident_id UUID NOT NULL, 
	patch_id UUID, 
	replay_type VARCHAR(30) NOT NULL, 
	endpoint VARCHAR(500), 
	http_method VARCHAR(20), 
	expected_status_code INTEGER, 
	actual_status_code INTEGER, 
	expected_behavior TEXT, 
	actual_behavior TEXT, 
	reproduced_failure BOOLEAN, 
	execution_output TEXT, 
	environment JSONB NOT NULL, 
	status VARCHAR(40) NOT NULL, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(incident_id) REFERENCES incidents (id), 
	FOREIGN KEY(patch_id) REFERENCES patches (id)
);

CREATE TABLE validation_runs (
	id UUID NOT NULL, 
	incident_id UUID NOT NULL, 
	patch_id UUID NOT NULL, 
	build_passed BOOLEAN, 
	tests_passed BOOLEAN, 
	replay_passed BOOLEAN, 
	original_failure_reproduced BOOLEAN, 
	repair_verified BOOLEAN, 
	exit_code INTEGER, 
	build_output TEXT, 
	test_output TEXT, 
	replay_output TEXT, 
	validation_summary TEXT, 
	status VARCHAR(40) NOT NULL, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(incident_id) REFERENCES incidents (id), 
	FOREIGN KEY(patch_id) REFERENCES patches (id)
);

CREATE TABLE repair_attempts (
	id UUID NOT NULL, 
	incident_id UUID NOT NULL, 
	patch_id UUID, 
	validation_run_id UUID, 
	attempt_number INTEGER NOT NULL, 
	failure_reason TEXT, 
	repair_action TEXT, 
	status VARCHAR(40) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(incident_id) REFERENCES incidents (id), 
	FOREIGN KEY(patch_id) REFERENCES patches (id), 
	FOREIGN KEY(validation_run_id) REFERENCES validation_runs (id)
);

