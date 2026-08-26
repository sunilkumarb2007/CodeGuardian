BEGIN;
DELETE FROM incidents WHERE id = 'd2a57169-6136-4cc7-83c6-3e21291cb14d';
DELETE FROM incidents WHERE title LIKE 'Past Incident%';
DELETE FROM repositories WHERE name = 'JavaAPICheck';
DELETE FROM applications WHERE name = 'JavaAPICheck';

INSERT INTO applications (id, name, description, environment, repository_url, status, created_at, updated_at) 
VALUES ('11111111-1111-1111-1111-111111111111', 'JavaAPICheck', 'Spring Boot payment processing demonstration application.', 'demo', 'https://github.com/sunilkumarb2007/JavaAPICheck', 'active', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');


INSERT INTO repositories (id, application_id, provider, owner, name, repository_url, default_branch, access_status, created_at, updated_at)
VALUES ('22222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'github', 'sunilkumarb2007', 'JavaAPICheck', 'https://github.com/sunilkumarb2007/JavaAPICheck', 'main', 'authorized', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');

INSERT INTO repository_files (id, repository_id, file_path, language, source_snapshot, created_at, updated_at) VALUES ('22222222-2222-2222-2222-222222222200', '22222222-2222-2222-2222-222222222222', 'pom.xml', 'xml', '<project>...</project>', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO repository_files (id, repository_id, file_path, language, source_snapshot, created_at, updated_at) VALUES ('22222222-2222-2222-2222-222222222201', '22222222-2222-2222-2222-222222222222', 'mvnw.cmd', 'cmd', '@echo off', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO repository_files (id, repository_id, file_path, language, source_snapshot, created_at, updated_at) VALUES ('22222222-2222-2222-2222-222222222202', '22222222-2222-2222-2222-222222222222', 'README.md', 'markdown', '# JavaAPICheck', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO repository_files (id, repository_id, file_path, language, source_snapshot, created_at, updated_at) VALUES ('22222222-2222-2222-2222-222222222203', '22222222-2222-2222-2222-222222222222', 'payment-service/src/main/java/com/codeguardian/paymentservice/PaymentProcessingService.java', 'java', 'PaymentRecord paymentRecord = repository.findByOrderId(request.orderId());

// Intentional bug: the null dereference happens before validation.
if (paymentRecord.getAmount() <= 0) {
    throw new IllegalStateException("Invalid demo amount");
}
', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO repository_files (id, repository_id, file_path, language, source_snapshot, created_at, updated_at) VALUES ('22222222-2222-2222-2222-222222222204', '22222222-2222-2222-2222-222222222222', 'payment-service/src/test/java/com/codeguardian/paymentservice/PaymentServiceApplicationTests.java', 'java', '@Test
void deterministicBugReturnsInternalServerError() throws Exception {
}', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');

INSERT INTO incidents (id, incident_number, application_id, repository_id, title, description, endpoint, http_method, observed_status_code, symptom_service, root_cause_service, root_cause_summary, error_fingerprint, request_id, first_seen_at, last_seen_at, status, resolution_status, created_at, updated_at)
VALUES ('d2a57169-6136-4cc7-83c6-3e21291cb14d', 1001, '11111111-1111-1111-1111-111111111111', '22222222-2222-2222-2222-222222222222', 'Payment processing NullPointerException', 'paymentRecord is dereferenced without checking whether the repository lookup returned null.', '/payments/charge', 'POST', 500, 'payment-service', 'payment-service', 'paymentRecord is dereferenced without checking whether the repository lookup returned null.', 'NULL_OBJECT_ACCESS', 'req-demo-1', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00', 'investigating', 'unresolved', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');

INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('4a2cc76e-dada-4d8a-8ac1-514830fca848', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'repository', '2026-08-26T08:04:20.699105+00:00', 'req-demo-1', '{"message": "Repository received"}', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('a7819293-5126-41bb-b9b4-45edc0ce5529', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'other', '2026-08-26T08:04:21.699105+00:00', 'req-demo-1', '{"message": "Architecture detected"}', '2026-08-26T08:04:21.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('ec0aada0-d0ee-4852-9870-46ab4c1b9550', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'other', '2026-08-26T08:04:22.699105+00:00', 'req-demo-1', '{"message": "Java detected"}', '2026-08-26T08:04:22.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('819815ec-bc4f-4e71-aacb-6ff19ebdf3d1', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'other', '2026-08-26T08:04:23.699105+00:00', 'req-demo-1', '{"message": "Spring Boot detected"}', '2026-08-26T08:04:23.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('630da6ad-49fa-4ef0-87dd-aaab31b46f16', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'other', '2026-08-26T08:04:24.699105+00:00', 'req-demo-1', '{"message": "Maven detected"}', '2026-08-26T08:04:24.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('4bc09625-1163-4f64-a8ad-f35a3b958283', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'other', '2026-08-26T08:04:25.699105+00:00', 'req-demo-1', '{"message": "Application topology detected"}', '2026-08-26T08:04:25.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('65408aa2-90af-4f69-ae38-7bf64dd445c3', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'request', '2026-08-26T08:04:26.699105+00:00', 'req-demo-1', '{"message": "Checkout request"}', '2026-08-26T08:04:26.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('dd4aaa29-74af-44eb-af29-4ec652d688ab', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'other', '2026-08-26T08:04:27.699105+00:00', 'req-demo-1', '{"message": "Request ID"}', '2026-08-26T08:04:27.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('c857f723-7774-4199-87b7-e83d197985f1', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'request', '2026-08-26T08:04:28.699105+00:00', 'req-demo-1', '{"message": "API gateway request"}', '2026-08-26T08:04:28.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('f4ceb1fc-c49b-4564-997c-65bbba811203', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'request', '2026-08-26T08:04:29.699105+00:00', 'req-demo-1', '{"message": "Order service request"}', '2026-08-26T08:04:29.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('11f6afdd-331d-4afa-9cb4-a5b8c27093b1', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'request', '2026-08-26T08:04:30.699105+00:00', 'req-demo-1', '{"message": "Payment service request"}', '2026-08-26T08:04:30.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('0664b2a8-a3a7-4a94-9072-7f5bbcfaf175', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'database', '2026-08-26T08:04:31.699105+00:00', 'req-demo-1', '{"message": "Repository lookup"}', '2026-08-26T08:04:31.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('224f0a31-d4e8-45e0-94f8-91c77aa2d050', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'database', '2026-08-26T08:04:32.699105+00:00', 'req-demo-1', '{"message": "Repository returned null"}', '2026-08-26T08:04:32.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('088eec8b-8e5c-4504-896c-8a7e9f21b4b5', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'error', '2026-08-26T08:04:33.699105+00:00', 'req-demo-1', '{"message": "Null dereference"}', '2026-08-26T08:04:33.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('ad5b6a87-c965-4d84-9d8f-4a2aab4d37c2', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'error', '2026-08-26T08:04:34.699105+00:00', 'req-demo-1', '{"message": "NullPointerException"}', '2026-08-26T08:04:34.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('660926f1-825a-495a-a559-e81e33aafb98', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'http', '2026-08-26T08:04:35.699105+00:00', 'req-demo-1', '{"message": "HTTP 500"}', '2026-08-26T08:04:35.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('379b1386-04fb-4cef-bb92-b7630471890d', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'trace', '2026-08-26T08:04:36.699105+00:00', 'req-demo-1', '{"message": "Stack trace"}', '2026-08-26T08:04:36.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('8896acff-1150-498a-bbc5-b307dc92f5ef', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'other', '2026-08-26T08:04:37.699105+00:00', 'req-demo-1', '{"message": "Source location"}', '2026-08-26T08:04:37.699105+00:00');
INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('bb2c102b-36fe-4f2a-bde1-55a7acd496b0', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 'payment-service', 'other', '2026-08-26T08:04:38.699105+00:00', 'req-demo-1', '{"message": "Root cause candidate"}', '2026-08-26T08:04:38.699105+00:00');
INSERT INTO failure_traces (id, incident_id, trace_version, symptom_service, root_cause_candidate, confidence, reasoning_summary, correlation_method, created_at) VALUES ('33333333-3333-3333-3333-333333333333', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', 1, 'api-gateway', 'payment-service', 0.99, 'Trace points from Gateway to Order to Payment Service where NullPointerException is thrown.', '{"method": "opentelemetry"}', '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_nodes (id, failure_trace_id, sequence_number, service_name, node_type, created_at) VALUES ('39d54077-712f-4258-a790-8ec333ed1773', '33333333-3333-3333-3333-333333333333', 0, 'api-gateway', 'symptom', '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_nodes (id, failure_trace_id, sequence_number, service_name, node_type, created_at) VALUES ('d310c754-96aa-496a-a5b8-6f4857e5806f', '33333333-3333-3333-3333-333333333333', 1, 'order-service', 'service', '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_edges (id, failure_trace_id, from_node_id, to_node_id, relationship_type, correlation_strength, created_at) VALUES ('c1a3bad6-bbc5-4b91-9188-b2a25a26b52e', '33333333-3333-3333-3333-333333333333', '39d54077-712f-4258-a790-8ec333ed1773', 'd310c754-96aa-496a-a5b8-6f4857e5806f', 'downstream', 1.0, '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_nodes (id, failure_trace_id, sequence_number, service_name, node_type, created_at) VALUES ('3014ec93-32d1-4bde-a037-b5c7eebe06b7', '33333333-3333-3333-3333-333333333333', 2, 'payment-service', 'service', '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_edges (id, failure_trace_id, from_node_id, to_node_id, relationship_type, correlation_strength, created_at) VALUES ('6ba17750-5497-4096-ba43-b0243b700b6f', '33333333-3333-3333-3333-333333333333', 'd310c754-96aa-496a-a5b8-6f4857e5806f', '3014ec93-32d1-4bde-a037-b5c7eebe06b7', 'downstream', 1.0, '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_nodes (id, failure_trace_id, sequence_number, service_name, node_type, created_at) VALUES ('c3cfcf6f-6f64-476e-95b8-7520d76ac80f', '33333333-3333-3333-3333-333333333333', 3, 'PaymentProcessingService.charge()', 'root_cause', '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_edges (id, failure_trace_id, from_node_id, to_node_id, relationship_type, correlation_strength, created_at) VALUES ('dd200b4f-1a93-442d-889b-6ea078c31506', '33333333-3333-3333-3333-333333333333', '3014ec93-32d1-4bde-a037-b5c7eebe06b7', 'c3cfcf6f-6f64-476e-95b8-7520d76ac80f', 'downstream', 1.0, '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_nodes (id, failure_trace_id, sequence_number, service_name, node_type, created_at) VALUES ('18d851e0-5d67-4d8d-a8f6-2a933e12f034', '33333333-3333-3333-3333-333333333333', 4, 'repository.findByOrderId()', 'database', '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_edges (id, failure_trace_id, from_node_id, to_node_id, relationship_type, correlation_strength, created_at) VALUES ('64e52162-d65b-43d5-ab60-482412a8f610', '33333333-3333-3333-3333-333333333333', 'c3cfcf6f-6f64-476e-95b8-7520d76ac80f', '18d851e0-5d67-4d8d-a8f6-2a933e12f034', 'downstream', 1.0, '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_nodes (id, failure_trace_id, sequence_number, service_name, node_type, created_at) VALUES ('e8f48a45-cc39-402c-b253-f09c00c4efd7', '33333333-3333-3333-3333-333333333333', 5, 'NULL', 'unknown', '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_edges (id, failure_trace_id, from_node_id, to_node_id, relationship_type, correlation_strength, created_at) VALUES ('693cc5db-851b-4cbd-af94-ae06718bf5b2', '33333333-3333-3333-3333-333333333333', '18d851e0-5d67-4d8d-a8f6-2a933e12f034', 'e8f48a45-cc39-402c-b253-f09c00c4efd7', 'downstream', 1.0, '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_nodes (id, failure_trace_id, sequence_number, service_name, node_type, created_at) VALUES ('58aad6a8-7678-400e-99ac-1217c7622f11', '33333333-3333-3333-3333-333333333333', 6, 'NullPointerException', 'unknown', '2026-08-26T08:04:40.699105+00:00');
INSERT INTO failure_trace_edges (id, failure_trace_id, from_node_id, to_node_id, relationship_type, correlation_strength, created_at) VALUES ('0d925206-5c4e-4d0f-8a8c-04f4e4fcc8fd', '33333333-3333-3333-3333-333333333333', 'e8f48a45-cc39-402c-b253-f09c00c4efd7', '58aad6a8-7678-400e-99ac-1217c7622f11', 'downstream', 1.0, '2026-08-26T08:04:40.699105+00:00');
INSERT INTO incidents (id, incident_number, application_id, title, status, resolution_status, created_at, updated_at) VALUES ('99999999-9999-9999-9999-999999999990', 2000, '11111111-1111-1111-1111-111111111111', 'Past Incident 0', 'resolved', 'resolved', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO failure_memories (id, incident_id, application_id, error_pattern, error_fingerprint, root_cause, affected_files, code_change, searchable_text, memory_status, created_at, updated_at) VALUES ('55555555-5555-5555-5555-555555555550', '99999999-9999-9999-9999-999999999990', '11111111-1111-1111-1111-111111111111', 'NULL_OBJECT_ACCESS in payment-service', 'NULL_OBJECT_ACCESS', 'Missing null check before dereference', '["payment-service"]', 'Add null check before dereference', 'NULL_OBJECT_ACCESS payment-service Missing null check before dereference', 'verified', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO incidents (id, incident_number, application_id, title, status, resolution_status, created_at, updated_at) VALUES ('99999999-9999-9999-9999-999999999991', 2001, '11111111-1111-1111-1111-111111111111', 'Past Incident 1', 'resolved', 'resolved', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO failure_memories (id, incident_id, application_id, error_pattern, error_fingerprint, root_cause, affected_files, code_change, searchable_text, memory_status, created_at, updated_at) VALUES ('55555555-5555-5555-5555-555555555551', '99999999-9999-9999-9999-999999999991', '11111111-1111-1111-1111-111111111111', 'NULL_OBJECT_ACCESS in order-service', 'NULL_OBJECT_ACCESS', 'Unvalidated object access', '["order-service"]', 'Validate object before use', 'NULL_OBJECT_ACCESS order-service Unvalidated object access', 'verified', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO incidents (id, incident_number, application_id, title, status, resolution_status, created_at, updated_at) VALUES ('99999999-9999-9999-9999-999999999992', 2002, '11111111-1111-1111-1111-111111111111', 'Past Incident 2', 'resolved', 'resolved', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO failure_memories (id, incident_id, application_id, error_pattern, error_fingerprint, root_cause, affected_files, code_change, searchable_text, memory_status, created_at, updated_at) VALUES ('55555555-5555-5555-5555-555555555552', '99999999-9999-9999-9999-999999999992', '11111111-1111-1111-1111-111111111111', 'MISSING_NULL_GUARD in payment-service', 'MISSING_NULL_GUARD', 'Null guard missing', '["payment-service"]', 'Add null guard', 'MISSING_NULL_GUARD payment-service Null guard missing', 'verified', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO incidents (id, incident_number, application_id, title, status, resolution_status, created_at, updated_at) VALUES ('99999999-9999-9999-9999-999999999993', 2003, '11111111-1111-1111-1111-111111111111', 'Past Incident 3', 'resolved', 'resolved', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO failure_memories (id, incident_id, application_id, error_pattern, error_fingerprint, root_cause, affected_files, code_change, searchable_text, memory_status, created_at, updated_at) VALUES ('55555555-5555-5555-5555-555555555553', '99999999-9999-9999-9999-999999999993', '11111111-1111-1111-1111-111111111111', 'UNVALIDATED_REPOSITORY_RESULT in payment-service', 'UNVALIDATED_REPOSITORY_RESULT', 'Repository result unvalidated', '["payment-service"]', 'Validate repository result', 'UNVALIDATED_REPOSITORY_RESULT payment-service Repository result unvalidated', 'verified', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO incidents (id, incident_number, application_id, title, status, resolution_status, created_at, updated_at) VALUES ('99999999-9999-9999-9999-999999999994', 2004, '11111111-1111-1111-1111-111111111111', 'Past Incident 4', 'resolved', 'resolved', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO failure_memories (id, incident_id, application_id, error_pattern, error_fingerprint, root_cause, affected_files, code_change, searchable_text, memory_status, created_at, updated_at) VALUES ('55555555-5555-5555-5555-555555555554', '99999999-9999-9999-9999-999999999994', '11111111-1111-1111-1111-111111111111', 'NULL_OBJECT_ACCESS in payment-service', 'NULL_OBJECT_ACCESS', 'Python NoneType dereference', '["payment-service"]', 'Check for None', 'NULL_OBJECT_ACCESS payment-service Python NoneType dereference', 'verified', '2026-08-26T08:04:20.699105+00:00', '2026-08-26T08:04:20.699105+00:00');
INSERT INTO memory_matches (id, incident_id, memory_id, similarity_score, match_reason, matched_error_pattern, matched_root_cause, matched_affected_files, matched_code_context, verification_status, created_at) VALUES ('e71e3cbb-16d6-482b-bcd1-a79e6410a77d', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', '55555555-5555-5555-5555-555555555550', 0.87, 'same error fingerprint, same affected service, same failure pattern, similar root cause', true, true, true, true, 'verified', '2026-08-26T08:04:45.699105+00:00');

INSERT INTO investigations (id, incident_id, failure_trace_id, investigation_type, root_cause, explanation, affected_files, affected_lines, proposed_fix, memory_used, status, created_at, updated_at)
VALUES ('44444444-4444-4444-4444-444444444444', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', '33333333-3333-3333-3333-333333333333', 'ai', 'Missing null guard.', 'PaymentProcessingService.charge() dereferences paymentRecord without null validation.', '["PaymentProcessingService.java"]', '{}', 'Add a null guard before object access.', true, 'completed', '2026-08-26T08:04:50.699105+00:00', '2026-08-26T08:04:50.699105+00:00');


INSERT INTO patches (id, incident_id, investigation_id, memory_match_id, patch_number, branch_name, commit_message, diff, affected_files, generation_reason, status, generated_by, created_at, updated_at)
VALUES ('4cf61f48-7700-430a-8a06-ce0ea5af68f7', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', '44444444-4444-4444-4444-444444444444', 'e71e3cbb-16d6-482b-bcd1-a79e6410a77d', 1, 'codeguardian/incident-d2a57169/repair-4cf61f48', 'fix: guard missing payment record', '--- a/payment-service/src/main/java/com/codeguardian/paymentservice/PaymentProcessingService.java
+++ b/payment-service/src/main/java/com/codeguardian/paymentservice/PaymentProcessingService.java
@@ -14,7 +14,7 @@
     public CheckoutResponse charge(CheckoutRequest request) {
         PaymentRecord paymentRecord = repository.findByOrderId(request.orderId());
 
-        // Intentional bug: the null dereference happens before validation.
-        if (paymentRecord.getAmount() <= 0) {
+        if (paymentRecord != null && paymentRecord.getAmount() <= 0) {
             throw new IllegalStateException("Invalid demo amount");
         }
 
--- a/payment-service/src/test/java/com/codeguardian/paymentservice/PaymentPatchRegressionTest.java
+++ b/payment-service/src/test/java/com/codeguardian/paymentservice/PaymentPatchRegressionTest.java
@@ -1,6 +1,5 @@
 package com.codeguardian.paymentservice;
 
-import org.junit.jupiter.api.Disabled;
 import org.junit.jupiter.api.Test;
 import org.springframework.beans.factory.annotation.Autowired;
 import org.springframework.boot.test.context.SpringBootTest;
@@ -8,7 +7,6 @@
 import static org.assertj.core.api.Assertions.assertThat;
 
-@Disabled("Enable after CodeGuardian adds the null check patch.")
 @SpringBootTest
 class PaymentPatchRegressionTest {
 
--- a/payment-service/src/test/java/com/codeguardian/paymentservice/PaymentServiceApplicationTests.java
+++ b/payment-service/src/test/java/com/codeguardian/paymentservice/PaymentServiceApplicationTests.java
@@ -23,8 +23,8 @@
                         .content("""
                                 {"userId":101,"orderId":5001,"amount":499.0}
                                 """))
-                .andExpect(status().isInternalServerError())
-                .andExpect(jsonPath("$.errorCode").value("NULL_OBJECT_ACCESS"));
+                .andExpect(status().isOk())
+                .andExpect(jsonPath("$.status").value("SUCCESS"));
     }
', '["PaymentProcessingService.java", "PaymentPatchRegressionTest.java", "PaymentServiceApplicationTests.java"]', 'Add null check', 'validated', 'gemini-3.6-flash', '2026-08-26T08:04:55.699105+00:00', '2026-08-26T08:04:55.699105+00:00');


INSERT INTO replay_runs (id, incident_id, patch_id, replay_type, expected_status_code, actual_status_code, expected_behavior, actual_behavior, reproduced_failure, execution_output, environment, status, created_at)
VALUES ('77777777-7777-7777-7777-777777777777', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', NULL, 'original', 500, 500, 'HTTP 500', 'HTTP 500', true, 'NULL_OBJECT_ACCESS FAILED', '{}', 'failed', '2026-08-26T08:05:00.699105+00:00');


INSERT INTO replay_runs (id, incident_id, patch_id, replay_type, expected_status_code, actual_status_code, expected_behavior, actual_behavior, reproduced_failure, execution_output, environment, status, created_at)
VALUES ('88888888-8888-8888-8888-888888888888', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', '4cf61f48-7700-430a-8a06-ce0ea5af68f7', 'patched', 200, 200, 'HTTP 200', 'HTTP 200', false, 'SUCCESS PASSED', '{}', 'passed', '2026-08-26T08:05:05.699105+00:00');


INSERT INTO validation_runs (id, incident_id, patch_id, build_passed, tests_passed, replay_passed, validation_summary, status, created_at)
VALUES ('66666666-6666-6666-6666-666666666666', 'd2a57169-6136-4cc7-83c6-3e21291cb14d', '4cf61f48-7700-430a-8a06-ce0ea5af68f7', true, true, true, 'Patch validated successfully.', 'passed', '2026-08-26T08:05:10.699105+00:00');

COMMIT;