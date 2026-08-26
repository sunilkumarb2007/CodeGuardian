import uuid
from datetime import datetime, timezone, timedelta
import json

def get_sql():
    sql = []
    
    app_id = "11111111-1111-1111-1111-111111111111"
    repo_id = "22222222-2222-2222-2222-222222222222"
    incident_id = "d2a57169-6136-4cc7-83c6-3e21291cb14d"
    trace_id = "33333333-3333-3333-3333-333333333333"
    inv_id = "44444444-4444-4444-4444-444444444444"
    patch_id = "4cf61f48-7700-430a-8a06-ce0ea5af68f7"
    val_id = "66666666-6666-6666-6666-666666666666"
    replay_id_1 = "77777777-7777-7777-7777-777777777777"
    replay_id_2 = "88888888-8888-8888-8888-888888888888"
    
    now = datetime.now(timezone.utc)
    t = lambda offset: (now + timedelta(seconds=offset)).isoformat()
    
    sql.append("BEGIN;")
    
    # Clean old demo data if exists
    sql.append(f"DELETE FROM incidents WHERE id = '{incident_id}';")
    sql.append(f"DELETE FROM incidents WHERE title LIKE 'Past Incident%';")
    sql.append(f"DELETE FROM repositories WHERE name = 'JavaAPICheck';")
    sql.append(f"DELETE FROM applications WHERE name = 'JavaAPICheck';")
    
    sql.append(f"""
INSERT INTO applications (id, name, description, environment, repository_url, status, created_at, updated_at) 
VALUES ('{app_id}', 'JavaAPICheck', 'Spring Boot payment processing demonstration application.', 'demo', 'https://github.com/sunilkumarb2007/JavaAPICheck', 'active', '{t(0)}', '{t(0)}');
""")

    sql.append(f"""
INSERT INTO repositories (id, application_id, provider, owner, name, repository_url, default_branch, access_status, created_at, updated_at)
VALUES ('{repo_id}', '{app_id}', 'github', 'sunilkumarb2007', 'JavaAPICheck', 'https://github.com/sunilkumarb2007/JavaAPICheck', 'main', 'authorized', '{t(0)}', '{t(0)}');
""")

    # Repository files
    files = [
        ('pom.xml', 'xml', '<project>...</project>'),
        ('mvnw.cmd', 'cmd', '@echo off'),
        ('README.md', 'markdown', '# JavaAPICheck'),
        ('payment-service/src/main/java/com/codeguardian/paymentservice/PaymentProcessingService.java', 'java', 'PaymentRecord paymentRecord = repository.findByOrderId(request.orderId());\n\n// Intentional bug: the null dereference happens before validation.\nif (paymentRecord.getAmount() <= 0) {\n    throw new IllegalStateException("Invalid demo amount");\n}\n'),
        ('payment-service/src/test/java/com/codeguardian/paymentservice/PaymentServiceApplicationTests.java', 'java', '@Test\nvoid deterministicBugReturnsInternalServerError() throws Exception {\n}'),
    ]
    for i, (path, lang, content) in enumerate(files):
        fid = f"22222222-2222-2222-2222-22222222220{i}"
        content_safe = content.replace("'", "''")
        sql.append(f"INSERT INTO repository_files (id, repository_id, file_path, language, source_snapshot, created_at, updated_at) VALUES ('{fid}', '{repo_id}', '{path}', '{lang}', '{content_safe}', '{t(0)}', '{t(0)}');")

    sql.append(f"""
INSERT INTO incidents (id, incident_number, application_id, repository_id, title, description, endpoint, http_method, observed_status_code, symptom_service, root_cause_service, root_cause_summary, error_fingerprint, request_id, first_seen_at, last_seen_at, status, resolution_status, created_at, updated_at)
VALUES ('{incident_id}', 1001, '{app_id}', '{repo_id}', 'Payment processing NullPointerException', 'paymentRecord is dereferenced without checking whether the repository lookup returned null.', '/payments/charge', 'POST', 500, 'payment-service', 'payment-service', 'paymentRecord is dereferenced without checking whether the repository lookup returned null.', 'NULL_OBJECT_ACCESS', 'req-demo-1', '{t(0)}', '{t(0)}', 'investigating', 'unresolved', '{t(0)}', '{t(0)}');
""")

    events = [
        ('Repository received', 'repository', 0),
        ('Architecture detected', 'other', 1),
        ('Java detected', 'other', 2),
        ('Spring Boot detected', 'other', 3),
        ('Maven detected', 'other', 4),
        ('Application topology detected', 'other', 5),
        ('Checkout request', 'request', 6),
        ('Request ID', 'other', 7),
        ('API gateway request', 'request', 8),
        ('Order service request', 'request', 9),
        ('Payment service request', 'request', 10),
        ('Repository lookup', 'database', 11),
        ('Repository returned null', 'database', 12),
        ('Null dereference', 'error', 13),
        ('NullPointerException', 'error', 14),
        ('HTTP 500', 'http', 15),
        ('Stack trace', 'trace', 16),
        ('Source location', 'other', 17),
        ('Root cause candidate', 'other', 18)
    ]
    for msg, etype, offset in events:
        eid = str(uuid.uuid4())
        sql.append(f"INSERT INTO evidence_events (id, incident_id, service_name, event_type, timestamp, request_id, metadata, created_at) VALUES ('{eid}', '{incident_id}', 'payment-service', '{etype}', '{t(offset)}', 'req-demo-1', '{{\"message\": \"{msg}\"}}', '{t(offset)}');")

    sql.append(f"INSERT INTO failure_traces (id, incident_id, trace_version, symptom_service, root_cause_candidate, confidence, reasoning_summary, correlation_method, created_at) VALUES ('{trace_id}', '{incident_id}', 1, 'api-gateway', 'payment-service', 0.99, 'Trace points from Gateway to Order to Payment Service where NullPointerException is thrown.', '{{\"method\": \"opentelemetry\"}}', '{t(20)}');")

    nodes = [
        ('api-gateway', 'symptom'),
        ('order-service', 'service'),
        ('payment-service', 'service'),
        ('PaymentProcessingService.charge()', 'root_cause'),
        ('repository.findByOrderId()', 'database'),
        ('NULL', 'unknown'),
        ('NullPointerException', 'unknown')
    ]
    prev_id = None
    for i, (name, ntype) in enumerate(nodes):
        nid = str(uuid.uuid4())
        sql.append(f"INSERT INTO failure_trace_nodes (id, failure_trace_id, sequence_number, service_name, node_type, created_at) VALUES ('{nid}', '{trace_id}', {i}, '{name}', '{ntype}', '{t(20)}');")
        if prev_id:
            eid = str(uuid.uuid4())
            sql.append(f"INSERT INTO failure_trace_edges (id, failure_trace_id, from_node_id, to_node_id, relationship_type, correlation_strength, created_at) VALUES ('{eid}', '{trace_id}', '{prev_id}', '{nid}', 'downstream', 1.0, '{t(20)}');")
        prev_id = nid

    # Memories
    memories = [
        ('NULL_OBJECT_ACCESS', 'payment-service', 'Missing null check before dereference', 'payment-service', 'Add null check before dereference'),
        ('NULL_OBJECT_ACCESS', 'order-service', 'Unvalidated object access', 'order-service', 'Validate object before use'),
        ('MISSING_NULL_GUARD', 'payment-service', 'Null guard missing', 'payment-service', 'Add null guard'),
        ('UNVALIDATED_REPOSITORY_RESULT', 'payment-service', 'Repository result unvalidated', 'payment-service', 'Validate repository result'),
        ('NULL_OBJECT_ACCESS', 'payment-service', 'Python NoneType dereference', 'payment-service', 'Check for None')
    ]
    for i, (fpr, srv, rc, aff, chg) in enumerate(memories):
        mid = f"55555555-5555-5555-5555-55555555555{i}"
        dummy_inc_id = f"99999999-9999-9999-9999-99999999999{i}"
        sql.append(f"INSERT INTO incidents (id, incident_number, application_id, title, status, resolution_status, created_at, updated_at) VALUES ('{dummy_inc_id}', {2000+i}, '{app_id}', 'Past Incident {i}', 'resolved', 'resolved', '{t(0)}', '{t(0)}');")
        sql.append(f"INSERT INTO failure_memories (id, incident_id, application_id, error_pattern, error_fingerprint, root_cause, affected_files, code_change, searchable_text, memory_status, created_at, updated_at) VALUES ('{mid}', '{dummy_inc_id}', '{app_id}', '{fpr} in {srv}', '{fpr}', '{rc}', '[\"{aff}\"]', '{chg}', '{fpr} {srv} {rc}', 'verified', '{t(0)}', '{t(0)}');")
    
    # Match for current incident
    match_id = str(uuid.uuid4())
    sql.append(f"INSERT INTO memory_matches (id, incident_id, memory_id, similarity_score, match_reason, matched_error_pattern, matched_root_cause, matched_affected_files, matched_code_context, verification_status, created_at) VALUES ('{match_id}', '{incident_id}', '55555555-5555-5555-5555-555555555550', 0.87, 'same error fingerprint, same affected service, same failure pattern, similar root cause', true, true, true, true, 'verified', '{t(25)}');")

    sql.append(f"""
INSERT INTO investigations (id, incident_id, failure_trace_id, investigation_type, root_cause, explanation, affected_files, affected_lines, proposed_fix, memory_used, status, created_at, updated_at)
VALUES ('{inv_id}', '{incident_id}', '{trace_id}', 'ai', 'Missing null guard.', 'PaymentProcessingService.charge() dereferences paymentRecord without null validation.', '["PaymentProcessingService.java"]', '{{}}', 'Add a null guard before object access.', true, 'completed', '{t(30)}', '{t(30)}');
""")

    diff = '''--- a/payment-service/src/main/java/com/codeguardian/paymentservice/PaymentProcessingService.java
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
'''
    diff_safe = diff.replace("'", "''")
    sql.append(f"""
INSERT INTO patches (id, incident_id, investigation_id, memory_match_id, patch_number, branch_name, commit_message, diff, affected_files, generation_reason, status, generated_by, created_at, updated_at)
VALUES ('{patch_id}', '{incident_id}', '{inv_id}', '{match_id}', 1, 'codeguardian/incident-d2a57169/repair-4cf61f48', 'fix: guard missing payment record', '{diff_safe}', '["PaymentProcessingService.java", "PaymentPatchRegressionTest.java", "PaymentServiceApplicationTests.java"]', 'Add null check', 'validated', 'gemini-3.6-flash', '{t(35)}', '{t(35)}');
""")

    sql.append(f"""
INSERT INTO replay_runs (id, incident_id, patch_id, replay_type, expected_status_code, actual_status_code, expected_behavior, actual_behavior, reproduced_failure, execution_output, environment, status, created_at)
VALUES ('{replay_id_1}', '{incident_id}', NULL, 'original', 500, 500, 'HTTP 500', 'HTTP 500', true, 'NULL_OBJECT_ACCESS FAILED', '{{}}', 'failed', '{t(40)}');
""")

    sql.append(f"""
INSERT INTO replay_runs (id, incident_id, patch_id, replay_type, expected_status_code, actual_status_code, expected_behavior, actual_behavior, reproduced_failure, execution_output, environment, status, created_at)
VALUES ('{replay_id_2}', '{incident_id}', '{patch_id}', 'patched', 200, 200, 'HTTP 200', 'HTTP 200', false, 'SUCCESS PASSED', '{{}}', 'passed', '{t(45)}');
""")

    sql.append(f"""
INSERT INTO validation_runs (id, incident_id, patch_id, build_passed, tests_passed, replay_passed, validation_summary, status, created_at)
VALUES ('{val_id}', '{incident_id}', '{patch_id}', true, true, true, 'Patch validated successfully.', 'passed', '{t(50)}');
""")

    sql.append("COMMIT;")
    
    return "\n".join(sql)

if __name__ == '__main__':
    with open('sql/demo_data.sql', 'w') as f:
        f.write(get_sql())
    print("Demo data generated.")
