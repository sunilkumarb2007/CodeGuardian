import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { API_BASE_URL } from '../api/client'
import type { Run } from '../api/types'
import { useRun } from '../hooks/useRun'
import { BrandLoader, LogoMark } from '../components/Layout'
import { CursorFX } from '../components/CursorFX'
import { Card, Eyebrow, StatusBadge, StatusDot } from '../components/primitives'
import { EventFeed, StageList } from '../components/panels/pipeline'
import {
  EvidencePanel,
  GhostTracePanel,
  IncidentPanel,
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
import { AgentPanel } from '../components/workspace/AgentPanel'

const RUN_STATUS_LABEL: Record<Run['status'], string> = {
  queued: 'QUEUED',
  running: 'INVESTIGATION RUNNING',
  waiting_for_approval: 'AWAITING HUMAN APPROVAL',
  completed: 'INVESTIGATION COMPLETE',
  failed: 'RUN FAILED',
  rejected: 'PATCH REJECTED',
}

const SECTIONS = [
  'Overview',
  'Repository',
  'Evidence',
  'GhostTrace',
  'Memory',
  'Investigation',
  'Source',
  'Patch',
  'Replay',
  'Validation',
  'Delivery',
] as const

type Section = (typeof SECTIONS)[number]

const DOCK_TABS = ['Event timeline', 'Changed files', 'Command log', 'Run status'] as const

type DockTab = (typeof DOCK_TABS)[number]

function badgeStatus(status: Run['status']) {
  if (status === 'completed') return 'completed' as const
  if (status === 'failed' || status === 'rejected') return 'failed' as const
  if (status === 'waiting_for_approval') return 'waiting_for_approval' as const
  return 'running' as const
}

export default function Investigation() {
  const params = useParams<{ runId: string }>()
  const runId = params.runId ?? ''
  const { run, error, loading, deciding, approve, reject, decideFile, refresh } = useRun(runId)
  const [section, setSection] = useState<Section>('Overview')
  const [dock, setDock] = useState<DockTab>('Event timeline')

  const status = run?.status ?? 'queued'
  const busy = status === 'running' || status === 'queued'

  return (
    <div className="flex min-h-screen flex-col bg-ink-900" data-busy={busy}>
      <CursorFX />

      <header className="flex flex-wrap items-center gap-3 border-b-2 border-ink-700 bg-ink-850 px-5 py-3">
        <Link to="/" className="flex items-center gap-3" aria-label="CodeGuardian home">
          <LogoMark className={`h-8 w-8 ${busy ? 'animate-logoPulse' : ''}`} />
          <span className="font-display text-base font-bold tracking-tight">
            Code<span className="text-lime">Guardian</span>
          </span>
        </Link>
        <span className="pill border-ink-600 text-ink-300">
          {run?.repository?.name ?? run?.repositoryUrl ?? 'repository not reported'}
        </span>
        {run?.incident?.fingerprint ? (
          <span className="pill border-signal-pink/60 text-signal-pink">{run.incident.fingerprint}</span>
        ) : null}
        {run?.mode ? (
          <span className="pill border-lime/60 text-lime">{run.mode.toUpperCase()} MODE</span>
        ) : null}
        <StatusBadge status={badgeStatus(status)} label={RUN_STATUS_LABEL[status]} />
        <span className="ml-auto flex items-center gap-3">
          <span className="hidden font-mono text-[11px] text-ink-500 sm:inline">run {runId}</span>
          <Link to="/" className="btn-ghost py-2 text-xs">
            New investigation
          </Link>
        </span>
      </header>

      {error ? (
        <div className="p-5">
          <Card accent="pink" className="p-7">
            <Eyebrow>Backend unavailable</Eyebrow>
            <p className="mt-3 font-mono text-sm text-signal-pink">{error}</p>
            <p className="mt-4 max-w-2xl text-sm text-ink-300">
              This workspace only renders state reported by the CodeGuardian API
              {API_BASE_URL ? ` at ${API_BASE_URL}` : ''}. Nothing is simulated in the browser.
            </p>
            <button type="button" className="btn-ghost mt-6 py-3 text-sm" onClick={() => void refresh()}>
              Retry
            </button>
          </Card>
        </div>
      ) : null}

      {loading && !run ? (
        <div className="p-8">
          <Card className="p-10">
            <BrandLoader label="Connecting to run…" />
          </Card>
        </div>
      ) : null}

      {run ? (
        <>
          <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-[220px_minmax(0,1fr)_320px]">
            <nav className="border-b-2 border-ink-700 bg-ink-850 p-3 lg:border-b-0 lg:border-r-2">
              <p className="eyebrow px-2 pb-2">Workspace</p>
              <ul className="flex flex-wrap gap-1 lg:block lg:space-y-1">
                {SECTIONS.map((item) => (
                  <li key={item}>
                    <button
                      type="button"
                      onClick={() => setSection(item)}
                      className={`w-full rounded-lg px-3 py-2 text-left font-display text-sm font-semibold transition-colors ${
                        section === item ? 'bg-lime text-ink-900' : 'text-ink-300 hover:bg-ink-800'
                      }`}
                    >
                      {item}
                    </button>
                  </li>
                ))}
              </ul>
              <p className="eyebrow px-2 pb-2 pt-6">Stages</p>
              <ul className="space-y-1 px-2">
                {run.stages.map((stage) => (
                  <li key={stage.key} className="flex items-center gap-2 py-1">
                    <StatusDot status={stage.status} />
                    <span
                      className={`font-mono text-[11px] uppercase tracking-[0.12em] ${
                        stage.key === run.currentStage ? 'text-lime' : 'text-ink-400'
                      }`}
                    >
                      {stage.name}
                    </span>
                  </li>
                ))}
              </ul>
            </nav>

            <main className="min-w-0 space-y-5 overflow-y-auto p-5">
              {section === 'Overview' ? (
                <>
                  <IncidentPanel incident={run.incident} />
                  <StageList stages={run.stages} />
                </>
              ) : null}
              {section === 'Repository' ? <RepositoryPanel repository={run.repository} /> : null}
              {section === 'Evidence' ? <EvidencePanel evidence={run.evidence} /> : null}
              {section === 'GhostTrace' ? <GhostTracePanel trace={run.ghostTrace} /> : null}
              {section === 'Memory' ? (
                <>
                  <MemoryPanel memory={run.memory} />
                  <MemoryUpdatePanel update={run.memoryUpdate} />
                </>
              ) : null}
              {section === 'Investigation' ? <InvestigationPanel investigation={run.investigation} /> : null}
              {section === 'Source' ? (
                <>
                  <StackTracePanel stackTrace={run.stackTrace} />
                  <SourcePanel files={run.sourceFiles} investigation={run.investigation} />
                </>
              ) : null}
              {section === 'Patch' ? (
                <>
                  <PatchPanel patch={run.patch} />
                  <CompatibilityPanel compatibility={run.compatibility} />
                  <ChangedFilesPanel
                    files={run.changedFiles}
                    onDecide={(fileId, decision) => void decideFile(fileId, decision)}
                    decisionsLocked={run.status === 'completed' || run.status === 'rejected'}
                  />
                </>
              ) : null}
              {section === 'Replay' ? <ReplayPanel replay={run.replay} /> : null}
              {section === 'Validation' ? (
                <>
                  <CommandResultPanel
                    index="11"
                    title="Build"
                    caption="Build executed against the patched source."
                    result={run.build}
                  />
                  <CommandResultPanel
                    index="12"
                    title="Tests"
                    caption="Regression suite executed against the patched source."
                    result={run.tests}
                  />
                  <ValidationPanel validation={run.validation} />
                </>
              ) : null}
              {section === 'Delivery' ? <DeliveryPanel delivery={run.delivery} /> : null}

              {run.status === 'waiting_for_approval' ? (
                <ApprovalPanel
                  onApprove={() => void approve()}
                  onReject={() => void reject()}
                  busy={deciding}
                />
              ) : null}

              {run.status === 'rejected' ? (
                <Card accent="pink" className="p-8">
                  <Eyebrow>Patch rejected</Eyebrow>
                  <p className="mt-3 text-sm text-ink-300">
                    Delivery is blocked. No branch, commit or pull request was created for this run.
                  </p>
                </Card>
              ) : null}

              {run.status === 'completed' ? (
                <Card className="overflow-hidden bg-lime text-ink-900">
                  <div className="grid-bg animate-gridDrift px-8 py-12 text-center">
                    <LogoMark className="mx-auto mb-5 h-16 w-16 drop-shadow-none" />
                    <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-ink-900/60">
                      Investigation complete
                    </p>
                    <p className="display-md mt-3">Failure traced, repaired, validated.</p>
                  </div>
                </Card>
              ) : null}
            </main>

            <AgentPanel run={run} />
          </div>

          <section className="border-t-2 border-ink-700 bg-ink-850">
            <div className="flex flex-wrap gap-1 border-b-2 border-ink-700 px-3 py-2">
              {DOCK_TABS.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setDock(tab)}
                  className={`rounded-pill px-4 py-2 font-mono text-[11px] uppercase tracking-[0.18em] transition-colors ${
                    dock === tab ? 'bg-lime text-ink-900' : 'text-ink-400 hover:text-white'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>
            <div className="max-h-[42vh] overflow-y-auto p-4">
              {dock === 'Event timeline' ? <EventFeed events={run.events} /> : null}
              {dock === 'Changed files' ? (
                <ChangedFilesPanel
                  files={run.changedFiles}
                  onDecide={(fileId, decision) => void decideFile(fileId, decision)}
                  decisionsLocked={run.status === 'completed' || run.status === 'rejected'}
                />
              ) : null}
              {dock === 'Command log' ? <CommandLogPanel commands={run.commands} /> : null}
              {dock === 'Run status' ? <RunStatusPanel run={run} /> : null}
            </div>
          </section>
        </>
      ) : null}
    </div>
  )
}
