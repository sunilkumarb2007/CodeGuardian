import type { Run, RunStatus } from './types'

export interface ResolvedRunPresentation {
  headerStatus: string
  headerTone: 'lime' | 'amber' | 'red' | 'cyan' | 'zinc'
  headerDot: string
  headerBg: string
  headerBorder: string
  isTerminal: boolean
  isPaused: boolean
  currentAction: string
  engineeringAnalysis: string
  replayOutcome: string
  replaySummary: string
  isBaselineFailureNotReproduced: boolean
  passedCount: number
  totalStages: number
  progressPercent: number
  displayRepositoryName: string
}

export function deriveRepositoryName(urlOrName?: string): string {
  if (!urlOrName) return 'JavaAPICheck'
  const clean = urlOrName.trim().replace(/\/+$/, '')
  const lastPart = clean.split('/').pop()?.replace(/\.git$/, '')
  return lastPart || clean || 'JavaAPICheck'
}

export function resolveRunPresentation(run?: Run): ResolvedRunPresentation {
  const status: RunStatus = run?.status ?? 'running'
  const repositoryUrl = run?.repositoryUrl || run?.repository?.url || ''
  const displayRepositoryName = run?.repository?.name || deriveRepositoryName(repositoryUrl)

  const isNoFailure = status === 'no_failure_evidence' || status === 'no_failure_found'
  const isCompleted = status === 'completed'
  const isBaselineFailureNotReproduced = status === 'baseline_failure_not_reproduced'
  const isFailed = !isNoFailure && (status === 'failed' || status === 'delivery_failed' || status === 'rejected' ||
    status === 'investigation_failed' || status === 'patch_apply_failed' ||
    status === 'replay_failed' || status === 'validation_failed')
  const isPaused = status === 'waiting_for_approval'
  const isTerminal = isCompleted || isNoFailure || isBaselineFailureNotReproduced || isFailed

  // Progress Calculation
  const passedCount = Math.min(
    run?.stages?.filter((s) => s.status === 'passed' || s.status === 'completed' || s.status === 'skipped').length ?? 0,
    17
  )
  const totalStages = 17
  const progressPercent = isCompleted || isNoFailure ? 100 : Math.min(Math.round((passedCount / totalStages) * 100), 100)

  // Status Badge Metadata
  let headerStatus = 'INVESTIGATION RUNNING'
  let headerTone: 'lime' | 'amber' | 'red' | 'cyan' | 'zinc' = 'lime'
  let headerDot = 'bg-lime animate-pulse'
  let headerBg = 'bg-black/60'
  let headerBorder = 'border-lime/40'

  if (isCompleted) {
    headerStatus = 'INVESTIGATION COMPLETED · REPAIR VERIFIED'
    headerTone = 'lime'
    headerDot = 'bg-lime'
    headerBg = 'bg-lime/10'
    headerBorder = 'border-lime/40'
  } else if (isNoFailure) {
    headerStatus = 'ANALYSIS COMPLETE · NO FAILURE DETECTED'
    headerTone = 'lime'
    headerDot = 'bg-lime'
    headerBg = 'bg-lime/10'
    headerBorder = 'border-lime/40'
  } else if (isBaselineFailureNotReproduced) {
    headerStatus = 'BASELINE FAILURE NOT REPRODUCED'
    headerTone = 'amber'
    headerDot = 'bg-amber-400'
    headerBg = 'bg-amber-950/40'
    headerBorder = 'border-amber-500/40'
  } else if (isPaused) {
    headerStatus = 'AWAITING HUMAN APPROVAL'
    headerTone = 'amber'
    headerDot = 'bg-amber-400 animate-pulse'
    headerBg = 'bg-amber-950/40'
    headerBorder = 'border-amber-500/40'
  } else if (status === 'delivery_running') {
    headerStatus = 'DELIVERY RUNNING'
    headerTone = 'cyan'
    headerDot = 'bg-cyan-400 animate-pulse'
    headerBg = 'bg-cyan-950/40'
    headerBorder = 'border-cyan-500/40'
  } else if (status === 'delivered') {
    headerStatus = 'DELIVERED · PR OPENED'
    headerTone = 'lime'
    headerDot = 'bg-lime'
    headerBg = 'bg-lime/10'
    headerBorder = 'border-lime/40'
  } else if (status === 'investigation_failed') {
    headerStatus = 'INVESTIGATION FAILED'
    headerTone = 'red'
    headerDot = 'bg-red-400'
    headerBg = 'bg-red-950/40'
    headerBorder = 'border-red-500/40'
  } else if (isFailed || isTerminal) {
    let failureMsg = 'RUN FAILED'
    if (status === 'rejected') failureMsg = 'PATCH REJECTED'
    else if (status === 'patch_apply_failed') failureMsg = 'PATCH APPLY FAILED'
    else if (status === 'replay_failed') failureMsg = 'REPLAY FAILED'
    else if (status === 'validation_failed') failureMsg = 'VALIDATION FAILED'
    else if (status === 'delivery_failed') failureMsg = 'DELIVERY FAILED'

    headerStatus = failureMsg
    headerTone = 'red'
    headerDot = 'bg-red-400'
    headerBg = 'bg-red-950/40'
    headerBorder = 'border-red-500/40'
  } else if (status === 'queued') {
    headerStatus = 'INVESTIGATION QUEUED'
    headerTone = 'zinc'
    headerDot = 'bg-zinc-400'
    headerBg = 'bg-zinc-900/80'
    headerBorder = 'border-zinc-700'
  }

  // Current Action & Analysis
  let currentAction = 'Analyzing repository and failure context'
  let engineeringAnalysis = 'Scanning repository structure, source dependencies, and failure telemetry.'
  let replayOutcome = 'PENDING'
  let replaySummary = run?.replay?.summary || 'Replay validation in progress.'

  if (isCompleted) {
    currentAction = 'Investigation Complete'
    engineeringAnalysis = 'All 17 pipeline stages cleared, verified against build/replay/tests, and delivered via GitHub PR.'
    replayOutcome = 'RESOLVED'
    replaySummary = 'Baseline failure replayed; candidate repair confirmed and verified in isolated workspace.'
  } else if (isNoFailure) {
    currentAction = 'Repository Analysis Complete'
    engineeringAnalysis = 'CodeGuardian inspected the repository snapshot and did not identify a reproducible failure requiring automated repair. 0 files edited, no PR required.'
    replayOutcome = 'NOT REQUIRED'
    replaySummary = 'No reproducible application defect found in repository. Remediation not required.'
  } else if (isBaselineFailureNotReproduced) {
    currentAction = 'Baseline Failure Not Reproduced'
    engineeringAnalysis = 'The reported failure cannot be reproduced against the repository snapshot. The defect may already have been merged or fixed on the target branch.'
    replayOutcome = 'NOT REPRODUCED'
    replaySummary = 'Baseline defect could not be reproduced against the repository snapshot. Replay validation halted safely.'
  } else if (isPaused) {
    currentAction = 'Awaiting Human Approval'
    engineeringAnalysis = 'Candidate patch cleared all deterministic safety gates (Replay, Build, Tests, Compatibility). Operator review is required before GitHub delivery.'
  } else if (status === 'delivery_running' || status === 'delivered') {
    currentAction = 'Delivering Pull Request'
    engineeringAnalysis = 'Creating Git feature branch, committing patch, pushing to GitHub, and opening Pull Request.'
  } else if (status === 'investigation_failed') {
    currentAction = 'Investigation Failed'
    engineeringAnalysis = run?.error || 'OpenRouter returned HTTP 402 or investigation boundaries exceeded.'
    replayOutcome = 'BLOCKED'
    replaySummary = 'Investigation failed. Replay and Validation stages are blocked.'
  } else if (isFailed || isTerminal) {
    currentAction = status === 'rejected' ? 'Patch Rejected by Operator' : 'Investigation Halted'
    engineeringAnalysis = run?.error || 'Investigation halted: provider or validation bounds exceeded without viable patch candidate.'
    replayOutcome = 'FAILED'
    replaySummary = run?.error || 'Stage validation or investigation failed.'
  }

  return {
    headerStatus,
    headerTone,
    headerDot,
    headerBg,
    headerBorder,
    isTerminal,
    isPaused,
    currentAction,
    engineeringAnalysis,
    replayOutcome,
    replaySummary,
    isBaselineFailureNotReproduced,
    passedCount,
    totalStages,
    progressPercent,
    displayRepositoryName,
  }
}
