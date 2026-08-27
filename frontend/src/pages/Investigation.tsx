import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useRun } from '../hooks/useRun'
import { CursorFX } from '../components/CursorFX'
import { Card } from '../components/primitives'
import { BrandLoader } from '../components/Layout'

import { IDEHeader } from '../components/workspace/IDEHeader'
import { IDESidebar, type WorkspaceSection } from '../components/workspace/IDESidebar'
import { IDEStatusBar } from '../components/workspace/IDEStatusBar'
import { TraceOverviewPanel } from '../components/workspace/TraceOverviewPanel'
import { AutoFixAgentPanel } from '../components/workspace/AutoFixAgentPanel'

import {
  EvidencePanel,
  GhostTracePanel,
  SourcePanel,
  StackTracePanel,
} from '../components/panels/failure'
import { RepositoryPanel, RunStatusPanel } from '../components/panels/discovery'
import {
  ApprovalPanel,
  ChangedFilesPanel,
  CommandLogPanel,
  CommandResultPanel,
  CompatibilityPanel,
  DeliveryPanel,
  InvestigationPanel,
  MemoryPanel,
  MemoryUpdatePanel,
  PatchPanel,
  ReplayPanel,
  ValidationPanel,
} from '../components/panels/repair'

type TabType = 'Trace Overview' | 'Stack Trace' | 'Logs (24)' | 'Request' | 'Response' | 'Metadata'

const TABS: TabType[] = [
  'Trace Overview',
  'Stack Trace',
  'Logs (24)',
  'Request',
  'Response',
  'Metadata',
]

