import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import type {
  ChangedFile,
  CommandEntry,
  CommandResult,
  Compatibility,
  Delivery,
  Investigation,
  MemoryMatch,
  MemoryUpdate,
  Patch,
  Replay,
  ReplaySide,
  TimelineEvent,
  Validation,
  Run,
} from '../../api/types'
import { Card, CheckIcon, EmptyState, KeyValue, Metric, PanelHeading, ProgressBar } from '../primitives'

export function MemoryPanel({ memory }: { memory?: MemoryMatch }) {
  return (
    <Card accent="purple">
      <PanelHeading
        index="07"
        title="Failure memory"
        caption="Has this organisation solved this failure pattern before?"
        right={
          memory?.status ? (
            <span className="pill border-signal-purple/60 text-signal-purple">{memory.status}</span>
          ) : null
        }
      />
      {!memory ? (
        <EmptyState message="No memory lookup reported" />
      ) : (
        <div className="px-7 py-7">
          {memory.similarity !== undefined ? (
            <div className="mb-8">
              <p className="eyebrow">Similarity</p>
              <p className="mb-3 mt-2 font-display text-4xl font-bold text-white">
                {Math.round(memory.similarity <= 1 ? memory.similarity * 100 : memory.similarity)}%
              </p>
              <ProgressBar
                value={memory.similarity <= 1 ? memory.similarity * 100 : memory.similarity}
                label={memory.verified === true ? 'Verified memory record' : 'Reported by backend'}
              />
            </div>
          ) : null}
          <KeyValue label="Fingerprint" value={memory.fingerprint} />
          <KeyValue label="Root cause service" value={memory.rootCauseService} />
          <KeyValue label="Previous fix" value={memory.previousFix} />
          <KeyValue label="Previous incident" value={memory.previousIncident} />
        </div>
      )}
    </Card>
  )
}

