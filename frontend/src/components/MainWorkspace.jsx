import React from 'react';

const MainWorkspace = ({ activeTab, data }) => {
  
  const renderOverview = () => (
    <div>
      <h2 style={{ marginBottom: '24px' }}>Incident Overview</h2>
      
      <div className="panel">
        <div className="panel-title">Repository</div>
        {data.repository?.url ? (
          <div className="mono">
            <div>URL: <span className="text-lime">{data.repository.url}</span></div>
            <div>Name: {data.repository.name}</div>
            <div>Language: {data.repository.language}</div>
          </div>
        ) : <div className="text-muted">Analyzing...</div>}
      </div>

      <div className="panel">
        <div className="panel-title">Failure Details</div>
        {data.incident?.fingerprint ? (
          <div>
            <div style={{ marginBottom: '12px' }}>
              <span className="badge badge-error">{data.incident.fingerprint}</span>
            </div>
            <div className="mono">
              <div>Title: {data.incident.title}</div>
              <div>Symptom Service: {data.incident.symptom_service}</div>
            </div>
          </div>
        ) : <div className="text-muted">Awaiting failure detection...</div>}
      </div>
    </div>
  );

  const renderTrace = () => (
    <div>
      <h2 style={{ marginBottom: '24px' }}>Ghost Trace Analysis</h2>
      <div className="panel">
        <div className="panel-title">Root Cause Candidate</div>
        {data.trace?.root_cause_candidate ? (
          <div className="mono text-lime" style={{ fontSize: '1.2rem', padding: '16px', backgroundColor: 'var(--bg-secondary)', borderRadius: '4px' }}>
            {data.trace.root_cause_candidate}
          </div>
        ) : <div className="text-muted">Tracing causal graph...</div>}
      </div>
    </div>
  );

  const renderMemory = () => (
    <div>
      <h2 style={{ marginBottom: '24px' }}>Failure Memory</h2>
      <div className="panel">
        <div className="panel-title">Correlation Match</div>
        {data.memory?.similarity ? (
          <div>
            <div style={{ marginBottom: '12px' }}>
              <span className="badge badge-success">Match Confidence: {(data.memory.similarity * 100).toFixed(1)}%</span>
            </div>
            <div className="mono" style={{ backgroundColor: 'var(--bg-secondary)', padding: '16px', borderRadius: '4px' }}>
              <div>{data.memory.match_reason}</div>
              <div style={{ marginTop: '12px', color: 'var(--text-muted)' }}>Historical Fix:</div>
              <div className="text-lime">{data.memory.previous_fix}</div>
            </div>
          </div>
        ) : <div className="text-muted">Searching historical failures...</div>}
      </div>
    </div>
  );

  const renderPatch = () => (
    <div>
      <h2 style={{ marginBottom: '24px' }}>Patch Generation</h2>
      <div className="panel">
        <div className="panel-title">Proposed Fix</div>
        {data.patch?.diff ? (
          <div>
            <div style={{ marginBottom: '12px' }}>
              <span className="badge badge-info">Affected Files: {JSON.stringify(data.patch.affected_files)}</span>
            </div>
            <pre className="mono" style={{ backgroundColor: 'var(--bg-secondary)', padding: '16px', borderRadius: '4px', overflowX: 'auto', color: '#e2e8f0' }}>
              {data.patch.diff}
            </pre>
            
            {data.run.status === 'waiting_for_approval' && (
              <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
                <button className="btn btn-primary" onClick={() => fetch(`/api/runs/${data.run.id}/approve`, { method: 'POST' })}>Approve & Deliver</button>
                <button className="btn" onClick={() => fetch(`/api/runs/${data.run.id}/reject`, { method: 'POST' })}>Reject</button>
              </div>
            )}
          </div>
        ) : <div className="text-muted">Synthesizing patch...</div>}
      </div>
    </div>
  );

  const renderReplay = () => (
    <div>
      <h2 style={{ marginBottom: '24px' }}>Ghost Replay Validation</h2>
      <div className="panel">
        <div className="panel-title">Before / After</div>
        {data.replay?.original ? (
          <div style={{ display: 'flex', gap: '24px' }}>
            <div style={{ flex: 1, backgroundColor: 'var(--bg-secondary)', padding: '16px', borderRadius: '4px' }}>
              <div style={{ fontWeight: 600, color: 'var(--status-error)', marginBottom: '12px' }}>Original Request</div>
              <div className="mono">
                <div>Status: {data.replay.original.status}</div>
                <div>Fingerprint: {data.replay.original.fingerprint}</div>
              </div>
            </div>
            
            <div style={{ flex: 1, backgroundColor: 'var(--bg-secondary)', padding: '16px', borderRadius: '4px' }}>
              <div style={{ fontWeight: 600, color: 'var(--status-success)', marginBottom: '12px' }}>Patched Request</div>
              <div className="mono">
                <div>Status: {data.replay.patched?.status || 'Validating...'}</div>
                {data.replay.patched && <div>Result: {data.replay.patched.result}</div>}
              </div>
            </div>
          </div>
        ) : <div className="text-muted">Awaiting replay environment...</div>}
      </div>
      
      <div className="panel">
        <div className="panel-title">Quality Gates</div>
        {data.validation?.gates ? (
          <div>
             {data.validation.gates.map((g, idx) => (
                <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                  <span>{g.name}</span>
                  <span className={g.result === 'PASS' ? 'text-lime' : 'text-muted'}>{g.result}</span>
                </div>
             ))}
          </div>
        ) : <div className="text-muted">Awaiting gates...</div>}
      </div>
    </div>
  );

  switch (activeTab) {
    case 'overview': return renderOverview();
    case 'trace': return renderTrace();
    case 'memory': return renderMemory();
    case 'patch': return renderPatch();
    case 'replay': return renderReplay();
    default: return renderOverview();
  }
};

export default MainWorkspace;
