import React, { useState, useEffect } from 'react';
import { runsApi } from '../api/runsApi';
import RightAgentPanel from './RightAgentPanel';
import MainWorkspace from './MainWorkspace';

const AppShell = () => {
  const [activeRunId, setActiveRunId] = useState(null);
  const [workspaceData, setWorkspaceData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  useEffect(() => {
    let interval;
    if (activeRunId) {
      interval = setInterval(async () => {
        try {
          const data = await runsApi.getWorkspace(activeRunId);
          setWorkspaceData(data);
          
          if (data.run.status === 'completed' || data.run.status === 'failed') {
            clearInterval(interval);
          }
        } catch (e) {
          console.error('Failed to fetch workspace', e);
        }
      }, 2000);
    }
    
    return () => clearInterval(interval);
  }, [activeRunId]);

  const startDemoRun = async () => {
    try {
      const result = await runsApi.startDemo();
      setActiveRunId(result.run_id);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="ide-layout">
      {/* TOP NAV */}
      <div className="ide-topnav">
        <div className="ide-brand">
          <span>CodeGuardian</span>
        </div>
        <div>
          {!activeRunId && (
            <button className="btn btn-primary" onClick={startDemoRun}>
              Start Investigation
            </button>
          )}
          {workspaceData && (
            <span className={`badge ${workspaceData.run.status === 'running' ? 'badge-warning pulse' : 'badge-success'}`} style={{ marginLeft: '12px' }}>
              {workspaceData.run.status.toUpperCase()}
            </span>
          )}
        </div>
      </div>

      <div className="ide-main">
        {/* LEFT SIDEBAR */}
        <div className="ide-sidebar">
          <div className="panel-title" style={{ paddingLeft: '16px' }}>Workspace</div>
          <div className={`nav-item ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
            Incident Overview
          </div>
          <div className={`nav-item ${activeTab === 'trace' ? 'active' : ''}`} onClick={() => setActiveTab('trace')}>
            Ghost Trace
          </div>
          <div className={`nav-item ${activeTab === 'memory' ? 'active' : ''}`} onClick={() => setActiveTab('memory')}>
            Failure Memory
          </div>
          <div className={`nav-item ${activeTab === 'patch' ? 'active' : ''}`} onClick={() => setActiveTab('patch')}>
            Patch Review
          </div>
          <div className={`nav-item ${activeTab === 'replay' ? 'active' : ''}`} onClick={() => setActiveTab('replay')}>
            Replay & Validation
          </div>
        </div>

        {/* MAIN WORKSPACE */}
        <div className="ide-workspace">
          {workspaceData ? (
            <MainWorkspace activeTab={activeTab} data={workspaceData} />
          ) : (
            <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
              Select "Start Investigation" to begin...
            </div>
          )}
        </div>

        {/* RIGHT AGENT PANEL */}
        <div className="ide-agent-panel">
          {workspaceData && <RightAgentPanel data={workspaceData} />}
        </div>
      </div>
    </div>
  );
};

export default AppShell;
