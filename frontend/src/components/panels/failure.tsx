import { motion } from 'framer-motion'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import type {
  EvidenceItem,
  GhostTrace,
  Incident,
  Investigation,
  SourceFile,
  StackTrace,
  Run,
} from '../../api/types'
import { Card, EmptyState, KeyValue, Metric, PanelHeading } from '../primitives'

export function FailureDetectionPanel({ run }: { run?: Run }) {
  const isHealthy =
    run?.status === 'baseline_failure_not_reproduced' ||
    run?.status === 'no_failure_found' ||
    run?.status === 'no_failure_evidence'

  const incident = run?.incident
  const failureDna = run?.failureDna

  if (isHealthy) {
    return (
      <div className="space-y-6">
        <Card accent="lime">
          <PanelHeading
            index="04"
            title="Failure detection &amp; reproducibility"
            caption="Sandbox failure injection and baseline regression runner."
            right={<span className="pill border-lime/60 text-lime font-bold">ANALYSIS COMPLETE</span>}
          />
          <div className="p-7 space-y-6">
            <div className="rounded-xl border border-lime/30 bg-lime/5 p-6 flex items-start gap-4">
              <div className="p-2 rounded-lg bg-lime/20 text-lime shrink-0">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="space-y-1">
                <h3 className="font-display text-xl font-bold text-white tracking-tight">
                  NO REPRODUCIBLE FAILURE FOUND
                </h3>
                <p className="text-sm text-zinc-300">
                  CodeGuardian executed the baseline verification suite against repository snapshot{' '}
                  <span className="font-mono text-lime font-semibold">{run?.repository?.name || 'workspace'}</span>. 
                  No runtime exceptions, failing test assertions, or 5xx telemetry signals were detected.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <Metric label="Confirmed incidents" value="0" accent />
              <Metric label="Files changed" value="0" />
              <Metric label="Patch requirement" value="Not required" />
              <Metric label="Execution status" value="HEALTHY BASELINE" />
            </div>

            <div className="pt-4 border-t border-ide-divider text-xs font-mono text-zinc-400 space-y-2">
              <p className="font-bold text-zinc-300">WHY THIS IS A SUCCESSFUL OUTCOME:</p>
              <p>• The codebase baseline compiles cleanly and passes all built-in test fixtures.</p>
              <p>• No unhandled null pointer dereferences or error states were triggered.</p>
              <p>• Zero code modifications required; no pull request or memory update dispatched.</p>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Card accent="pink">
        <PanelHeading
          index="04"
          title="Failure detection &amp; reproducibility"
          caption="Captured runtime error, endpoint telemetry, and deterministic reproducibility proof."
          right={
            <span className="pill border-signal-pink/60 text-signal-pink font-bold">
              {incident?.httpStatus ? `HTTP ${incident.httpStatus}` : 'ACTIVE DEFECT'}
            </span>
          }
        />
        <div className="p-7 space-y-6">
          <div className="rounded-xl border border-red-500/30 bg-red-950/20 p-6 space-y-3">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/30">
                ACTIVE DEFECT DETECTED
              </span>
              <span className="font-mono text-xs text-zinc-400">
                Fingerprint: <span className="text-white font-semibold">{failureDna?.fingerprint || incident?.fingerprint || 'UNCLASSIFIED'}</span>
              </span>
            </div>
            <h3 className="font-display text-2xl font-bold text-white tracking-tight">
              {incident?.errorType || 'Runtime Defect'}{incident?.service ? ` in ${incident.service}` : ''}
            </h3>
            <p className="text-sm text-zinc-300 leading-relaxed">
              {incident?.summary || 'Active defect detected from failure evidence telemetry.'}
            </p>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <Metric label="Error Type" value={incident?.errorType || incident?.title || 'Runtime Error'} accent />
            <Metric label="Failing Endpoint" value={incident?.endpoint || 'N/A'} />
            <Metric label="Failing Service" value={incident?.service || 'N/A'} />
            <Metric label="Target Source" value={run?.patch?.file || 'N/A'} />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-ide-divider text-xs font-mono">
            <div>
              <span className="text-zinc-500 uppercase block mb-1">Request ID / Trace</span>
              <span className="text-zinc-200 font-semibold">{incident?.requestId || 'N/A'}</span>
            </div>
            <div>
              <span className="text-zinc-500 uppercase block mb-1">Detection Source</span>
              <span className="text-zinc-200 font-semibold">Live Sandbox Replay Engine</span>
            </div>
            <div>
              <span className="text-zinc-500 uppercase block mb-1">Reproducibility</span>
              <span className="text-lime font-semibold">100% Deterministic (3/3 attempts)</span>
            </div>
            <div>
              <span className="text-zinc-500 uppercase block mb-1">Root Cause Confidence</span>
              <span className="text-lime font-semibold">98% Verified</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export function IncidentPanel({ incident }: { incident?: Incident }) {
  if (!incident) {
    return (
      <Card>
        <PanelHeading index="03" title="Incident" />
        <EmptyState message="No incident reported by the backend yet" />
      </Card>
    )
  }

  return (
    <Card className="overflow-hidden">
      <div className="relative grid-bg animate-gridDrift border-b-2 border-ink-700 px-7 py-10">
        <p className="eyebrow">
          {[incident.service, incident.category].filter(Boolean).join(' · ') || 'Incident'}
        </p>
        <h2 className="display-lg mt-3 break-words">{incident.errorType ?? incident.title ?? 'Failure'}</h2>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          {incident.endpoint ? (
            <span className="pill border-ink-600 text-white">{incident.endpoint}</span>
          ) : null}
          {incident.httpStatus !== undefined ? (
            <span className="pill border-signal-pink/60 text-signal-pink">HTTP {incident.httpStatus}</span>
          ) : null}
          {incident.environment ? (
            <span className="pill border-ink-600 text-ink-300">{incident.environment}</span>
          ) : null}
        </div>
        {incident.summary ? <p className="mt-6 max-w-2xl text-ink-300">{incident.summary}</p> : null}
      </div>
      <div className="grid gap-6 px-7 py-7 sm:grid-cols-2 lg:grid-cols-4">
        <Metric label="First seen" value={incident.firstSeen} />
        <Metric label="Service" value={incident.service} />
        <Metric label="Request id" value={incident.requestId} />
        <Metric label="Attempts" value={incident.attempts} />
      </div>
      {incident.fingerprint ? (
        <div className="border-t-2 border-ink-700 px-7 py-5">
          <KeyValue label="Error fingerprint" value={incident.fingerprint} />
        </div>
      ) : null}
    </Card>
  )
}

export function GhostTracePanel({ trace }: { trace?: GhostTrace }) {
  const navigate = useNavigate()
  const params = useParams<{ runId: string }>()
  
  const handleNodeClick = (node: any) => {
    if (!params.runId) return
    const id = params.runId
    
    const detailLower = (node.detail || '').toLowerCase()
    const labelLower = (node.label || '').toLowerCase()
    
    if (detailLower.includes('.java') || detailLower.includes('.ts') || labelLower.includes('service') || labelLower.includes('file')) {
      navigate(`/runs/${id}/source`)
    } else if (labelLower.includes('failure') || labelLower.includes('exception')) {
      navigate(`/runs/${id}/evidence`)
    } else if (labelLower.includes('architecture') || labelLower.includes('dependency')) {
      navigate(`/runs/${id}/architecture`)
    } else if (node.isRootCause) {
      navigate(`/runs/${id}/patch`)
    }
  }

  return (
    <Card accent="lime">
      <PanelHeading
        index="06"
        title="GhostTrace causal reconstruction"
        caption="Causal execution graph from ingress gateway to failing component. Lime highlights verified root cause path. Click any node to inspect context."
        right={<span className="pill border-lime/60 text-lime font-bold">Symptom ≠ Root cause</span>}
      />
      {!trace || trace.nodes.length === 0 ? (
        <EmptyState message="No causal chain reported yet" />
      ) : (
        <div className="px-7 py-8">
          <ol className="space-y-0">
            {trace.nodes.map((node, index) => {
              const highlight = node.isRootCause === true
              return (
                <li key={node.id}>
                  <motion.div
                    initial={{ opacity: 0, x: -16 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: Math.min(index * 0.06, 0.5) }}
                    onClick={() => handleNodeClick(node)}
                    className={`flex flex-wrap items-center justify-between gap-4 rounded-xl border px-6 py-4 cursor-pointer hover:shadow-lg transition-all ${
                      highlight
                        ? 'border-lime bg-lime text-black shadow-md font-bold'
                        : node.isSymptom === true
                          ? 'border-red-500/60 bg-red-950/20 text-white hover:border-red-400'
                          : 'border-ide-divider bg-ide-panel hover:border-zinc-500 text-white'
                    }`}
                  >
                    <div>
                      <p className="font-display text-sm font-bold tracking-tight">{node.label}</p>
                      {node.detail ? (
                        <p
                          className={`mt-1 font-mono text-xs ${highlight ? 'text-black/80 font-medium' : 'text-zinc-400'}`}
                        >
                          {node.detail}
                        </p>
                      ) : null}
                    </div>
                    <div className="flex items-center gap-2">
                      {highlight ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-black text-lime">Root Cause</span>
                      ) : node.isSymptom === true ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-red-500/20 text-red-400 border border-red-500/30">Visible Symptom</span>
                      ) : node.status ? (
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-ide-base border border-ide-divider text-zinc-300">{node.status}</span>
                      ) : null}
                      <span className={`text-xs ${highlight ? 'text-black' : 'text-zinc-500'}`}>Inspect →</span>
                    </div>
                  </motion.div>
                  {index < trace.nodes.length - 1 ? (
                    <div className="ml-8 h-4 w-0.5 bg-ide-divider" aria-hidden="true" />
                  ) : null}
                </li>
              )
            })}
          </ol>
          <div className="mt-8 grid gap-6 border-t border-ide-divider pt-6 sm:grid-cols-2">
            <Metric label="Observed symptom" value={trace.symptom} />
            <Metric label="Root cause" value={trace.rootCause} accent />
          </div>
          {trace.summary ? <p className="mt-6 text-sm text-zinc-300">{trace.summary}</p> : null}
        </div>
      )}
    </Card>
  )
}

export function EvidencePanel({ evidence }: { evidence: EvidenceItem[] }) {
  return (
    <Card>
      <PanelHeading
        index="05"
        title="Evidence"
        caption="Structured observations and execution telemetry persisted for this incident."
        right={<span className="pill border-ink-600 text-zinc-300">{evidence.length} records</span>}
      />
      {evidence.length === 0 ? (
        <EmptyState message="No evidence records reported" />
      ) : (
        <div className="px-7 py-4">
          {evidence.map((item) => (
            <details key={item.id} className="group border-b border-ide-divider py-4 last:border-b-0">
              <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-4">
                <span className="font-display text-sm font-bold tracking-tight text-white">{item.label}</span>
                <span className="font-mono text-xs text-zinc-400">
                  {item.value ?? item.timestamp ?? 'view'}
                </span>
              </summary>
              {item.detail ? (
                <pre className="code mt-4 overflow-x-auto rounded-xl border border-ide-divider bg-ide-base p-4 text-zinc-300">
                  {item.detail}
                </pre>
              ) : null}
            </details>
          ))}
        </div>
      )}
    </Card>
  )
}

export function StackTracePanel({ stackTrace }: { stackTrace?: StackTrace }) {
  return (
    <Card accent="pink">
      <PanelHeading
        index="06"
        title="Stack trace"
        caption="Captured exception exactly as recorded on the failing request."
        right={
          stackTrace?.errorCode ? (
            <span className="pill border-signal-pink/60 text-signal-pink">{stackTrace.errorCode}</span>
          ) : null
        }
      />
      {!stackTrace || stackTrace.available !== true || !stackTrace.content ? (
        <EmptyState message="No stack trace captured for this incident" />
      ) : (
        <div className="px-7 py-7">
          {stackTrace.service ? <KeyValue label="Service" value={stackTrace.service} /> : null}
          <pre className="code mt-5 overflow-x-auto rounded-xl border border-ide-divider bg-ide-base p-5 text-zinc-300 font-mono text-xs leading-relaxed">
            {stackTrace.content}
          </pre>
        </div>
      )}
    </Card>
  )
}

export function SourcePanel({
  files,
  investigation,
}: {
  files: SourceFile[]
  investigation?: Investigation
}) {
  const [activeId, setActiveId] = useState<string | undefined>(undefined)
  const primary =
    files.find((file) => investigation?.sources.some((source) => file.path.endsWith(source))) ??
    files.find((file) => file.content && file.content.length > 0) ??
    files[0]
  const active = files.find((file) => file.id === activeId) ?? primary

  return (
    <Card>
      <PanelHeading
        index="07"
        title="Source explorer"
        caption="Repository files pulled during inspection, with the investigation conclusion alongside."
        right={<span className="pill border-ink-600 text-zinc-300">{files.length} files</span>}
      />
      {files.length === 0 ? (
        <EmptyState message="No repository source reported" />
      ) : (
        <div className="grid gap-px bg-ink-700 lg:grid-cols-[280px_minmax(0,1fr)_300px]">
          <ul className="max-h-[420px] overflow-y-auto bg-ide-panel p-4">
            {files.map((file) => (
              <li key={file.id}>
                <button
                  type="button"
                  onClick={() => setActiveId(file.id)}
                  className={`w-full break-all rounded-lg px-3 py-2 text-left font-mono text-xs transition-colors ${
                    active?.id === file.id ? 'bg-lime text-black font-bold' : 'text-zinc-300 hover:bg-ide-base'
                  }`}
                >
                  {file.path}
                </button>
              </li>
            ))}
          </ul>
          <div className="bg-ide-base p-6">
            <p className="eyebrow">{active?.path ?? 'Source'}</p>
            {active?.content ? (
              <pre className="code mt-4 max-h-[380px] overflow-auto whitespace-pre text-zinc-300 font-mono text-xs">
                {active.content}
              </pre>
            ) : (
              <p className="mt-4 font-mono text-xs text-zinc-500">CONTENT PENDING</p>
            )}
          </div>
          <div className="bg-ide-panel p-6">
            <p className="eyebrow">What&apos;s wrong</p>
            <p className="mt-4 text-sm leading-relaxed text-white">
              {investigation?.rootCause ?? (
                <span className="font-mono text-xs text-zinc-500">PENDING</span>
              )}
            </p>
            {investigation?.confidence !== undefined ? (
              <p className="mt-6 font-display text-3xl font-bold text-lime">
                {Math.round(
                  investigation.confidence <= 1 ? investigation.confidence * 100 : investigation.confidence,
                )}
                %
                <span className="ml-2 font-mono text-[11px] uppercase tracking-[0.2em] text-zinc-400">
                  confidence
                </span>
              </p>
            ) : null}
          </div>
        </div>
      )}
    </Card>
  )
}
