SELECT 'applications' AS table_name, count(*) AS count FROM applications
UNION ALL
SELECT 'repositories', count(*) FROM repositories
UNION ALL
SELECT 'repository_files', count(*) FROM repository_files
UNION ALL
SELECT 'incidents', count(*) FROM incidents
UNION ALL
SELECT 'evidence_events', count(*) FROM evidence_events
UNION ALL
SELECT 'failure_traces', count(*) FROM failure_traces
UNION ALL
SELECT 'failure_trace_nodes', count(*) FROM failure_trace_nodes
UNION ALL
SELECT 'failure_trace_edges', count(*) FROM failure_trace_edges
UNION ALL
SELECT 'failure_memories', count(*) FROM failure_memories
UNION ALL
SELECT 'memory_matches', count(*) FROM memory_matches
UNION ALL
SELECT 'investigations', count(*) FROM investigations
UNION ALL
SELECT 'patches', count(*) FROM patches
UNION ALL
SELECT 'replay_runs', count(*) FROM replay_runs
UNION ALL
SELECT 'validation_runs', count(*) FROM validation_runs;
