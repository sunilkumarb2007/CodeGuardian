import React from 'react';

const RightAgentPanel = ({ data }) => {
  const { agent_events, command_log } = data;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--bg-panel)' }}>
        <div className="panel-title" style={{ margin: 0 }}>Agent Activity</div>
      </div>
      
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        <h4 style={{ color: 'var(--text-muted)', marginBottom: '12px', fontSize: '0.85rem', textTransform: 'uppercase' }}>Reasoning & Events</h4>
        
        {agent_events && agent_events.map((ev, idx) => (
          <div key={idx} style={{ marginBottom: '16px', position: 'relative', paddingLeft: '16px', borderLeft: '2px solid var(--accent-lime-dim)' }}>
            <div style={{ position: 'absolute', left: '-5px', top: '4px', width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--accent-lime)' }}></div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{new Date(ev.timestamp).toLocaleTimeString()}</div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginTop: '4px' }}>{ev.title}</div>
            {ev.description && <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '4px' }}>{ev.description}</div>}
          </div>
        ))}

        {(!agent_events || agent_events.length === 0) && (
          <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>No events yet...</div>
        )}
      </div>

      <div style={{ height: '35%', borderTop: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '8px 16px', backgroundColor: 'var(--bg-panel)', borderBottom: '1px solid var(--border-color)' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Terminal</span>
        </div>
        <div style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', backgroundColor: '#000', fontFamily: 'var(--font-mono)' }}>
          {command_log && command_log.map((cmd, idx) => (
            <div key={idx} style={{ marginBottom: '12px' }}>
              <div style={{ color: 'var(--accent-lime)', fontSize: '0.85rem' }}>{cmd.display_command}</div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', whiteSpace: 'pre-wrap', marginTop: '4px' }}>{cmd.output}</div>
            </div>
          ))}
          {(!command_log || command_log.length === 0) && (
            <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Waiting for commands...</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RightAgentPanel;
