import { useState } from 'react'
import type { Run } from '../../api/types'
import { resolveRunPresentation } from '../../api/presentation'

interface StageAgentConfig {
  action: string
  analysis: string
  command?: string
  output?: string
  finding?: {
    title: string
    detail: string
  }
  nextAction: {
    title: string
    estimatedTime: string
  }
}

const STAGE_AGENT_MAP: Record<string, StageAgentConfig> = {
  '01_repository': {
    action: 'Inspecting repository',
    analysis: "Analyzing directory structure, language definitions, and build configuration files.",
    command: '$ inspect_repository',
    output: 'Repository cloned cleanly.\nFiles mapped and isolated in execution sandbox.',
    finding: {
      title: 'Repository structure identified.',
      detail: 'Clean isolated workspace created for investigation.',
    },
    nextAction: {
      title: 'Analyze application architecture',
      estimatedTime: '1–2s',
    },
  },
  '02_inspection': {
    action: 'Mapping source tree',
    analysis: 'Scanning source files, endpoints, service boundaries, and dependency manifests.',
    command: '$ scan_source_tree',
    output: 'Classes and components scanned across source packages.',
    finding: {
      title: 'Architecture map built.',
      detail: 'Layered architecture and dependencies indexed.',
    },
    nextAction: {
      title: 'Detect failure signals',
      estimatedTime: '2–3s',
    },
  },
  '03_architecture': {
    action: 'Evaluating dependencies',
    analysis: 'Detecting testing framework, test runners, and runtime requirements.',
    command: '$ check_build_system',
    output: 'Build tool and test framework configurations detected.',
    finding: {
      title: 'Build and test strategies configured.',
      detail: 'Automated test runners and wrappers available.',
    },
    nextAction: {
      title: 'Run failure detection',
      estimatedTime: '2s',
    },
  },
  '04_failure_detection': {
    action: 'Failure Detection',
    analysis: 'Analyzing error patterns across services and parsing recent telemetry to establish failure signal.',
    command: '$ detect_failure',
    output: 'Failure signature and error fingerprint established.\nInitial root cause candidate identified.',
    finding: {
      title: 'Defect pattern identified.',
      detail: 'Telemetry and stack trace isolated to root cause candidate.',
    },
    nextAction: {
      title: 'GhostTrace reconstruction',
      estimatedTime: '3–5s',
    },
  },
  '05_evidence': {
    action: 'Collecting failure evidence',
    analysis: 'Extracting request payloads, stack traces, runtime exceptions, and log records.',
    command: '$ collect_evidence',
    output: 'Structured telemetry captured and verified.',
    finding: {
      title: 'Verified execution evidence assembled.',
      detail: 'Causal chain contains verified telemetry records.',
    },
    nextAction: {
      title: 'Run GhostTrace reconstruction',
      estimatedTime: '3s',
    },
  },
  '06_ghost_trace': {
    action: 'Reconstructing causal flow',
    analysis: 'Tracking request flow from ingress gateway down to the failing component.',
    command: '$ ghosttrace',
    output: 'Causal execution graph reconstructed from symptom to root cause.',
    finding: {
      title: 'Root cause component isolated.',
      detail: 'First failing application node pinpointed.',
    },
    nextAction: {
      title: 'Search historical failure memory',
      estimatedTime: '2–4s',
    },
  },
  '07_failure_memory': {
    action: 'Searching failure memory',
    analysis: 'Querying vector memory of validated previous repairs for matching behavioral fingerprints.',
    command: '$ memory_search',
    output: 'Historical failure patterns queried against database.',
    finding: {
      title: 'Memory search evaluated.',
      detail: 'Historical resolutions referenced for repair synthesis.',
    },
    nextAction: {
      title: 'Investigate source and bounded context',
      estimatedTime: '4–6s',
    },
  },
  '08_investigation': {
    action: 'Investigating root cause',
    analysis: 'Correlating bounded source context with GhostTrace evidence and failure memory.',
    command: '$ investigate_bounded_context',
    output: 'Root cause confirmed from source inspection and execution evidence.',
    finding: {
      title: 'Root cause analysis complete.',
      detail: 'Unsafe execution path verified against repository source.',
    },
    nextAction: {
      title: 'Generate constrained repair candidate',
      estimatedTime: '5–8s',
    },
  },
  '09_patch': {
    action: 'Generating repair candidate',
    analysis: 'Synthesizing minimal, defensive patch adhering to repository conventions.',
    command: '$ generate_patch',
    output: 'Repair candidates generated in Counterfactual Repair Lab.',
    finding: {
      title: 'Candidate patch generated.',
      detail: 'Constrained to target source without modifying external interfaces.',
    },
    nextAction: {
      title: 'Run patch compatibility check',
      estimatedTime: '2s',
    },
  },
  '10_compatibility': {
    action: 'Checking patch safety',
    analysis: 'Verifying syntax, imports, method signatures, path bounds, and safety limits.',
    command: '$ verify_patch_safety',
    output: 'Path safety: PASS\nSyntax valid: PASS\nMethod signature: PASS',
    finding: {
      title: 'Safety clearance approved.',
      detail: 'Candidate patch meets all deterministic safety rules.',
    },
    nextAction: {
      title: 'Ghost Replay simulation',
      estimatedTime: '4s',
    },
  },
  '11_replay': {
    action: 'Replaying original failure',
    analysis: 'Applying patch in isolated workspace and replaying the exact failing request.',
    command: '$ replay_failure',
    output: 'Baseline failure replayed; patched workspace behavior verified.',
    finding: {
      title: 'Failure resolution proven.',
      detail: 'Controlled outcome confirmed under replay test.',
    },
    nextAction: {
      title: 'Compile and build patched workspace',
      estimatedTime: '5s',
    },
  },
  '12_build': {
    action: 'Compiling patched repository',
    analysis: 'Running build system in isolated sandbox container.',
    command: '$ run_build',
    output: 'BUILD SUCCESS\n0 compilation errors, 0 warnings',
    finding: {
      title: 'Compilation successful.',
      detail: 'Source compiles cleanly against all dependencies.',
    },
    nextAction: {
      title: 'Run test suite',
      estimatedTime: '6s',
    },
  },
  '13_tests': {
    action: 'Running regression test suite',
    analysis: 'Executing all unit and integration tests to verify no regressions were introduced.',
    command: '$ run_test_suite',
    output: 'Automated test suite executed successfully.',
    finding: {
      title: 'Regression tests passed.',
      detail: 'Automated test suite passed without regressions.',
    },
    nextAction: {
      title: 'Evaluate validation safety gates',
      estimatedTime: '2s',
    },
  },
  '14_validation': {
    action: 'Evaluating validation gates',
    analysis: 'Verifying build, test, replay, and safety metrics against promotion criteria.',
    command: '$ validate_gates --all',
    output: 'Build: PASS | Tests: PASS | Replay: PASS | Path: PASS\nOverall status: VALIDATED',
    finding: {
      title: 'All validation gates cleared.',
      detail: 'Patch is proven and ready for human operator review.',
    },
    nextAction: {
      title: 'Request human approval',
      estimatedTime: 'Awaiting user',
    },
  },
  '15_human_approval': {
    action: 'Awaiting human approval',
    analysis: 'All deterministic gates passed. Human approval is required before delivery.',
    command: '$ status_check --approval',
    output: 'State: WAITING_FOR_APPROVAL\nDiff reviewed: Ready for delivery',
    finding: {
      title: 'Validated patch pending approval.',
      detail: 'Human review controls feature branch and PR creation.',
    },
    nextAction: {
      title: 'Deliver branch and Pull Request',
      estimatedTime: '2–3s after approval',
    },
  },
  '16_delivery': {
    action: 'Delivering Pull Request',
    analysis: 'Creating Git feature branch, committing patch, pushing to GitHub and opening PR.',
    command: '$ git push_and_open_pr',
    output: 'Branch created on GitHub with detailed evidence report.',
    finding: {
      title: 'Pull Request published.',
      detail: 'Pull request ready for final merge.',
    },
    nextAction: {
      title: 'Persist validated resolution to memory',
      estimatedTime: '1s',
    },
  },
  '17_memory_update': {
    action: 'Updating failure memory',
    analysis: 'Indexing incident evidence, causal fingerprint, and validated patch into failure memory.',
    command: '$ memory_persist',
    output: 'Knowledge base updated with validated resolution.',
    finding: {
      title: 'Failure memory updated.',
      detail: 'Proven solution is now available to accelerate future investigations.',
    },
    nextAction: {
      title: 'Investigation complete',
      estimatedTime: 'Done',
    },
  },
  'baseline_failure_not_reproduced': {
    action: 'Baseline Failure Not Reproduced',
    analysis: 'The reported failure cannot be reproduced against the current repository baseline. The defect may have already been resolved or merged.',
    command: '$ verify_baseline --fixture',
    output: 'Baseline failure could not be reproduced against the repository snapshot.',
    finding: {
      title: 'Replay validation cannot proceed.',
      detail: 'Replay validation cannot proceed because the baseline failure was not reproduced.',
    },
    nextAction: {
      title: 'Investigation stopped safely',
      estimatedTime: 'Done',
    },
  },
}