export default function Investigation() {
  const params = useParams<{ runId: string }>()
  const runId = params.runId ?? ''
  const { run, error, loading, deciding, approve, reject, decideFile, refresh } = useRun(runId)

  const [activeSection, setActiveSection] = useState<WorkspaceSection>('Overview')
  const [activeTab, setActiveTab] = useState<TabType>('Trace Overview')

  const displayRunId = runId ? `INV-${runId.slice(0, 4).toUpperCase()}` : 'INV-1042'
  const incidentTitle = run?.incident?.title || run?.incident?.errorType || 'Payment processing\nNullPointerException'
  const incidentDescription =
    run?.incident?.summary ||
    'paymentRecord is dereferenced without checking whether the repository lookup returned null.'
  const httpStatus = run?.incident?.httpStatus ?? 500
  const endpoint = run?.incident?.endpoint ?? 'POST /payments/charge'
  const serviceName = run?.incident?.service ?? run?.repository?.name ?? 'payment-service'
  const requestId = run?.incident?.requestId ?? 'req-demo-1'
  const firstSeen = run?.incident?.firstSeen ?? '2026-08-26 13:34:20 +05:30'
  const environment = run?.incident?.environment ?? 'development'
  const fingerprint = run?.incident?.fingerprint ?? 'NULL_OBJECT_ACCESS'
  const attempts = run?.incident?.attempts !== undefined ? `${run.incident.attempts} / 3` : '0 / 3'

  const handleSelectStage = (stageKey: string) => {
    // Map stage key to corresponding workspace section or keep Overview
    if (stageKey.includes('repository')) setActiveSection('Repository')
    else if (stageKey.includes('evidence')) setActiveSection('Evidence')
    else if (stageKey.includes('ghost_trace')) setActiveSection('GhostTrace')
    else if (stageKey.includes('memory')) setActiveSection('Memory')
    else if (stageKey.includes('investigation')) setActiveSection('Investigation')
    else if (stageKey.includes('patch')) setActiveSection('Patch')
    else if (stageKey.includes('replay')) setActiveSection('Replay')
    else if (stageKey.includes('validation')) setActiveSection('Validation')
    else if (stageKey.includes('delivery')) setActiveSection('Delivery')
    else setActiveSection('Overview')
  }

  return (
    <div className="flex h-screen flex-col bg-[#070A0B] text-white font-sans overflow-hidden select-none">
      <CursorFX />

      {/* 1. Global Top IDE Header */}
      <IDEHeader run={run} runId={runId} />

      {/* Error Banner if API failed */}
      {error ? (
        <div className="p-4 bg-red-950/40 border-b border-red-500/40 flex items-center justify-between text-xs font-mono text-red-300">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-red-500 animate-ping" />
            <span>BACKEND DISCONNECTED: {error}</span>
          </div>
          <button
            type="button"
            onClick={() => void refresh()}
            className="px-3 py-1 bg-red-900/60 hover:bg-red-900 border border-red-500/50 rounded text-white"
          >
            Retry Connection
          </button>
        </div>
      ) : null}

      {/* Loading state before initial payload */}
      {loading && !run ? (
        <div className="flex-1 flex items-center justify-center">
          <Card className="p-8 text-center border border-white/[0.08] bg-[#0F1518]">
            <BrandLoader label="Connecting to CodeGuardian workspace..." />
          </Card>
        </div>
      ) : (
        /* 2. Main 3-Column IDE Workspace Body */
        <div className="flex-1 flex min-h-0 overflow-hidden">
          {/* Column A: Left Sidebar (~195px) */}
          <IDESidebar
            activeSection={activeSection}
            onSelectSection={(s) => {
              setActiveSection(s)
              if (s === 'Overview') setActiveTab('Trace Overview')
            }}
            run={run}
            onSelectStage={handleSelectStage}
          />

          {/* Column B: Center Investigation Area (Scrollable Main Workspace) */}
          <main className="flex-1 flex flex-col min-w-0 bg-[#0B1012] overflow-y-auto">
            <div className="p-6 max-w-[1400px] mx-auto w-full space-y-6">
              {/* Breadcrumb */}
              <div className="flex items-center gap-2 text-xs font-mono text-zinc-500">
                <span className="hover:text-zinc-300 cursor-pointer">Investigations</span>
                <span>/</span>
                <span className="text-zinc-400">{displayRunId}</span>
                <span>/</span>
                <span className="text-lime font-semibold">
                  {activeSection === 'Overview' ? 'Failure Detection' : activeSection}
                </span>
              </div>

              {/* Incident Header */}
              <div className="rounded-xl border border-white/[0.08] bg-[#0F1518] p-5">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                  {/* Left Title & Chips */}
                  <div className="lg:col-span-8 space-y-3">
                    <h1 className="font-display text-2xl lg:text-3xl font-black text-white tracking-tight leading-tight whitespace-pre-line">
                      {incidentTitle}
                    </h1>

                    {/* Metadata Chips */}
                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <span className="px-2.5 py-0.5 rounded font-mono text-xs font-bold bg-red-500/15 border border-red-500/30 text-red-400">
                        HTTP {httpStatus}
                      </span>
                      <span className="px-2.5 py-0.5 rounded font-mono text-xs bg-[#070A0B] border border-white/[0.08] text-zinc-300">
                        {endpoint}
                      </span>
                      <span className="px-2.5 py-0.5 rounded font-mono text-xs bg-blue-500/10 border border-blue-500/30 text-blue-300 flex items-center gap-1.5">
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                        </svg>
                        {serviceName}
                      </span>
                      <span className="px-2.5 py-0.5 rounded font-mono text-xs bg-[#070A0B] border border-white/[0.08] text-zinc-400">
                        {requestId}
                      </span>
                    </div>

                    {/* Summary Description */}
                    <p className="text-sm text-zinc-300 font-sans leading-relaxed pt-1">
                      {incidentDescription}
                    </p>
                  </div>

                  {/* Right Metadata 2-Column Grid */}
                  <div className="lg:col-span-4 border-t lg:border-t-0 lg:border-l border-white/[0.08] lg:pl-6 grid grid-cols-2 gap-y-2 text-xs font-mono">
                    <div>
                      <span className="text-zinc-500 block text-[10px] uppercase">First seen</span>
                      <span className="text-zinc-200 text-[11px]">{firstSeen}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px] uppercase">Environment</span>
                      <span className="text-zinc-200">{environment}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px] uppercase">Error fingerprint</span>
                      <span className="text-zinc-300 text-[11px]">{fingerprint}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px] uppercase">Attempts</span>
                      <span className="text-zinc-300">{attempts}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px] uppercase">Severity</span>
                      <span className="text-amber-400 font-semibold flex items-center gap-1">
                        <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
                        Medium
                      </span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px] uppercase">Duration</span>
                      <span className="text-zinc-200">17ms</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Tab Navigation */}
              <div className="flex items-center gap-6 border-b border-white/[0.08] text-xs font-mono">
                {TABS.map((tab) => {
                  const isActive = activeTab === tab
                  return (
                    <button
                      key={tab}
                      type="button"
                      onClick={() => setActiveTab(tab)}
                      className={`pb-2.5 transition-colors relative font-semibold ${
                        isActive
                          ? 'text-lime'
                          : 'text-zinc-400 hover:text-zinc-200'
                      }`}
                    >
                      <span>{tab}</span>
                      {isActive ? (
                        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-lime rounded-full" />
                      ) : null}
                    </button>
                  )
                })}
              </div>

              {/* Main Tab Content */}
              {activeTab === 'Trace Overview' && activeSection === 'Overview' ? (
                <TraceOverviewPanel trace={run?.ghostTrace} incident={run?.incident} />
              ) : activeTab === 'Stack Trace' || activeSection === 'Source' ? (
                <div className="space-y-6">
                  <StackTracePanel stackTrace={run?.stackTrace} />
                  <SourcePanel files={run?.sourceFiles ?? []} investigation={run?.investigation} />
                </div>
              ) : activeTab === 'Logs (24)' ? (
                <div className="space-y-6">
                  <CommandLogPanel commands={run?.commands ?? []} />
                </div>
              ) : activeTab === 'Request' ? (
                <div className="rounded-xl border border-white/[0.08] bg-[#0F1518] p-5 font-mono text-xs space-y-4">
                  <h3 className="font-bold text-white uppercase text-sm">HTTP Request</h3>
                  <pre className="p-3 bg-[#070A0B] rounded-lg text-zinc-300 border border-white/[0.08] overflow-x-auto">
                    {`POST /payments/charge HTTP/1.1\nHost: api.codeguardian.local\nContent-Type: application/json\nX-Request-Id: ${requestId}\n\n{\n  "amount": 2500,\n  "currency": "USD",\n  "customer_id": "cust_90124",\n  "payment_method": "pm_card_visa"\n}`}
                  </pre>
                </div>
              ) : activeTab === 'Response' ? (
                <div className="rounded-xl border border-white/[0.08] bg-[#0F1518] p-5 font-mono text-xs space-y-4">
                  <h3 className="font-bold text-red-400 uppercase text-sm">HTTP Response (500 Internal Server Error)</h3>
                  <pre className="p-3 bg-[#070A0B] rounded-lg text-red-400 border border-red-500/20 overflow-x-auto">
                    {`HTTP/1.1 500 Internal Server Error\nContent-Type: application/json\nX-Request-Id: ${requestId}\n\n{\n  "error": "InternalServerError",\n  "message": "NullPointerException: Cannot read properties of null at PaymentService.charge(PaymentService.java:82)",\n  "status": 500\n}`}
                  </pre>
                </div>
              ) : activeTab === 'Metadata' ? (
                <div className="rounded-xl border border-white/[0.08] bg-[#0F1518] p-5 font-mono text-xs space-y-4">
                  <h3 className="font-bold text-white uppercase text-sm">Incident Metadata</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-zinc-500 block text-[10px]">APPLICATION</span>
                      <span className="text-zinc-200">{serviceName}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px]">HOST</span>
                      <span className="text-zinc-200">macos-worker-01</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px]">TRACE ID</span>
                      <span className="text-zinc-300">4b4d05950bc9045a470d62</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px]">RUNTIME</span>
                      <span className="text-zinc-200">OpenJDK 17.0.9</span>
                    </div>
                  </div>
                </div>
              ) : null}

              {/* Workspace Sections Content if navigated via Left Nav */}
              {activeSection === 'Repository' ? (
                <div className="space-y-6">
                  <RepositoryPanel repository={run?.repository} />
                  {run ? <RunStatusPanel run={run} /> : null}
                </div>
              ) : activeSection === 'Evidence' ? (
                <div className="space-y-6">
                  <EvidencePanel evidence={run?.evidence ?? []} />
                  <CommandLogPanel commands={run?.commands ?? []} />
                </div>
              ) : activeSection === 'GhostTrace' ? (
                <GhostTracePanel trace={run?.ghostTrace} />
              ) : activeSection === 'Memory' ? (
                <div className="space-y-6">
                  <MemoryPanel memory={run?.memory} />
                  <MemoryUpdatePanel update={run?.memoryUpdate} />
                </div>
              ) : activeSection === 'Investigation' ? (
                <InvestigationPanel investigation={run?.investigation} />
              ) : activeSection === 'Patch' ? (
                <div className="space-y-6">
                  <PatchPanel patch={run?.patch} />
                  <CompatibilityPanel compatibility={run?.compatibility} />
                  <ChangedFilesPanel
                    files={run?.changedFiles ?? []}
                    onDecide={(fileId, decision) => void decideFile(fileId, decision)}
                    decisionsLocked={run?.status === 'completed' || run?.status === 'rejected'}
                  />
                </div>
              ) : activeSection === 'Replay' ? (
                <ReplayPanel replay={run?.replay} />
              ) : activeSection === 'Validation' ? (
                <div className="space-y-6">
                  <CommandResultPanel index="11" title="Build" caption="Build executed against the patched source." result={run?.build} />
                  <CommandResultPanel index="12" title="Tests" caption="Regression suite executed against the patched source." result={run?.tests} />
                  <ValidationPanel validation={run?.validation} />
                </div>
              ) : activeSection === 'Delivery' ? (
                <DeliveryPanel delivery={run?.delivery} />
              ) : null}

              {/* Human Approval Gate Banner */}
              {run?.status === 'waiting_for_approval' ? (
                <div className="mt-8">
                  <ApprovalPanel
                    onApprove={() => void approve()}
                    onReject={() => void reject()}
                    busy={deciding}
                  />
                </div>
              ) : null}
            </div>
          </main>

          {/* Column C: Persistent Right AI Agent (AutoFix) (~310px) */}
          <AutoFixAgentPanel
            run={run}
            onQuickAction={(action) => {
              if (action === 'ghosttrace') {
                setActiveSection('GhostTrace')
                setActiveTab('Trace Overview')
              } else if (action === 'logs') {
                setActiveTab('Logs (24)')
              } else if (action === 'source') {
                setActiveSection('Source')
                setActiveTab('Stack Trace')
              }
            }}
          />
        </div>
      )}

      {/* 3. Execution Status Bar (Bottom) */}
      <IDEStatusBar run={run} runId={runId} />
    </div>
  )
}
