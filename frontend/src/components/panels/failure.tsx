import { motion } from 'framer-motion'
import { useState } from 'react'
import type {
  EvidenceItem,
  GhostTrace,
  Incident,
  Investigation,
  SourceFile,
  StackTrace,
} from '../../api/types'
import { Card, EmptyState, KeyValue, Metric, PanelHeading } from '../primitives'

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
  return (
    <Card accent="lime">
      <PanelHeading
        index="04"
        title="GhostTrace"
        caption="Reconstructed causal chain. Lime marks the path that actually caused the failure."
        right={<span className="pill border-lime/60 text-lime">Symptom ≠ Root cause</span>}
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
                    className={`flex flex-wrap items-center justify-between gap-4 rounded-card border-2 px-6 py-5 ${
                      highlight
                        ? 'border-lime bg-lime text-ink-900'
                        : node.isSymptom === true
                          ? 'border-signal-pink/60 bg-ink-800'
                          : 'border-ink-700 bg-ink-800'
                    }`}
                  >
                    <div>
                      <p className="font-display text-base font-bold tracking-tight">{node.label}</p>
                      {node.detail ? (
                        <p
                          className={`mt-1 font-mono text-xs ${highlight ? 'text-ink-900/70' : 'text-ink-400'}`}
                        >
                          {node.detail}
                        </p>
                      ) : null}
                    </div>
                    {highlight ? (
                      <span className="pill border-ink-900 text-ink-900">Root cause</span>
                    ) : node.isSymptom === true ? (
                      <span className="pill border-signal-pink/60 text-signal-pink">Visible symptom</span>
                    ) : node.status ? (
                      <span className="pill border-ink-600 text-ink-300">{node.status}</span>
                    ) : null}
                  </motion.div>
                  {index < trace.nodes.length - 1 ? (
                    <div className="ml-8 h-6 w-0.5 bg-ink-600" aria-hidden="true" />
                  ) : null}
                </li>
              )
            })}
          </ol>
          <div className="mt-8 grid gap-6 border-t-2 border-ink-700 pt-6 sm:grid-cols-2">
            <Metric label="Observed symptom" value={trace.symptom} />
            <Metric label="Root cause" value={trace.rootCause} accent />
          </div>
          {trace.summary ? <p className="mt-6 text-sm text-ink-300">{trace.summary}</p> : null}
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
        caption="Structured observations persisted for this incident."
        right={<span className="pill border-ink-600 text-ink-300">{evidence.length} records</span>}
      />
      {evidence.length === 0 ? (
        <EmptyState message="No evidence records reported" />
      ) : (
        <div className="px-7 py-4">
          {evidence.map((item) => (
            <details key={item.id} className="group border-b border-ink-700 py-4 last:border-b-0">
              <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-4">
                <span className="font-display text-sm font-bold tracking-tight">{item.label}</span>
                <span className="font-mono text-xs text-ink-400">
                  {item.value ?? item.timestamp ?? 'view'}
                </span>
              </summary>
              {item.detail ? (
                <pre className="code mt-4 overflow-x-auto rounded-2xl border-2 border-ink-700 bg-ink-900 p-4 text-ink-300">
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
        caption="The captured exception exactly as recorded on the failing request."
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
          <pre className="code mt-5 overflow-x-auto rounded-2xl border-2 border-ink-700 bg-ink-900 p-5 text-ink-300">
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
        title="Source"
        caption="Repository files pulled during inspection, with the investigation conclusion alongside."
        right={<span className="pill border-ink-600 text-ink-300">{files.length} files</span>}
      />
      {files.length === 0 ? (
        <EmptyState message="No repository source reported" />
      ) : (
        <div className="grid gap-px bg-ink-700 lg:grid-cols-[280px_minmax(0,1fr)_300px]">
          <ul className="max-h-[420px] overflow-y-auto bg-ink-850 p-4">
            {files.map((file) => (
              <li key={file.id}>
                <button
                  type="button"
                  onClick={() => setActiveId(file.id)}
                  className={`w-full break-all rounded-lg px-3 py-2 text-left font-mono text-xs transition-colors ${
                    active?.id === file.id ? 'bg-lime text-ink-900' : 'text-ink-300 hover:bg-ink-800'
                  }`}
                >
                  {file.path}
                </button>
              </li>
            ))}
          </ul>
          <div className="bg-ink-900 p-6">
            <p className="eyebrow">{active?.path ?? 'Source'}</p>
            {active?.content ? (
              <pre className="code mt-4 max-h-[380px] overflow-auto whitespace-pre text-ink-300">
                {active.content}
              </pre>
            ) : (
              <p className="mt-4 font-mono text-xs text-ink-500">file content not reported</p>
            )}
          </div>
          <div className="bg-ink-850 p-6">
            <p className="eyebrow">What&apos;s wrong</p>
            <p className="mt-4 text-sm leading-relaxed text-white">
              {investigation?.rootCause ?? (
                <span className="font-mono text-xs text-ink-500">not reported</span>
              )}
            </p>
            {investigation?.confidence !== undefined ? (
              <p className="mt-6 font-display text-3xl font-bold text-lime">
                {Math.round(
                  investigation.confidence <= 1 ? investigation.confidence * 100 : investigation.confidence,
                )}
                %
                <span className="ml-2 font-mono text-[11px] uppercase tracking-[0.2em] text-ink-400">
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