export function AutoFixAgentPanel({
  run,
  onQuickAction,
}: {
  run?: Run
  onQuickAction?: (action: string) => void
}) {
  const [copied, setCopied] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const viewTimeline = true

  const repoName = run?.repository?.name || run?.repositoryUrl?.split('/').pop()?.replace(/\.git$/, '') || 'Unknown Repository'
  const fileCount = run?.sourceFiles?.length || 1
  const firstFilePath = run?.sourceFiles?.[0]?.path || 'src/main'

  const presentation = resolveRunPresentation(run)
  const isTerminalRun = presentation.isTerminal

  const rawStage = run?.currentStage?.toLowerCase() || ''
  const stageEntry = Object.entries(STAGE_AGENT_MAP).find(([k]) => {
    if (k === rawStage) return true
    const stripped = k.replace(/^\d+_/, '')
    return stripped === rawStage || rawStage.includes(stripped)
  })


  let config: StageAgentConfig
  if (run?.status === 'baseline_failure_not_reproduced') {
    config = STAGE_AGENT_MAP['baseline_failure_not_reproduced']
  } else if (run?.status === 'completed') {
    config = STAGE_AGENT_MAP['17_memory_update']
  } else if (run?.status === 'investigation_failed') {
    config = {
      action: 'Investigation Failed',
      analysis: presentation.engineeringAnalysis,
      finding: { title: 'Investigation Halted', detail: presentation.replaySummary },
      nextAction: { title: 'Investigation stopped safely', estimatedTime: 'Done' }
    }
  } else if (isTerminalRun) {
    config = {
      action: 'Run Failed',
      analysis: presentation.engineeringAnalysis,
      finding: { title: 'Terminal State Reached', detail: presentation.replaySummary },
      nextAction: { title: 'Execution stopped', estimatedTime: 'Done' }
    }
  } else if (stageEntry) {
    config = stageEntry[1]
  } else if (run?.status === 'waiting_for_approval') {
    config = STAGE_AGENT_MAP['15_human_approval']
  } else if (run?.status === 'delivery_running' || run?.status === 'delivered') {
    config = STAGE_AGENT_MAP['16_delivery']
  } else {
    config = STAGE_AGENT_MAP['08_investigation']
  }

  const handleCopy = () => {
    if (config.command) {
      navigator.clipboard.writeText(config.command)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <aside
      aria-label="Agent execution overview"
      className="w-[300px] xl:w-[320px] shrink-0 border-l border-ide-divider bg-ide-base flex flex-col justify-between overflow-y-auto select-none z-20"
    >
      <div className="p-4 space-y-4">
        {/* Header with Live Animation */}
        <div className="flex items-center justify-between pb-3 border-b border-ide-divider">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-lime opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-lime" />
            </span>
            <span className="font-mono text-xs font-bold text-white tracking-wider">
              AUTO-FIX AGENT
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-lime/10 border border-lime/30 text-lime font-semibold">
              ACTIVE
            </span>
            <button
              type="button"
              onClick={() => setIsPaused(!isPaused)}
              className="text-zinc-400 hover:text-white transition-colors"
              title={isPaused ? 'Resume' : 'Pause'}
            >
              {isPaused ? (
                <svg className="h-4 w-4 text-lime" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* Dynamic Context Card (Target & Stage) */}
        <div className="rounded-xl border border-ide-divider bg-ide-panel p-3.5 space-y-2.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-zinc-300 font-mono">Stage {String(presentation.passedCount || 1).padStart(2, '0')} / 17</span>
            <span className="text-[11px] font-mono text-lime font-bold">
              {presentation.progressPercent}%
            </span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-ide-base overflow-hidden">
            <div
              className="h-full bg-lime transition-all duration-300"
              style={{ width: `${presentation.progressPercent}%` }}
            />
          </div>
          <div className="flex items-center justify-between text-[11px] font-mono text-zinc-300 pt-0.5">
            <span>{run?.durationMs ? `Worked for ${(run.durationMs / 1000).toFixed(1)}s ▾` : 'Duration pending ▾'}</span>
            <span>Explored {fileCount} file{fileCount !== 1 ? 's' : ''} ▾</span>
          </div>
        </div>

        {/* Live Execution Activity Stream */}
        {viewTimeline ? (
          <div
            tabIndex={0}
            role="region"
            aria-label="Live execution activity log"
            className="rounded-lg border border-white/[0.06] bg-[#0A0E10] p-3 text-xs font-mono space-y-2 max-h-56 overflow-y-auto focus:outline-none focus:ring-1 focus:ring-zinc-700"
          >
            <div className="text-zinc-300 text-[11px]">Analysis active ▾</div>
            <div className="flex items-center gap-1.5 text-zinc-200 hover:text-white cursor-pointer">
              <span className="text-blue-400">Target</span>
              <span className="truncate font-semibold">{repoName}</span>
            </div>
            <div className="flex items-center gap-1.5 text-zinc-200 hover:text-white cursor-pointer">
              <span className="text-blue-400">Focus</span>
              <span className="truncate">{firstFilePath}</span>
            </div>
            <div className="text-zinc-300 text-[11px] pt-1">Execution history ▾</div>
            {run?.events && run.events.length > 0 ? (
              run.events.slice(-6).map((evt, idx) => (
                <div key={evt.id || idx} className="text-zinc-200 pl-2 text-[11px] flex items-center gap-1.5">
                  <span className="text-lime shrink-0">✓</span>
                  <span className="truncate">{evt.message}</span>
                </div>
              ))
            ) : (
              <div className="text-zinc-300 pl-2 text-[11px]">✓ Repository workspace loaded</div>
            )}
            <div className={`${isTerminalRun ? 'text-zinc-300' : 'text-lime'} pl-2 flex items-center gap-1.5`}>
              <span>
                {run?.status === 'completed'
                  ? '✓ Investigation completed'
                  : run?.status === 'baseline_failure_not_reproduced'
                  ? '⚠ Baseline failure not reproduced'
                  : config.action}
              </span>
              {!isTerminalRun ? (
                <span className="h-1.5 w-1.5 rounded-full bg-lime animate-ping shrink-0" />
              ) : null}
            </div>
          </div>
        ) : null}

        {/* Current Action */}
        <div className="pt-1">
          <span className="font-mono text-xs text-zinc-300 uppercase tracking-wider block mb-1 font-bold">
            CURRENT ACTION
          </span>
          <div className="flex items-center justify-between">
            <span className="font-display text-xs font-bold text-white tracking-wide">
              {presentation.currentAction}
            </span>
            <span className="relative flex h-3.5 w-3.5 items-center justify-center">
              {run?.status === 'completed' ? (
                <svg className="w-4 h-4 text-lime" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              ) : run?.status === 'baseline_failure_not_reproduced' ? (
                <span className="h-3 w-3 rounded-full bg-amber-400" />
              ) : run?.status === 'failed' || run?.status === 'rejected' ? (
                <span className="h-3 w-3 rounded-full bg-red-500" />
              ) : (
                <span className={`inline-flex h-full w-full rounded-full border-2 ${isPaused ? 'border-amber-400' : 'border-lime border-t-transparent animate-spin'}`} />
              )}
            </span>
          </div>
        </div>

        {/* Engineering Analysis (Rich text explanation) */}
        <div>
          <span className="font-mono text-xs text-zinc-300 uppercase tracking-wider block mb-1 font-bold">
            ENGINEERING ANALYSIS
          </span>
          <p className="text-xs text-zinc-300 leading-relaxed bg-ide-panel p-3 rounded-lg border border-ide-divider">
            {presentation.engineeringAnalysis || config.analysis}
          </p>
        </div>

        {/* Command Executed */}
        <div>
          <span className="font-mono text-xs text-zinc-300 uppercase tracking-wider block mb-1 font-bold">
            COMMAND EXECUTED
          </span>
          <div className="rounded-lg border border-ide-divider bg-[#0A0E10] p-2.5 font-mono text-xs text-zinc-200">
            <div className="flex items-center justify-between">
              <span className="text-lime">{config.command || '$ inspect_workspace'}</span>
              <button
                type="button"
                onClick={handleCopy}
                aria-label="Copy command"
                className="text-zinc-400 hover:text-white shrink-0 p-1.5 rounded hover:bg-white/[0.08] transition-colors flex items-center justify-center min-w-[28px] min-h-[28px]"
              >
                {copied ? (
                  <svg className="h-4 w-4 text-lime" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>
            </div>
            {config.output && (
              <pre className="mt-1.5 text-[11px] text-zinc-300 whitespace-pre-wrap leading-tight">
                {config.output}
              </pre>
            )}
          </div>
        </div>

        {/* Finding / Decision Box */}
        {config.finding && (
          <div>
            <span className="font-mono text-xs text-zinc-300 uppercase tracking-wider block mb-1 font-bold">
              FINDING / DECISION
            </span>
            <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3 text-xs space-y-1">
              <p className="font-semibold text-blue-300">{config.finding.title}</p>
              <p className="text-zinc-300 text-[11px] leading-relaxed">
                {config.finding.detail}
              </p>
            </div>
          </div>
        )}

        {/* Next Action / Status */}
        <div className="rounded-xl border border-ide-divider bg-ide-panel p-3.5 space-y-1">
          <span className="font-mono text-[10px] text-zinc-400 uppercase tracking-widest block font-bold">
            {isTerminalRun ? 'STATUS' : 'NEXT ACTION'}
          </span>
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold text-white">{config.nextAction.title}</p>
              <p className="text-[10px] font-mono text-zinc-300">
                {isTerminalRun ? 'Status: Completed' : `Estimated time: ${config.nextAction.estimatedTime}`}
              </p>
            </div>
            <button
              type="button"
              onClick={() => onQuickAction?.(isTerminalRun ? 'overview' : 'investigation')}
              className="text-xs font-mono text-lime hover:underline cursor-pointer"
            >
              View details →
            </button>
          </div>
        </div>
      </div>

      {/* Quick Actions (2x2 Grid at Bottom) */}
      <div className="p-4 border-t border-ide-divider">
        <span className="font-mono text-[10px] text-zinc-400 uppercase tracking-widest block mb-2 font-bold">
          QUICK ACTIONS
        </span>
        <div className="grid grid-cols-2 gap-2 text-xs">
          {isTerminalRun ? (
            <>
              <button
                type="button"
                onClick={() => onQuickAction?.('delivery')}
                className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg border border-ide-divider bg-ide-panel text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
              >
                <svg className="h-3.5 w-3.5 text-lime" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
                <span className="text-[11px] truncate">View Pull Request</span>
              </button>
              <button
                type="button"
                onClick={() => onQuickAction?.('patch')}
                className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg border border-ide-divider bg-ide-panel text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
              >
                <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                <span className="text-[11px] truncate">View Patch</span>
              </button>
              <button
                type="button"
                onClick={() => onQuickAction?.('replay')}
                className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg border border-ide-divider bg-ide-panel text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
              >
                <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                </svg>
                <span className="text-[11px] truncate">View Replay</span>
              </button>
              <button
                type="button"
                onClick={() => onQuickAction?.('validation')}
                className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg border border-ide-divider bg-ide-panel text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
              >
                <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-[11px] truncate">View Validation</span>
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => onQuickAction?.('ghosttrace')}
                className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg border border-ide-divider bg-ide-panel text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
              >
                <svg className="h-3.5 w-3.5 text-lime" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                </svg>
                <span className="text-[11px] truncate">Run GhostTrace</span>
              </button>
              <button
                type="button"
                onClick={() => onQuickAction?.('events')}
                className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg border border-ide-divider bg-ide-panel text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
              >
                <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
                <span className="text-[11px] truncate">View Full Logs</span>
              </button>
              <button
                type="button"
                onClick={() => onQuickAction?.('source')}
                className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg border border-ide-divider bg-ide-panel text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
              >
                <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                </svg>
                <span className="text-[11px] truncate">Open in Source</span>
              </button>
              <button
                type="button"
                onClick={() => onQuickAction?.('issue')}
                className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg border border-ide-divider bg-ide-panel text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
              >
                <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span className="text-[11px] truncate">Create Issue Draft</span>
              </button>
            </>
          )}
        </div>
      </div>
    </aside>
  )
}
