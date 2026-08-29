import { useState, useEffect, useMemo } from 'react'
import { useParams, useNavigate, useLocation } from 'react-router-dom'
import { useRun } from '../hooks/useRun'
import { CursorFX } from '../components/CursorFX'
import { Card } from '../components/primitives'
import { BrandLoader } from '../components/Layout'

import { IDEHeader } from '../components/workspace/IDEHeader'
import { IDESidebar, type WorkspaceSection } from '../components/workspace/IDESidebar'
import { IDEStatusBar } from '../components/workspace/IDEStatusBar'
import { TraceOverviewPanel } from '../components/workspace/TraceOverviewPanel'
import { AutoFixAgentPanel } from '../components/workspace/AutoFixAgentPanel'
import { IDESourceWorkspace } from '../components/workspace/IDESourceWorkspace'

import {
  EvidencePanel,
  GhostTracePanel,
  StackTracePanel,
  FailureDetectionPanel,
} from '../components/panels/failure'
import { RepositoryPanel, RunStatusPanel, InspectionPanel, ArchitecturePanel } from '../components/panels/discovery'
import {
  ApprovalPanel,
  ChangedFilesPanel,
  CommandLogPanel,
  BuildPanel,
  TestsPanel,
  CompatibilityPanel,
  DeliveryPanel,
  InvestigationPanel,
  MemoryPanel,
  MemoryUpdatePanel,
  PatchPanel,
  ReplayPanel,
  ValidationPanel,
  EventHistoryPanel,
} from '../components/panels/repair'
import { FailureDNAPanel } from '../components/panels/FailureDNAPanel'
import { RepairLabPanel } from '../components/panels/RepairLabPanel'
import { BlastRadiusPanel } from '../components/panels/BlastRadiusPanel'
import { ImmunizationPanel } from '../components/panels/ImmunizationPanel'
import { FailureLabPanel } from '../components/panels/FailureLabPanel'
import { CapsulePanel } from '../components/panels/CapsulePanel'

type TabType = 'Trace Overview' | 'Stack Trace' | 'Events' | 'Request' | 'Response' | 'Metadata'

const TABS: TabType[] = [
  'Trace Overview',
  'Stack Trace',
  'Events',
  'Request',
  'Response',
  'Metadata',
]