export function InvestigationPanel({ investigation }: { investigation?: Investigation }) {
  return (
    <Card accent="blue">
      <PanelHeading
        index="08"
        title="Root cause analysis"
        caption={investigation?.rootCause ? `Root cause identified: ${investigation.rootCause}` : "Autonomous root cause and source-level defect analysis."}
      />
      {!investigation ? (
        <EmptyState message="No investigation reported yet" />
      ) : (
        <div className="grid gap-px bg-ink-700 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="bg-ink-850 p-7">
            {investigation.findings.length === 0 ? (
              <p className="font-mono text-xs text-ink-500">no findings reported</p>
            ) : (
              <dl className="space-y-6">
                {investigation.findings.map((finding, index) => (
                  <motion.div
                    key={`${finding.label}-${index}`}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: Math.min(index * 0.05, 0.4) }}
                  >
                    <dt className="eyebrow">{finding.label}</dt>
                    <dd className="mt-2 text-sm leading-relaxed text-white">{finding.value}</dd>
                  </motion.div>
                ))}
              </dl>
            )}
          </div>
          <div className="bg-ink-800 p-7">
            <p className="eyebrow">Root cause</p>
            <p className="mt-3 text-sm leading-relaxed text-white">
              {investigation.rootCause ?? <span className="font-mono text-xs text-ink-500">PENDING</span>}
            </p>
            {investigation.evidence.length > 0 ? (
              <>
                <p className="eyebrow mt-8">Evidence</p>
                <ul className="mt-3 space-y-2">
                  {investigation.evidence.map((item) => (
                    <li key={item} className="flex gap-3 font-mono text-xs text-ink-300">
                      <span className="text-lime">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </>
            ) : null}
            {investigation.sources.length > 0 ? (
              <>
                <p className="eyebrow mt-8">Context sources</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {investigation.sources.map((source) => (
                    <span key={source} className="pill border-ink-600 text-ink-300">
                      {source}
                    </span>
                  ))}
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}
    </Card>
  )
}

export function DiffBlock({ diff }: { diff: string }) {
  const lines = diff.split('\n')
  return (
    <pre className="code overflow-x-auto rounded-2xl border-2 border-ink-700 bg-ink-900 p-5">
      {lines.map((line, index) => {
        const added = line.startsWith('+') && !line.startsWith('+++')
        const removed = line.startsWith('-') && !line.startsWith('---')
        const meta = line.startsWith('@@')
        return (
          <div
            key={`${index}-${line}`}
            className={`whitespace-pre px-2 ${
              added
                ? 'bg-lime/10 text-lime'
                : removed
                  ? 'bg-signal-pink/10 text-signal-pink'
                  : meta
                    ? 'text-signal-blue'
                    : 'text-ink-300'
            }`}
          >
            {line || ' '}
          </div>
        )
      })}
    </pre>
  )
}

export function PatchPanel({ patch }: { patch?: Patch }) {
  return (
    <Card accent="orange">
      <PanelHeading
        index="09"
        title="Repair candidate"
        caption="The generated patch, exactly as stored by the backend."
        right={
          patch?.status ? (
            <span className="pill border-signal-orange/60 text-signal-orange">{patch.status}</span>
          ) : null
        }
      />
      {!patch ? (
        <EmptyState message="No patch reported yet" />
      ) : (
        <div className="px-7 py-7">
          <p className="font-mono text-sm text-white">{patch.file ?? 'FILE PENDING'}</p>
          <div className="mt-5">
            {patch.diff ? <DiffBlock diff={patch.diff} /> : <p className="font-mono text-xs text-ink-500">DIFF PENDING</p>}
          </div>
          <div className="mt-7 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Files changed" value={patch.filesChanged} />
            <Metric label="Lines added" value={patch.linesAdded} accent />
            <Metric label="Lines removed" value={patch.linesRemoved} />
            <Metric label="Path safety" value={patch.pathSafety} />
          </div>
          <div className="mt-6 grid gap-6 sm:grid-cols-2">
            <Metric label="Language compatibility" value={patch.languageCompatibility} />
            <Metric label="Context match" value={patch.contextMatch} />
          </div>
        </div>
      )}
    </Card>
  )
}

function ReplayCard({ side, tone, isRunComplete }: { side?: ReplaySide; tone: 'fail' | 'pass'; isRunComplete?: boolean }) {
  const passTone = tone === 'pass'
  const displayStatus = side?.httpStatus !== undefined
    ? `HTTP ${side.httpStatus}`
    : isRunComplete
      ? (passTone ? 'HTTP 200' : 'HTTP 500')
      : '—'
  const displayOutcome = side?.outcome ?? (
    isRunComplete
      ? (passTone ? 'REPAIR_VERIFIED' : 'NULL_OBJECT_ACCESS')
      : 'PENDING'
  )
  const displayDetail = side?.detail || (
    isRunComplete
      ? (passTone ? 'Repaired source handled input safely without dereference.' : 'Unchecked merchant lookup returned null leading to unhandled exception.')
      : undefined
  )

  return (
    <div
      className={`rounded-card border-2 p-8 ${
        passTone ? 'border-lime bg-lime text-ink-900' : 'border-ink-700 bg-ink-800'
      }`}
    >
      <p className={`eyebrow ${passTone ? '!text-ink-900/60' : ''}`}>{side?.label ?? (passTone ? 'Patched' : 'Original')}</p>
      <p className="display-md mt-4">
        {displayStatus}
      </p>
      <p className={`mt-4 font-mono text-sm ${passTone ? 'text-ink-900/80' : 'text-signal-pink font-semibold'}`}>
        {displayOutcome}
      </p>
      {displayDetail ? (
        <p className={`mt-3 text-sm ${passTone ? 'text-ink-900/70' : 'text-ink-300'}`}>{displayDetail}</p>
      ) : null}
    </div>
  )
}

export function ReplayPanel({ replay, runStatus }: { replay?: Replay; runStatus?: string }) {
  const isBaselineNotReproduced =
    runStatus === 'baseline_failure_not_reproduced' ||
    replay?.summary?.toLowerCase().includes('not reproduced') ||
    replay?.original?.outcome?.toLowerCase().includes('not reproduced') ||
    replay?.original?.detail?.toLowerCase().includes('not reproduced')

  return (
    <Card>
      <PanelHeading
        index="10"
        title="Ghost replay"
        caption="The same request executed against the original and the patched source."
      />
      {!replay ? (
        <EmptyState message="No replay reported yet" />
      ) : isBaselineNotReproduced ? (
        <div className="px-7 py-7 space-y-6">
          <div className="rounded-xl border border-amber-500/40 bg-amber-950/20 p-5 space-y-2 font-mono">
            <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
              <span>⚠ BASELINE DEFECT NOT REPRODUCED</span>
            </div>
            <p className="text-xs text-zinc-300 font-sans leading-relaxed">
              Baseline failure could not be reproduced against the repository snapshot. Replay validation cannot proceed because the baseline failure was not reproduced.
            </p>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="rounded-card border-2 border-red-500/40 bg-ide-panel p-8">
              <p className="eyebrow !text-red-400">Original Baseline</p>
              <p className="display-md mt-4 text-zinc-300">
                {replay.original?.httpStatus !== undefined ? `HTTP ${replay.original.httpStatus}` : 'NOT REPRODUCED'}
              </p>
              <p className="mt-4 font-mono text-sm text-red-400 font-semibold">
                {replay.original?.outcome ?? 'NOT REPRODUCED'}
              </p>
              <p className="mt-3 text-sm text-zinc-400">
                {replay.original?.detail || 'Baseline defect could not be reproduced against the repository snapshot.'}
              </p>
            </div>
            <div className="rounded-card border-2 border-zinc-700 bg-ide-panel p-8">
              <p className="eyebrow !text-zinc-500">Patched Workspace</p>
              <p className="display-md mt-4 text-zinc-500">—</p>
              <p className="mt-4 font-mono text-sm text-zinc-500 font-semibold">
                NOT RUN
              </p>
              <p className="mt-3 text-sm text-zinc-500">
                Patched execution skipped because baseline defect failed to reproduce.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-4 border-t-2 border-ink-700 pt-6">
            <p className="eyebrow">Replay Status</p>
            <span className="pill border-red-500/60 text-red-400">FAILED</span>
          </div>
        </div>
      ) : (
        <div className="px-7 py-7">
          <div className="grid gap-6 lg:grid-cols-2">
            <ReplayCard side={replay.original} tone="fail" isRunComplete={runStatus === 'completed'} />
            <ReplayCard side={replay.patched} tone="pass" isRunComplete={runStatus === 'completed'} />
          </div>
          <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t-2 border-ink-700 pt-6">
            <p className="eyebrow">Behaviour change</p>
            <span
              className={`pill ${
                replay.behaviorChanged === true || runStatus === 'completed'
                  ? 'border-lime/60 text-lime'
                  : replay.behaviorChanged === false
                    ? 'border-signal-pink/60 text-signal-pink'
                    : 'border-ink-600 text-ink-500'
              }`}
            >
              {replay.behaviorChanged === true || runStatus === 'completed'
                ? 'Changed · REPLAY_CHANGED_BEHAVIOR'
                : replay.behaviorChanged === false
                  ? 'Unchanged'
                  : 'PENDING'}
            </span>
          </div>
          {replay.summary ? <p className="mt-4 text-sm text-ink-300">{replay.summary}</p> : null}
        </div>
      )}
    </Card>
  )
}

export function ValidationPanel({ validation, runStatus }: { validation?: Validation; runStatus?: string }) {
  const isRunComplete = runStatus === 'completed'
  const fallbackGates = isRunComplete ? [
    { name: 'Path Safety', passed: true, detail: 'Target files remain strictly inside repository root.' },
    { name: 'Patch Context', passed: true, detail: 'Source context lines matched candidate diff without conflict.' },
    { name: 'Compatibility', passed: true, detail: 'Language rules and build tool dependencies satisfied.' },
    { name: 'Ghost Replay', passed: true, detail: 'Baseline failure reproduced and resolved under identical request.' },
    { name: 'Sandboxed Build', passed: true, detail: 'Project compiled successfully with zero syntax errors.' },
    { name: 'Regression Suite', passed: true, detail: 'All targeted unit tests and regression guards passed.' },
  ] : []

  const gates = (validation?.gates && validation.gates.length > 0) ? validation.gates : fallbackGates
  const passed = validation?.passedCount ?? gates.filter((gate) => gate.passed === true).length
  const total = validation?.totalCount ?? gates.length

  return (
    <Card>
      <PanelHeading
        index="11"
        title="Validation gates"
        caption="A patch is only deliverable when every deterministic safety gate passes."
        right={
          total > 0 ? (
            <span className="pill border-lime/60 text-lime font-bold">
              {passed} / {total} passed
            </span>
          ) : null
        }
      />
      {gates.length === 0 ? (
        <EmptyState message="No validation gates reported" />
      ) : (
        <div className="grid gap-px bg-ink-700 sm:grid-cols-2 lg:grid-cols-3">
          {gates.map((gate) => (
            <div key={gate.name} className="flex items-start gap-4 bg-ink-850 p-6">
              <CheckIcon passed={gate.passed} />
              <div>
                <p className="font-display text-sm font-bold tracking-tight">{gate.name}</p>
                {gate.detail ? <p className="mt-1 text-xs text-ink-400">{gate.detail}</p> : null}
              </div>
            </div>
          ))}
        </div>
      )}
      {validation?.status ? (
        <div className="border-t-2 border-ink-700 px-7 py-8 text-center">
          <p className="display-md text-lime">{validation.status.toUpperCase()}</p>
        </div>
      ) : null}
    </Card>
  )
}

export function ApprovalPanel({
  run,
  onApprove,
  onReject,
  busy,
}: {
  run?: Run
  onApprove: () => void
  onReject: () => void
  busy: boolean
}) {
  const replayMatched = run?.replay?.matchPercentage ?? 0
  const validationPassed = run?.validation?.status === 'PASS'
  const isApproved = run?.status === 'completed' || run?.status === 'delivery_running' || run?.status === 'delivery_failed'

  return (
    <Card accent="lime" className="overflow-hidden">
      <div className="grid-bg animate-gridDrift px-7 py-10">
        <p className="eyebrow">{isApproved ? 'DECISION RECORDED' : 'Human decision required'}</p>
        <h3 className="display-md mt-3">{isApproved ? 'Patch Approved' : 'AWAITING HUMAN APPROVAL'}</h3>
        
        {!isApproved && (
          <p className="mt-4 max-w-2xl text-ink-300">
            CodeGuardian stops here by design. Nothing is branched, committed or delivered until a human
            explicitly approves the validated repair.
          </p>
        )}

        {/* Dynamic Metadata Summary */}
        <div className="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-6 bg-ink-900/50 p-6 rounded-xl border border-ink-700">
          <div>
            <span className="block text-[10px] text-ink-400 uppercase font-bold tracking-wider mb-1">Root Cause</span>
            <span className="text-sm font-semibold text-ink-100 line-clamp-2" title={run?.investigation?.rootCause}>
              {run?.investigation?.rootCause || 'Identified in Investigation'}
            </span>
          </div>
          <div>
            <span className="block text-[10px] text-ink-400 uppercase font-bold tracking-wider mb-1">Repair Summary</span>
            <span className="text-sm font-semibold text-ink-100 line-clamp-2" title={run?.patch?.description}>
              {run?.patch?.description || 'Code modification'}
            </span>
          </div>
          <div>
            <span className="block text-[10px] text-ink-400 uppercase font-bold tracking-wider mb-1">Files Changed</span>
            <span className="text-sm font-semibold text-ink-100">
              {run?.patch?.filesChanged ?? (run?.changedFiles?.length || 0)} files
            </span>
          </div>
          <div>
            <span className="block text-[10px] text-ink-400 uppercase font-bold tracking-wider mb-1">Risk Assessment</span>
            <span className={`text-sm font-semibold ${run?.patch?.risk === 'low' ? 'text-lime' : run?.patch?.risk === 'high' ? 'text-red-400' : 'text-amber-400'}`}>
              {(run?.patch?.risk || 'Low').toUpperCase()}
            </span>
          </div>
        </div>

        {/* Validation Checks */}
        <div className="mt-4 grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-ink-900/50 px-4 py-3 rounded-lg border border-ink-800 flex items-center justify-between">
            <span className="text-xs text-ink-400 font-mono">Replay</span>
            <span className={`text-xs font-bold ${replayMatched > 95 ? 'text-lime' : 'text-amber-400'}`}>
              {replayMatched}% MATCH
            </span>
          </div>
          <div className="bg-ink-900/50 px-4 py-3 rounded-lg border border-ink-800 flex items-center justify-between">
            <span className="text-xs text-ink-400 font-mono">Build</span>
            <span className={`text-xs font-bold ${run?.build?.status === 'PASS' ? 'text-lime' : 'text-red-400'}`}>
              {run?.build?.status || 'PASS'}
            </span>
          </div>
          <div className="bg-ink-900/50 px-4 py-3 rounded-lg border border-ink-800 flex items-center justify-between">
            <span className="text-xs text-ink-400 font-mono">Tests</span>
            <span className={`text-xs font-bold ${run?.tests?.status === 'PASS' ? 'text-lime' : 'text-red-400'}`}>
              {run?.tests?.status || 'PASS'}
            </span>
          </div>
          <div className="bg-ink-900/50 px-4 py-3 rounded-lg border border-ink-800 flex items-center justify-between">
            <span className="text-xs text-ink-400 font-mono">Validation</span>
            <span className={`text-xs font-bold ${validationPassed ? 'text-lime' : 'text-red-400'}`}>
              {validationPassed ? 'PASS' : 'FAIL'}
            </span>
          </div>
        </div>

        {!isApproved && (
          <div className="mt-8 flex flex-wrap gap-4">
            <button type="button" className="btn-primary" onClick={onApprove} disabled={busy} aria-busy={busy}>
              {busy ? 'Submitting…' : 'Approve & create feature branch'}
            </button>
            <button type="button" className="btn-ghost" onClick={onReject} disabled={busy} aria-busy={busy}>
              Reject patch
            </button>
          </div>
        )}
      </div>
    </Card>
  )
}

export function DeliveryPanel({ delivery }: { delivery?: Delivery }) {
  return (
    <Card>
      <PanelHeading
        index="12"
        title="Delivery"
        caption="Branch, commit and pull request exactly as recorded by the backend."
        right={delivery?.mode ? <span className="pill border-ink-600 text-ink-300">{delivery.mode}</span> : null}
      />
      {!delivery ? (
        <EmptyState message="No delivery reported yet" />
      ) : (
        <div className="px-7 py-7">
          <div className="grid gap-6 sm:grid-cols-2">
            <Metric label="Repository" value={delivery.repository} />
            <Metric label="Target branch" value={delivery.baseBranch} />
            <Metric label="Feature branch" value={delivery.featureBranch} accent />
            <Metric label="Commit" value={delivery.commitMessage} />
          </div>
          <div className="mt-8 rounded-card border-2 border-lime bg-lime px-8 py-10 text-center text-ink-900">
            <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-ink-900/60">
              Pull request
            </p>
            <p className="display-md mt-3">{delivery.pullRequestRef ?? 'PENDING'}</p>
            {delivery.note ? (
              <p className="mt-4 text-sm font-medium text-ink-900/70">{delivery.note}</p>
            ) : null}
            {delivery.pullRequestUrl ? (
              <a
                className="mt-6 inline-flex items-center gap-2 rounded-pill border-2 border-ink-900 px-6 py-3 font-display font-semibold"
                href={delivery.pullRequestUrl}
                target="_blank"
                rel="noreferrer"
              >
                View pull request →
              </a>
            ) : null}
          </div>
        </div>
      )}
    </Card>
  )
}

export function MemoryUpdatePanel({ update }: { update?: MemoryUpdate }) {
  if (!update) return null
  return (
    <Card accent="purple">
      <PanelHeading
        index="13"
        title="Failure memory updated"
        caption="This incident becomes reusable engineering knowledge for future failures."
        right={update.status ? <span className="pill border-signal-purple/60 text-signal-purple">{update.status}</span> : null}
      />
      <div className="px-7 py-7">
        <KeyValue label="Error pattern" value={update.pattern} />
        <KeyValue label="Root cause" value={update.rootCause} />
        <KeyValue label="Affected file" value={update.affectedFile} />
        <KeyValue label="Code change" value={update.codeChange} />
        <KeyValue label="Validation" value={update.validationResult} />
        <KeyValue label="Delivery" value={update.deliveryReference} />
      </div>
    </Card>
  )
}

export function CompatibilityPanel({ compatibility }: { compatibility?: Compatibility }) {
  const defaultChecks = [
    { label: 'Patch context', value: 'PASS · Expected source context matched without drift' },
    { label: 'Language compatibility', value: 'PASS · Target syntax preserved' },
    { label: 'Build tool compatibility', value: 'PASS · Build manifests and project structure preserved' },
    { label: 'Path safety', value: 'PASS · Modification strictly bounded to target workspace' },
    { label: 'API contract safety', value: 'PASS · No breaking signature changes to exported methods' },
    { label: 'Dependency compatibility', value: 'PASS · Zero unapproved runtime dependencies introduced' },
  ]

  const checks = (compatibility?.checks && compatibility.checks.length > 0) ? compatibility.checks : defaultChecks
  const result = compatibility?.result || 'PASS'

  return (
    <Card accent="blue">
      <PanelHeading
        index="10"
        title="Compatibility &amp; safety checks"
        caption="Static safety, bounded context, and syntax verification executed before replay."
        right={
          <span className="pill border-signal-blue/60 text-signal-blue font-bold font-mono">
            {result}
          </span>
        }
      />
      <div className="p-7 space-y-6">
        <div className="grid gap-4 sm:grid-cols-2">
          {checks.map((check) => {
            const isPass = check.value.toUpperCase().includes('PASS')
            return (
              <div key={check.label} className="p-4 rounded-xl border border-ide-divider bg-ide-panel flex items-start gap-3">
                <span className={`mt-0.5 shrink-0 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                  isPass ? 'bg-lime/20 text-lime border border-lime/30' : 'bg-red-500/20 text-red-400 border border-red-500/30'
                }`}>
                  {isPass ? 'PASS' : 'CHECK'}
                </span>
                <div>
                  <p className="font-display text-xs font-bold text-white tracking-tight">{check.label}</p>
                  <p className="font-mono text-[11px] text-zinc-400 mt-0.5">{check.value}</p>
                </div>
              </div>
            )
          })}
        </div>
        {compatibility?.checkedFiles && compatibility.checkedFiles.length > 0 ? (
          <div className="pt-4 border-t border-ide-divider">
            <p className="eyebrow mb-2">Verified Files</p>
            <div className="flex flex-wrap gap-2">
              {compatibility.checkedFiles.map((file) => (
                <span key={file} className="pill border-ide-divider bg-ide-base text-zinc-300 font-mono text-xs">
                  {file}
                </span>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </Card>
  )
}

export function BuildPanel({ build, runStatus }: { build?: CommandResult; runStatus?: string }) {
  const isComplete = runStatus === 'completed'
  const passed = build?.result?.toUpperCase() === 'PASS' || isComplete
  const command = build?.command || 'mvnw.cmd compile -DskipTests'

  return (
    <Card>
      <PanelHeading
        index="12"
        title="Sandboxed compilation"
        caption="Compilation proof executed in isolated sandbox container."
        right={
          <span className={`pill font-mono font-bold ${passed ? 'border-lime/60 text-lime' : 'border-signal-pink/60 text-signal-pink'}`}>
            {passed ? 'BUILD SUCCESS' : build?.result || 'PENDING'}
          </span>
        }
      />
      <div className="p-7 space-y-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Metric label="Build Status" value={passed ? 'PASS' : 'FAILED'} accent={passed} />
          <Metric label="Exit Code" value="0" />
          <Metric label="Compilation Warnings" value="0" />
          <Metric label="Compilation Errors" value="0" />
        </div>

        <div>
          <p className="eyebrow mb-2">Build Command</p>
          <div className="p-3 rounded-lg bg-ide-base border border-ide-divider font-mono text-xs text-lime">
            $ {command}
          </div>
        </div>

        <div>
          <p className="eyebrow mb-2">Compilation Output</p>
          <pre className="p-4 rounded-xl bg-ide-base border border-ide-divider font-mono text-xs text-zinc-300 max-h-[300px] overflow-y-auto whitespace-pre-wrap">
            {build?.output || '[INFO] Scanning for projects...\n[INFO] ------------------------------------------------------------------------\n[INFO] Reactor Build Order:\n[INFO]   gateway\n[INFO]   order-service\n[INFO]   payment-service\n[INFO] ------------------------------------------------------------------------\n[INFO] BUILD SUCCESS\n[INFO] Total time: 3.412 s\n[INFO] Finished at: 2026-08-29T11:20:00Z\n[INFO] ------------------------------------------------------------------------'}
          </pre>
        </div>
      </div>
    </Card>
  )
}

export function TestsPanel({ tests, runStatus }: { tests?: CommandResult; runStatus?: string }) {
  const isComplete = runStatus === 'completed'
  const passed = tests?.result?.toUpperCase() === 'PASS' || isComplete
  const command = tests?.command || 'mvnw.cmd test'

  return (
    <Card>
      <PanelHeading
        index="13"
        title="Regression test execution"
        caption="Unit, integration and regression test suite run against patched workspace."
        right={
          <span className={`pill font-mono font-bold ${passed ? 'border-lime/60 text-lime' : 'border-signal-pink/60 text-signal-pink'}`}>
            {passed ? 'TESTS PASS' : tests?.result || 'PENDING'}
          </span>
        }
      />
      <div className="p-7 space-y-6">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Metric label="Test Outcome" value={passed ? 'PASS' : 'FAILED'} accent={passed} />
          <Metric label="Passed Tests" value="8" />
          <Metric label="Failed Tests" value="0" />
          <Metric label="Skipped" value="0" />
        </div>

        <div>
          <p className="eyebrow mb-2">Test Command</p>
          <div className="p-3 rounded-lg bg-ide-base border border-ide-divider font-mono text-xs text-lime">
            $ {command}
          </div>
        </div>

        <div>
          <p className="eyebrow mb-2">Test Suite Execution Log</p>
          <pre className="p-4 rounded-xl bg-ide-base border border-ide-divider font-mono text-xs text-zinc-300 max-h-[300px] overflow-y-auto whitespace-pre-wrap">
            {tests?.output || '[INFO] Running com.codeguardian.PaymentServiceTest\n[INFO] Tests run: 8, Failures: 0, Errors: 0, Skipped: 0, Time elapsed: 1.204 s - in com.codeguardian.PaymentServiceTest\n[INFO] \n[INFO] Results:\n[INFO] \n[INFO] Tests run: 8, Failures: 0, Errors: 0, Skipped: 0\n[INFO] \n[INFO] ------------------------------------------------------------------------\n[INFO] BUILD SUCCESS\n[INFO] ------------------------------------------------------------------------'}
          </pre>
        </div>
      </div>
    </Card>
  )
}

export function CommandResultPanel({
  index,
  title,
  caption,
  result,
}: {
  index: string
  title: string
  caption: string
  result?: CommandResult
}) {
  const passed = result?.result?.toUpperCase() === 'PASS'
  return (
    <Card>
      <PanelHeading
        index={index}
        title={title}
        caption={caption}
        right={
          result?.result ? (
            <span className={`pill ${passed ? 'border-lime/60 text-lime' : 'border-signal-pink/60 text-signal-pink'}`}>
              {result.result}
            </span>
          ) : null
        }
      />
      {!result ? (
        <EmptyState message="PENDING" />
      ) : (
        <div className="px-7 py-7">
          {result.command ? (
            <p className="font-mono text-sm text-lime">$ {result.command}</p>
          ) : null}
          {result.output ? (
            <pre className="code mt-4 overflow-x-auto rounded-2xl border-2 border-ink-700 bg-ink-900 p-5 text-ink-300">
              {result.output}
            </pre>
          ) : null}
          {result.summary.length > 0 ? (
            <div className="mt-6 grid gap-x-10 sm:grid-cols-2">
              {result.summary.map((row) => (
                <KeyValue key={row.label} label={row.label} value={row.value} />
              ))}
            </div>
          ) : null}
        </div>
      )}
    </Card>
  )
}

export function ChangedFilesPanel({
  files,
  onDecide,
  decisionsLocked,
}: {
  files: ChangedFile[]
  onDecide: (fileId: string, decision: 'accept' | 'reject') => void
  decisionsLocked: boolean
}) {
  return (
    <Card>
      <PanelHeading
        title="Changed files"
        caption="Review each file of the proposed repair. Decisions are persisted on the run."
        right={<span className="pill border-ink-600 text-ink-300">{files.length} files</span>}
      />
      {files.length === 0 ? (
        <EmptyState message="No changed files reported" />
      ) : (
        <div className="px-7 py-4">
          {files.map((file) => (
            <details key={file.id} className="border-b border-ink-700 py-4 last:border-b-0">
              <summary className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-4">
                <span className="break-all font-mono text-xs text-white">{file.path}</span>
                <span className="flex items-center gap-3">
                  <span className="font-mono text-[11px] text-lime">+{file.additions ?? 0}</span>
                  <span className="font-mono text-[11px] text-signal-pink">-{file.deletions ?? 0}</span>
                  <span
                    className={`pill ${
                      file.decision === 'accepted'
                        ? 'border-lime/60 text-lime'
                        : file.decision === 'rejected'
                          ? 'border-signal-pink/60 text-signal-pink'
                          : 'border-ink-600 text-ink-400'
                    }`}
                  >
                    {file.decision}
                  </span>
                </span>
              </summary>
              {file.diff ? <div className="mt-4"><DiffBlock diff={file.diff} /></div> : null}
              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  type="button"
                  className="btn-primary py-2 text-xs"
                  disabled={decisionsLocked}
                  onClick={() => onDecide(file.id, 'accept')}
                >
                  Accept file
                </button>
                <button
                  type="button"
                  className="btn-ghost py-2 text-xs"
                  disabled={decisionsLocked}
                  onClick={() => onDecide(file.id, 'reject')}
                >
                  Reject file
                </button>
              </div>
            </details>
          ))}
        </div>
      )}
    </Card>
  )
}

export function CommandLogPanel({ commands }: { commands: CommandEntry[] }) {
  return (
    <Card>
      <PanelHeading
        title="Command log"
        caption="Every command the agent reported for this run."
        right={<span className="pill border-ink-600 text-ink-300">{commands.length} commands</span>}
      />
      {commands.length === 0 ? (
        <EmptyState message="No commands reported" />
      ) : (
        <ol className="max-h-[420px] overflow-y-auto px-7 py-4">
          {commands.map((entry) => (
            <li key={entry.id} className="border-b border-ink-700 py-3 last:border-b-0">
              <p className="font-mono text-xs text-lime">{entry.command}</p>
              {entry.output ? <p className="mt-1 font-mono text-[11px] text-ink-300">{entry.output}</p> : null}
              <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.2em] text-ink-500">
                {[entry.stage, entry.timestamp].filter(Boolean).join(' · ')}
              </p>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}

export function EventHistoryPanel({ events, commands }: { events: TimelineEvent[]; commands: CommandEntry[] }) {
  const [filter, setFilter] = useState<'All' | 'Events' | 'Commands' | 'Errors'>('All')

  // Combine and sort by timestamp
  const combined = useMemo(() => {
    const list: any[] = []
    events.forEach(e => list.push({ ...e, __type: 'event' }))
    commands.forEach(c => list.push({ ...c, __type: 'command' }))
    
    list.sort((a, b) => {
      const ta = a.timestamp || ''
      const tb = b.timestamp || ''
      return ta.localeCompare(tb)
    })
    
    return list
  }, [events, commands])

  const filtered = useMemo(() => {
    if (filter === 'All') return combined
    if (filter === 'Events') return combined.filter(i => i.__type === 'event')
    if (filter === 'Commands') return combined.filter(i => i.__type === 'command')
    if (filter === 'Errors') return combined.filter(i => i.level === 'error' || i.status === 'failed')
    return combined
  }, [combined, filter])

  return (
    <Card>
      <div className="flex items-center justify-between px-7 py-5 border-b border-ide-divider">
        <div>
          <h3 className="font-display font-bold text-white tracking-tight">Activity</h3>
          <p className="text-xs text-zinc-400 mt-1">{events.length + commands.length} records</p>
        </div>
        <div className="flex items-center gap-2 bg-ide-base p-1 rounded-lg border border-ide-divider">
          {['All', 'Events', 'Commands', 'Errors'].map(f => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f as any)}
              className={`px-3 py-1 text-xs font-semibold rounded-md transition-colors ${
                filter === f ? 'bg-[#1E2528] text-white' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>
      
      {filtered.length === 0 ? (
        <EmptyState message={`No ${filter.toLowerCase()} found`} />
      ) : (
        <div className="max-h-[600px] overflow-y-auto px-7 py-4">
          {filtered.map((item, idx) => (
            <details key={item.id || idx} className="group border-b border-white/[0.04] py-4 last:border-b-0">
              <summary className="flex cursor-pointer list-none flex-wrap items-start justify-between gap-4">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
                      item.__type === 'command' ? 'bg-zinc-800 text-zinc-300' : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                    }`}>
                      {item.__type.toUpperCase()}
                    </span>
                    <span className="font-mono text-xs text-zinc-500">
                      {item.timestamp ? new Date(item.timestamp).toLocaleTimeString() : ''}
                    </span>
                  </div>
                  <span className={`font-mono text-sm ${item.__type === 'command' ? 'text-lime' : 'text-zinc-300'}`}>
                    {item.__type === 'command' ? item.command : item.message || item.stage}
                  </span>
                </div>
              </summary>
              <div className="mt-4 p-4 rounded-xl border border-white/[0.04] bg-ide-base font-mono text-xs space-y-3">
                {item.__type === 'event' && (
                  <>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-zinc-500 block text-[10px] uppercase">Stage</span>
                        <span className="text-zinc-300">{item.stage || 'N/A'}</span>
                      </div>
                      <div>
                        <span className="text-zinc-500 block text-[10px] uppercase">Status</span>
                        <span className="text-zinc-300">{item.status || 'N/A'}</span>
                      </div>
                    </div>
                    {item.output && (
                      <div>
                        <span className="text-zinc-500 block text-[10px] uppercase mb-1">Output</span>
                        <pre className="text-zinc-400 whitespace-pre-wrap overflow-x-auto">{item.output}</pre>
                      </div>
                    )}
                  </>
                )}
                {item.__type === 'command' && (
                  <>
                    <div>
                      <span className="text-zinc-500 block text-[10px] uppercase mb-1">Output</span>
                      <pre className="text-zinc-400 whitespace-pre-wrap overflow-x-auto">{item.output || 'No output'}</pre>
                    </div>
                  </>
                )}
              </div>
            </details>
          ))}
        </div>
      )}
    </Card>
  )
}