export default function Investigation() {
  const navigate = useNavigate()
  const location = useLocation()
  const params = useParams<{ runId: string; '*': string }>()
  const runId = params.runId ?? ''
  const { run, error, loading, deciding, approve, reject, decideFile } = useRun(runId)

  const [activeSection, setActiveSection] = useState<WorkspaceSection>('Overview')
  const [activeTab, setActiveTab] = useState<TabType>('Trace Overview')
  const [isSourceFullScreen, setIsSourceFullScreen] = useState(false)

  const isHealthyRun =
    run?.status === 'baseline_failure_not_reproduced' ||
    run?.status === 'no_failure_found' ||
    run?.status === 'no_failure_evidence'

  const displayRunId = runId ? `INV-${runId.slice(0, 4).toUpperCase()}` : 'INV-710B'
  const incidentTitle = isHealthyRun ? 'ANALYSIS COMPLETE' : (run?.incident?.title || run?.incident?.errorType || 'NO INCIDENT TITLE')
  const incidentDescription = isHealthyRun ? 'No reproducible failure found against repository baseline.' : (run?.incident?.summary || 'No incident summary available.')
  const httpStatus = isHealthyRun ? '200 OK' : (run?.incident?.httpStatus ?? 'N/A')
  const endpoint = isHealthyRun ? '/api/health' : (run?.incident?.endpoint ?? 'N/A')
  const serviceName = run?.incident?.service ?? run?.repository?.name ?? 'UNKNOWN'
  const requestId = run?.incident?.requestId ?? 'N/A'
  const firstSeen = run?.incident?.firstSeen ?? 'RECORDED'
  const environment = run?.incident?.environment ?? 'UNKNOWN'
  const fingerprint = isHealthyRun ? 'HEALTHY_BASELINE' : (run?.incident?.fingerprint ?? 'PENDING')
  const attempts = isHealthyRun ? '3 / 3 (Passed)' : (run?.incident?.attempts !== undefined ? `${run.incident.attempts} / 3` : '0 / 3')

  // Extract path subsegment after /runs/:runId/
  const subpath = useMemo(() => {
    const prefix = `/runs/${runId}`
    if (location.pathname.startsWith(prefix)) {
      const rest = location.pathname.slice(prefix.length).replace(/^\/+/, '').toLowerCase()
      return rest.replace(/^stages\//, '')
    }
    return ''
  }, [location.pathname, runId])

  // Sync URL subpath with activeSection
  useEffect(() => {
    if (!subpath || subpath === 'overview') {
      setActiveSection('Overview')
    } else if (subpath === 'failure-dna' || subpath === 'failuredna') {
      setActiveSection('Failure DNA')
    } else if (subpath === 'repair-lab' || subpath === 'repairlab') {
      setActiveSection('Repair Lab')
    } else if (subpath === 'blast-radius' || subpath === 'blastradius') {
      setActiveSection('Blast Radius')
    } else if (subpath === 'immunization') {
      setActiveSection('Immunization')
    } else if (subpath === 'failure-lab' || subpath === 'failurelab') {
      setActiveSection('Failure Lab')
    } else if (subpath === 'capsule') {
      setActiveSection('Capsule')
    } else if (subpath === 'repository' || subpath === '01_repository') {
      setActiveSection('Repository')
    } else if (subpath === 'inspection' || subpath === '02_inspection') {
      setActiveSection('Inspection')
    } else if (subpath === 'architecture' || subpath === '03_architecture') {
      setActiveSection('Architecture')
    } else if (subpath === 'failure-detection' || subpath === '04_failure_detection' || subpath === 'failure') {
      setActiveSection('Failure Detection')
    } else if (subpath === 'evidence' || subpath === '05_evidence') {
      setActiveSection('Evidence')
    } else if (subpath === 'ghosttrace' || subpath === 'ghost-trace' || subpath === '06_ghost_trace') {
      setActiveSection('GhostTrace')
    } else if (subpath === 'memory' || subpath === '07_failure_memory' || subpath === 'failure-memory') {
      setActiveSection('Memory')
    } else if (subpath === 'investigation' || subpath === '08_investigation') {
      setActiveSection('Investigation')
    } else if (subpath === 'source') {
      setActiveSection('Source')
    } else if (subpath === 'patch' || subpath === '09_patch') {
      setActiveSection('Patch')
    } else if (subpath === 'compatibility' || subpath === '10_compatibility') {
      setActiveSection('Compatibility')
    } else if (subpath === 'replay' || subpath === '11_replay') {
      setActiveSection('Replay')
    } else if (subpath === 'build' || subpath === '12_build') {
      setActiveSection('Build')
    } else if (subpath === 'tests' || subpath === '13_tests') {
      setActiveSection('Tests')
    } else if (subpath === 'validation' || subpath === '14_validation') {
      setActiveSection('Validation')
    } else if (subpath === 'human-approval' || subpath === '15_human_approval' || subpath === 'approval') {
      setActiveSection('Human Approval')
    } else if (subpath === 'delivery' || subpath === '16_delivery') {
      setActiveSection('Delivery')
    } else if (subpath === 'memory-update' || subpath === '17_memory_update') {
      setActiveSection('Memory Update')
    } else {
      setActiveSection('Overview')
    }
  }, [subpath])

  const handleNavigateSection = (section: string) => {
    const slug = section.toLowerCase().replace(/\s+/g, '-')
    navigate(`/runs/${runId}/${slug}`)
  }

  const handleSelectStage = (stageKey: string) => {
    const base = stageKey.replace(/^\d+_/, '')
    if (base === 'repository') handleNavigateSection('repository')
    else if (base === 'inspection') handleNavigateSection('inspection')
    else if (base === 'architecture') handleNavigateSection('architecture')
    else if (base === 'failure_detection' || base === 'failure') handleNavigateSection('failure-detection')
    else if (base === 'evidence') handleNavigateSection('evidence')
    else if (base === 'ghost_trace' || base === 'ghosttrace') handleNavigateSection('ghosttrace')
    else if (base === 'failure_memory') handleNavigateSection('memory')
    else if (base === 'investigation') handleNavigateSection('investigation')
    else if (base === 'patch') handleNavigateSection('patch')
    else if (base === 'compatibility') handleNavigateSection('compatibility')
    else if (base === 'replay') handleNavigateSection('replay')
    else if (base === 'build') handleNavigateSection('build')
    else if (base === 'tests') handleNavigateSection('tests')
    else if (base === 'validation') handleNavigateSection('validation')
    else if (base === 'human_approval') handleNavigateSection('human-approval')
    else if (base === 'delivery') handleNavigateSection('delivery')
    else if (base === 'memory_update') handleNavigateSection('memory-update')
    else handleNavigateSection('overview')
  }

  return (
    <div className="flex h-screen flex-col bg-ide-base text-white font-sans overflow-hidden select-none">
      <CursorFX />

      {/* 1. Global Top IDE Header */}
      <IDEHeader
        run={run}
        runId={runId}
        isFullScreen={isSourceFullScreen}
        onToggleFullScreen={() => setIsSourceFullScreen(!isSourceFullScreen)}
      />

      {/* Error Banner if API failed */}
      {error ? (
        <div className="bg-red-500/10 border-b border-red-500/20 px-4 py-2 text-xs text-red-400 font-mono flex items-center justify-between">
          <span>Failed to connect to CodeGuardian backend: {error}</span>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="text-white underline hover:no-underline font-semibold"
          >
            Retry
          </button>
        </div>
      ) : null}

      {/* 2. Main 3-Column IDE Workspace Grid */}
      {loading && !run ? (
        <div className="flex-1 flex items-center justify-center bg-ide-base">
          <BrandLoader label="Connecting to sandboxed investigation environment..." />
        </div>
      ) : (
        <div className="flex flex-1 min-h-0 relative overflow-hidden">
          {/* Column A: Persistent Left Sidebar (Workspace & 17 Stages) */}
          <IDESidebar
            activeSection={activeSection}
            onSelectSection={(s) => handleNavigateSection(s)}
            run={run}
            onSelectStage={handleSelectStage}
          />

          {/* Column B: Primary IDE Workspace Area */}
          <main
            tabIndex={0}
            role="main"
            aria-label="Investigation workspace main content"
            className="flex-1 flex flex-col min-w-0 bg-ide-base overflow-y-auto focus:outline-none"
          >
            {/* Context Breadcrumbs */}
            <div className="px-6 py-2.5 border-b border-ide-divider flex items-center justify-between text-xs font-mono text-zinc-400 bg-ide-panel/40 shrink-0">
              <div className="flex items-center gap-2">
                <span className="text-zinc-500">runs</span>
                <span>/</span>
                <span className="text-lime font-semibold">{displayRunId}</span>
                <span>/</span>
                <span className="text-white font-bold">{activeSection}</span>
              </div>
              <div className="flex items-center gap-4 text-[11px]">
                <span className="text-zinc-500">
                  Target:{' '}
                  <span className="text-zinc-300 font-semibold">{run?.repository?.name || serviceName}</span>
                </span>
                <span className="text-zinc-500">
                  Status:{' '}
                  <span className={`font-semibold ${isHealthyRun ? 'text-lime' : run?.status === 'completed' ? 'text-lime' : 'text-amber-400'}`}>
                    {isHealthyRun ? 'HEALTHY (NO DEFECT)' : (run?.status || 'RUNNING').toUpperCase()}
                  </span>
                </span>
              </div>
            </div>

            {/* Content Display Area */}
            <div className="p-6 space-y-6 max-w-7xl w-full mx-auto">
              {/* Executive Incident Header (Only on Overview) */}
              {activeSection === 'Overview' ? (
                <div className="rounded-xl border border-ide-divider bg-ide-panel p-5 space-y-4">
                  {/* Top Chips Row */}
                  <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
                    <span className="px-2 py-0.5 rounded bg-lime/10 border border-lime/30 text-lime font-semibold">
                      {serviceName}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-zinc-300">
                      {endpoint}
                    </span>
                    <span className={`px-2 py-0.5 rounded border font-semibold ${
                      isHealthyRun ? 'bg-lime/10 border-lime/30 text-lime' : 'bg-red-500/10 border-red-500/30 text-red-400'
                    }`}>
                      HTTP {httpStatus}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-zinc-300">
                      {environment}
                    </span>
                  </div>

                  {/* Title & Description */}
                  <div className="space-y-1">
                    <h2 className="font-display text-2xl font-bold text-white tracking-tight">
                      {incidentTitle}
                    </h2>
                    <p className="text-xs text-zinc-400 leading-relaxed max-w-4xl">
                      {incidentDescription}
                    </p>
                  </div>

                  {/* Incident Quick Metrics Grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-3 border-t border-ide-divider text-xs font-mono">
                    <div>
                      <span className="text-zinc-500 block text-[10px]">FIRST RECORDED</span>
                      <span className="text-zinc-300 font-semibold">{firstSeen}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px]">REPRODUCIBILITY</span>
                      <span className="text-zinc-300 font-semibold">{attempts}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px]">ROOT CAUSE SERVICE</span>
                      <span className="text-zinc-300 font-semibold">{serviceName}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px]">ERROR FINGERPRINT</span>
                      <span className="text-lime font-semibold">{fingerprint}</span>
                    </div>
                  </div>
                </div>
              ) : null}

              {/* Tab Navigation (Only in Overview) */}
              {activeSection === 'Overview' ? (
                <div className="border-b border-ide-divider flex items-center gap-1 overflow-x-auto">
                  {TABS.map((tab) => {
                    const isActive = activeTab === tab
                    return (
                      <button
                        key={tab}
                        type="button"
                        onClick={() => setActiveTab(tab)}
                        className={`px-4 py-2 text-xs font-mono font-medium rounded-t-lg transition-colors border-b-2 whitespace-nowrap ${
                          isActive
                            ? 'border-lime text-lime bg-ide-panel/80 font-bold'
                            : 'border-transparent text-zinc-400 hover:text-zinc-200 hover:bg-ide-panel/40'
                        }`}
                      >
                        {tab}
                        {tab === 'Events' && run?.events ? ` (${run.events.length})` : ''}
                      </button>
                    )
                  })}
                </div>
              ) : null}

              {/* Tab Content Display (Only in Overview) */}
              {activeSection === 'Overview' && activeTab === 'Trace Overview' ? (
                <TraceOverviewPanel trace={run?.ghostTrace} incident={run?.incident} />
              ) : null}

              {activeSection === 'Overview' && activeTab === 'Stack Trace' ? (
                <StackTracePanel stackTrace={run?.stackTrace} />
              ) : null}

              {activeSection === 'Overview' && activeTab === 'Events' ? (
                <EventHistoryPanel events={run?.events ?? []} commands={run?.commands ?? []} />
              ) : null}

              {activeSection === 'Overview' && activeTab === 'Request' ? (
                <Card>
                  <div className="p-6">
                    <p className="eyebrow mb-2">Request Payload</p>
                    <pre className="code font-mono text-xs text-zinc-300 bg-ide-base p-4 rounded-xl border border-ide-divider overflow-x-auto">
                      {run?.incident?.requestPayload
                        ? JSON.stringify(run.incident.requestPayload, null, 2)
                        : JSON.stringify(
                            {
                              method: 'POST',
                              endpoint: endpoint,
                              headers: { 'Content-Type': 'application/json' },
                              body: run?.incident?.payload ?? {
                                transaction_id: 'tx_live_9941a',
                                amount: 25000,
                                currency: 'USD',
                                merchant: null,
                              },
                            },
                            null,
                            2,
                          )}
                    </pre>
                  </div>
                </Card>
              ) : null}

              {activeSection === 'Overview' && activeTab === 'Response' ? (
                <Card>
                  <div className="p-6">
                    <p className="eyebrow mb-2">Response Payload</p>
                    <pre className="code font-mono text-xs text-zinc-300 bg-ide-base p-4 rounded-xl border border-ide-divider overflow-x-auto">
                      {run?.incident?.responsePayload
                        ? JSON.stringify(run.incident.responsePayload, null, 2)
                        : JSON.stringify(
                            {
                              status: isHealthyRun ? 200 : (run?.incident?.httpStatus ?? 500),
                              error: isHealthyRun ? null : (run?.incident?.errorType ?? 'Internal Server Error'),
                              message: incidentDescription,
                              timestamp: new Date().toISOString(),
                            },
                            null,
                            2,
                          )}
                    </pre>
                  </div>
                </Card>
              ) : null}

              {activeSection === 'Overview' && activeTab === 'Metadata' ? (
                <div className="rounded-xl border border-ide-divider bg-ide-panel p-6 space-y-4 font-mono text-xs">
                  <p className="eyebrow">Incident Diagnostic Metadata</p>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <span className="text-zinc-500 block text-[10px]">ENVIRONMENT</span>
                      <span className="text-zinc-300">{environment}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px]">RECORDED AT</span>
                      <span className="text-zinc-300">{firstSeen}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px]">TRACE ID</span>
                      <span className="text-zinc-300">{requestId}</span>
                    </div>
                    <div>
                      <span className="text-zinc-500 block text-[10px]">FINGERPRINT</span>
                      <span className="text-zinc-200">{fingerprint}</span>
                    </div>
                  </div>
                </div>
              ) : null}

              {/* Workspace Sections Content */}
              {activeSection === 'Failure DNA' ? (
                <FailureDNAPanel dna={run?.failureDna} />
              ) : activeSection === 'Repair Lab' ? (
                <RepairLabPanel candidates={run?.repairCandidates} />
              ) : activeSection === 'Blast Radius' ? (
                <BlastRadiusPanel impact={run?.impactAnalysis} />
              ) : activeSection === 'Immunization' ? (
                <ImmunizationPanel immunization={run?.immunization} />
              ) : activeSection === 'Failure Lab' ? (
                <FailureLabPanel />
              ) : activeSection === 'Capsule' ? (
                <CapsulePanel runId={runId} capsule={run?.capsule} />
              ) : activeSection === 'Repository' ? (
                <div className="space-y-6">
                  <RepositoryPanel repository={run?.repository} />
                  {run ? <RunStatusPanel run={run} /> : null}
                </div>
              ) : activeSection === 'Inspection' ? (
                <InspectionPanel
                  repository={run?.repository}
                  sourceFiles={run?.sourceFiles}
                  durationMs={run?.stages?.find((s) => s.key.includes('inspection'))?.durationMs}
                />
              ) : activeSection === 'Architecture' ? (
                <ArchitecturePanel repository={run?.repository} />
              ) : activeSection === 'Failure Detection' ? (
                <FailureDetectionPanel run={run} />
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
              ) : activeSection === 'Source' ? (
                <IDESourceWorkspace
                  files={run?.sourceFiles ?? []}
                  investigation={run?.investigation}
                  stackTrace={run?.stackTrace}
                  isFullScreen={isSourceFullScreen}
                  onToggleFullScreen={() => setIsSourceFullScreen(!isSourceFullScreen)}
                  onBackToInvestigation={() => handleNavigateSection('overview')}
                />
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
              ) : activeSection === 'Compatibility' ? (
                <CompatibilityPanel compatibility={run?.compatibility} />
              ) : activeSection === 'Replay' ? (
                <ReplayPanel replay={run?.replay} runStatus={run?.status} />
              ) : activeSection === 'Build' ? (
                <BuildPanel build={run?.build} runStatus={run?.status} />
              ) : activeSection === 'Tests' ? (
                <TestsPanel tests={run?.tests} runStatus={run?.status} />
              ) : activeSection === 'Validation' ? (
                <div className="space-y-6">
                  <BuildPanel build={run?.build} runStatus={run?.status} />
                  <TestsPanel tests={run?.tests} runStatus={run?.status} />
                  <ValidationPanel validation={run?.validation} runStatus={run?.status} />
                </div>
              ) : activeSection === 'Human Approval' ? (
                <ApprovalPanel
                  run={run}
                  onApprove={() => void approve()}
                  onReject={() => void reject()}
                  busy={deciding}
                />
              ) : activeSection === 'Delivery' ? (
                <DeliveryPanel delivery={run?.delivery} />
              ) : activeSection === 'Memory Update' ? (
                <MemoryUpdatePanel update={run?.memoryUpdate} />
              ) : null}

              {/* Human Approval Gate Banner if waiting */}
              {run?.status === 'waiting_for_approval' && activeSection !== 'Human Approval' ? (
                <div className="mt-8">
                  <ApprovalPanel
                    run={run}
                    onApprove={() => void approve()}
                    onReject={() => void reject()}
                    busy={deciding}
                  />
                </div>
              ) : null}
            </div>
          </main>

          {/* Column C: Persistent Right AI Agent (AutoFix) (~300-320px) */}
          <AutoFixAgentPanel
            run={run}
            onQuickAction={(action) => {
              if (action === 'overview') {
                handleNavigateSection('overview')
              } else if (action === 'investigation') {
                handleNavigateSection('investigation')
              } else if (action === 'logs' || action === 'events') {
                handleNavigateSection('overview')
                setActiveTab('Events')
              } else if (action === 'source') {
                handleNavigateSection('source')
              } else if (action === 'delivery' || action === 'issue') {
                handleNavigateSection('delivery')
              } else if (['patch', 'replay', 'validation', 'ghosttrace', 'memory', 'inspection', 'architecture', 'build', 'tests'].includes(action)) {
                handleNavigateSection(action)
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
