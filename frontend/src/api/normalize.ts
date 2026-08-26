import {
  asRecord,
  readBoolean,
  readNumber,
  readRecord,
  readRecordList,
  readString,
  readStringList,
  type JsonRecord,
} from './json'
import type {
  ChangedFile,
  TraceNode,
  CommandEntry,
  CommandResult,
  Compatibility,
  CompatibilityCheck,
  Delivery,
  FileDecision,
  RepositoryFileEntry,
  SourceFile,
  StackTrace,
  EvidenceItem,
  GhostTrace,
  Incident,
  Investigation,
  MemoryMatch,
  MemoryUpdate,
  Patch,
  Replay,
  ReplaySide,
  Repository,
  Run,
  RunStatus,
  Stage,
  StageStatus,
  TimelineEvent,
  Validation,
  ValidationGate,
} from './types'

const STAGE_STATUS: Record<string, StageStatus> = {
  pending: 'pending',
  queued: 'pending',
  not_started: 'pending',
  running: 'running',
  in_progress: 'running',
  active: 'running',
  pass: 'passed',
  passed: 'passed',
  success: 'passed',
  succeeded: 'passed',
  ok: 'passed',
  done: 'passed',
  complete: 'completed',
  completed: 'completed',
  fail: 'failed',
  failed: 'failed',
  error: 'failed',
  skipped: 'skipped',
  rejected: 'rejected',
  blocked: 'failed',
  waiting: 'waiting_for_approval',
  waiting_for_approval: 'waiting_for_approval',
  awaiting_approval: 'waiting_for_approval',
  approval: 'waiting_for_approval',
}

const RUN_STATUS: Record<string, RunStatus> = {
  queued: 'queued',
  pending: 'queued',
  running: 'running',
  in_progress: 'running',
  waiting_for_approval: 'waiting_for_approval',
  awaiting_approval: 'waiting_for_approval',
  approval: 'waiting_for_approval',
  completed: 'completed',
  complete: 'completed',
  success: 'completed',
  delivered: 'completed',
  failed: 'failed',
  error: 'failed',
  rejected: 'rejected',
}

function humanize(value: string): string {
  return value
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .toUpperCase()
}

export function toStageStatus(value: string | undefined): StageStatus {
  if (!value) return 'pending'
  return STAGE_STATUS[value.trim().toLowerCase()] ?? 'pending'
}

export function toRunStatus(value: string | undefined): RunStatus {
  if (!value) return 'running'
  return RUN_STATUS[value.trim().toLowerCase()] ?? 'running'
}

function normalizeStage(record: JsonRecord, index: number): Stage {
  const key = readString(record, 'key', 'id', 'stage', 'stage_key', 'name') ?? `stage-${index}`
  const name = readString(record, 'name', 'label', 'title', 'stage', 'stage_name') ?? key
  return {
    key,
    name: humanize(name),
    status: toStageStatus(readString(record, 'status', 'state', 'result')),
    description: readString(record, 'description', 'summary', 'message', 'detail'),
    detail: readString(record, 'detail', 'output', 'note'),
    startedAt: readString(record, 'started_at', 'startedAt', 'start_time'),
    completedAt: readString(record, 'completed_at', 'completedAt', 'end_time', 'finished_at'),
    durationMs: readNumber(record, 'duration_ms', 'durationMs', 'elapsed_ms'),
  }
}


function normalizeRepository(record: JsonRecord | undefined): Repository | undefined {
  if (!record) return undefined
  return {
    owner: readString(record, 'owner'),
    provider: readString(record, 'provider'),
    accessStatus: readString(record, 'access_status', 'accessStatus'),
    application: readString(record, 'application'),
    environment: readString(record, 'environment'),
    files: [],
    services: [],
    name: readString(record, 'name', 'full_name', 'repository_name', 'repo'),
    url: readString(record, 'url', 'repository_url', 'html_url', 'clone_url'),
    language: readString(record, 'language', 'primary_language'),
    framework: readString(record, 'framework', 'stack'),
    buildTool: readString(record, 'build_tool', 'buildTool', 'build_system'),
    defaultBranch: readString(record, 'default_branch', 'defaultBranch', 'base_branch'),
    fileCount: readNumber(record, 'file_count', 'files', 'files_scanned'),
  }
}

function normalizeIncident(record: JsonRecord | undefined): Incident | undefined {
  if (!record) return undefined
  return {
    title: readString(record, 'title', 'name', 'headline'),
    errorType: readString(record, 'error_type', 'errorType', 'exception', 'error', 'type'),
    service: readString(record, 'service', 'service_name', 'symptom_service', 'component'),
    environment: readString(record, 'environment', 'env'),
    endpoint: readString(record, 'endpoint', 'route', 'path', 'operation'),
    httpStatus: readNumber(record, 'http_status', 'httpStatus', 'observed_status_code', 'status_code'),
    firstSeen: readString(record, 'first_seen', 'first_seen_at', 'firstSeen', 'detected_at', 'created_at'),
    requestId: readString(record, 'request_id', 'requestId', 'correlation_id', 'trace_id'),
    attempts: readNumber(record, 'attempts', 'occurrences', 'event_count'),
    fingerprint: readString(record, 'fingerprint', 'error_fingerprint', 'signature'),
    category: readString(record, 'category', 'failure_category', 'classification', 'status'),
    summary: readString(record, 'summary', 'root_cause_summary', 'description', 'message'),
  }
}






function normalizeMemory(record: JsonRecord | undefined): MemoryMatch | undefined {
  if (!record) return undefined
  return {
    matchFound: readBoolean(record, 'match_found', 'matchFound'),
    matchReason: readString(record, 'match_reason', 'matchReason'),
    errorPattern: readString(record, 'error_pattern', 'errorPattern'),
    affectedFiles: readStringList(record, 'affected_files', 'affectedFiles'),
    status: readString(record, 'status', 'state', 'match_status', 'result'),
    fingerprint: readString(record, 'fingerprint', 'error_fingerprint', 'signature'),
    similarity: readNumber(record, 'similarity', 'similarity_score', 'score', 'confidence'),
    rootCauseService: readString(record, 'root_cause_service', 'service', 'rootCauseService'),
    previousFix: readString(record, 'previous_fix', 'previousFix', 'fix', 'resolution'),
    previousIncident: readString(record, 'previous_incident', 'incident_reference', 'reference'),
    verified: readBoolean(record, 'verified', 'is_verified'),
  }
}

function normalizeInvestigation(record: JsonRecord | undefined): Investigation | undefined {
  if (!record) return undefined
  const findingRecords = readRecordList(record, 'findings', 'steps', 'observations', 'report')
  const findings = findingRecords.map((finding, index) => ({
    label: readString(finding, 'label', 'name', 'key', 'title', 'stage') ?? `Finding ${index + 1}`,
    value: readString(finding, 'value', 'text', 'description', 'detail', 'content') ?? '',
  }))

  const structured: Array<[string, string | undefined]> = [
    ['Observation', readString(record, 'observation')],
    ['Evidence', readString(record, 'evidence_summary', 'evidenceSummary', 'evidence')],
    ['Hypothesis', readString(record, 'hypothesis')],
    ['Decision', readString(record, 'decision')],
    ['Result', readString(record, 'result')],
    ['Next action', readString(record, 'next_action', 'nextAction')],
  ]
  for (const [label, value] of structured) {
    if (value) findings.push({ label, value })
  }

  return {
    rootCause: readString(record, 'root_cause', 'rootCause', 'conclusion', 'summary'),
    confidence: readNumber(record, 'confidence', 'confidence_score', 'score'),
    findings,
    evidence: readStringList(record, 'evidence', 'evidence_points', 'signals'),
    sources: readStringList(record, 'sources', 'affected_files', 'inputs', 'context_sources'),
  }
}

function readFlag(record: JsonRecord | undefined, ...keys: string[]): string | undefined {
  const text = readString(record, ...keys)
  if (text) return text
  const flag = readBoolean(record, ...keys)
  if (flag === undefined) return undefined
  return flag ? 'Verified' : 'Failed'
}

function normalizePatch(record: JsonRecord | undefined): Patch | undefined {
  if (!record) return undefined
  return {
    id: readString(record, 'id', 'patch_id'),
    branch: readString(record, 'branch_name', 'branch'),
    commitMessage: readString(record, 'commit_message', 'commitMessage'),
    generatedBy: readString(record, 'generated_by', 'generatedBy'),
    reason: readString(record, 'generation_reason', 'reason'),
    affectedFiles: readStringList(record, 'affected_files', 'affectedFiles'),
    file: readString(record, 'file', 'affected_file', 'path', 'filename'),
    status: readString(record, 'status', 'state', 'validation_status'),
    diff: readString(record, 'diff', 'unified_diff', 'patch', 'content'),
    filesChanged: readNumber(record, 'files_changed', 'filesChanged'),
    linesAdded: readNumber(record, 'lines_added', 'linesAdded', 'additions'),
    linesRemoved: readNumber(record, 'lines_removed', 'linesRemoved', 'deletions'),
    pathSafety: readFlag(record, 'path_safety', 'pathSafety', 'path_safe', 'pathSafe'),
    languageCompatibility: readFlag(
      record,
      'language_compatibility',
      'languageCompatibility',
      'language_compatible',
      'languageCompatible',
      'language',
    ),
    contextMatch: readFlag(record, 'context_match', 'contextMatch', 'context_matched'),
  }
}

function normalizeReplaySide(record: JsonRecord | undefined, label: string): ReplaySide | undefined {
  if (!record) return undefined
  return {
    label,
    httpStatus: readNumber(record, 'http_status', 'status_code', 'status'),
    outcome: readString(record, 'outcome', 'result', 'error', 'error_type', 'message'),
    detail: readString(record, 'detail', 'description', 'body', 'summary'),
    passed: readBoolean(record, 'passed', 'success', 'ok'),
  }
}

function normalizeReplay(record: JsonRecord | undefined): Replay | undefined {
  if (!record) return undefined
  return {
    original: normalizeReplaySide(readRecord(record, 'original', 'before', 'baseline'), 'Original'),
    patched: normalizeReplaySide(readRecord(record, 'patched', 'after', 'repaired'), 'Patched'),
    behaviorChanged: readBoolean(record, 'behavior_changed', 'behaviorChanged', 'changed'),
    summary: readString(record, 'summary', 'description', 'conclusion'),
  }
}


function normalizeDelivery(record: JsonRecord | undefined): Delivery | undefined {
  if (!record) return undefined
  return {
    note: readString(record, 'note'),
    files: readStringList(record, 'files', 'affected_files'),
    mode: readString(record, 'mode', 'delivery_mode'),
    repository: readString(record, 'repository', 'repo', 'repository_name'),
    baseBranch: readString(record, 'base_branch', 'baseBranch', 'target_branch', 'base'),
    featureBranch: readString(record, 'feature_branch', 'featureBranch', 'branch'),
    commitMessage: readString(record, 'commit_message', 'commitMessage', 'commit'),
    pullRequestRef: readString(record, 'pull_request_ref', 'pull_request', 'pr_reference', 'pr_number'),
    pullRequestUrl: readString(record, 'pull_request_url', 'pr_url', 'html_url', 'url'),
    status: readString(record, 'status', 'state'),
  }
}

function normalizeMemoryUpdate(record: JsonRecord | undefined): MemoryUpdate | undefined {
  if (!record) return undefined
  return {
    status: readString(record, 'status', 'memory_status', 'state'),
    pattern: readString(record, 'pattern', 'error_pattern', 'error_fingerprint', 'fingerprint'),
    rootCause: readString(record, 'root_cause', 'rootCause'),
    affectedFile: readString(record, 'affected_file', 'file', 'path'),
    codeChange: readString(record, 'code_change', 'change', 'fix'),
    validationResult: readString(record, 'validation_result', 'validation'),
    deliveryReference: readString(record, 'delivery_reference', 'delivery_result', 'delivery', 'pull_request'),
  }
}


function titleize(value: string): string {
  return value
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
    .trim()
}

/** Turn a flat backend record into label/value rows, skipping the keys shown elsewhere. */
function toChecks(record: JsonRecord | undefined, skip: string[]): CompatibilityCheck[] {
  if (!record) return []
  const rows: CompatibilityCheck[] = []
  for (const [key, value] of Object.entries(record)) {
    if (skip.includes(key) || value === null || value === undefined) continue
    if (typeof value === 'object') continue
    rows.push({ label: titleize(key), value: String(value) })
  }
  return rows
}

function normalizeAgentEvent(record: JsonRecord, index: number): TimelineEvent {
  const title = readString(record, 'title')
  const description = readString(record, 'description')
  const output = readString(record, 'output')
  return {
    id: readString(record, 'id') ?? `event-${index}`,
    timestamp: readString(record, 'timestamp'),
    channel: readString(record, 'related_stage', 'type'),
    message: description ?? output ?? title ?? '',
    level: readString(record, 'type'),
    status: toStageStatus(readString(record, 'status')),
    stage: title,
    command: readString(record, 'command'),
    output,
  }
}

function normalizeCommand(record: JsonRecord, index: number): CommandEntry {
  return {
    id: readString(record, 'id') ?? `command-${index}`,
    timestamp: readString(record, 'timestamp'),
    command: readString(record, 'display_command', 'command') ?? '',
    output: readString(record, 'output'),
    status: toStageStatus(readString(record, 'status')),
    stage: readString(record, 'related_stage'),
  }
}

function normalizeChangedFile(record: JsonRecord, index: number): ChangedFile {
  const decision = readString(record, 'decision')
  return {
    id: readString(record, 'id') ?? `file-${index}`,
    path: readString(record, 'path') ?? '',
    name: readString(record, 'name') ?? readString(record, 'path') ?? `File ${index + 1}`,
    diff: readString(record, 'diff'),
    additions: readNumber(record, 'additions'),
    deletions: readNumber(record, 'deletions'),
    decision:
      decision === 'accepted' || decision === 'rejected' ? (decision as FileDecision) : 'pending',
  }
}

function normalizeSourceFile(record: JsonRecord, index: number): SourceFile {
  return {
    id: readString(record, 'id') ?? `source-${index}`,
    path: readString(record, 'path') ?? `file-${index}`,
    language: readString(record, 'language'),
    content: readString(record, 'content'),
  }
}

function normalizeStackTrace(record: JsonRecord | undefined): StackTrace | undefined {
  if (!record) return undefined
  return {
    available: readBoolean(record, 'available') ?? false,
    service: readString(record, 'service'),
    errorCode: readString(record, 'error_code'),
    content: readString(record, 'content'),
  }
}

function normalizeCompatibility(record: JsonRecord | undefined): Compatibility | undefined {
  if (!record) return undefined
  return {
    result: readString(record, 'result'),
    checkedFiles: readStringList(record, 'checked_files'),
    checks: toChecks(record, ['result', 'checked_files']),
  }
}

function normalizeCommandResult(record: JsonRecord | undefined): CommandResult | undefined {
  if (!record) return undefined
  const summaryRecord = readRecord(record, 'summary')
  return {
    command: readString(record, 'command'),
    output: readString(record, 'output'),
    result: readString(record, 'result'),
    summary: [
      ...toChecks(record, ['command', 'output', 'result', 'summary']),
      ...toChecks(summaryRecord, []),
    ],
  }
}

function normalizeWorkspaceTrace(record: JsonRecord | undefined): GhostTrace | undefined {
  if (!record) return undefined
  const nodes: TraceNode[] = readRecordList(record, 'nodes').map((node, index) => ({
    id: readString(node, 'id') ?? `node-${index}`,
    label: readString(node, 'service_name') ?? `Node ${index + 1}`,
    detail: readString(node, 'error_message', 'endpoint'),
    kind: readString(node, 'node_type'),
    isRootCause: readString(node, 'node_type') === 'root_cause',
    isSymptom: readString(node, 'node_type') === 'symptom',
    status: readString(node, 'status_code'),
  }))
  return {
    nodes,
    rootCause: readString(record, 'root_cause_candidate'),
    symptom: readString(record, 'symptom_service'),
    summary: readString(record, 'reasoning_summary', 'summary'),
  }
}

function normalizeWorkspaceValidation(record: JsonRecord | undefined): Validation | undefined {
  if (!record) return undefined
  const gates: ValidationGate[] = readRecordList(record, 'gates').map((gate, index) => ({
    name: humanize(readString(gate, 'name') ?? `Gate ${index + 1}`),
    passed: readBoolean(gate, 'result', 'passed'),
    detail: readString(gate, 'detail'),
  }))
  return {
    gates,
    status: readString(record, 'status', 'final'),
    passedCount: gates.filter((gate) => gate.passed).length,
    totalCount: gates.length,
  }
}

function normalizeWorkspaceEvidence(record: JsonRecord, index: number): EvidenceItem {
  const statusCode = readNumber(record, 'status_code')
  const detail = [
    readString(record, 'error_message'),
    readString(record, 'endpoint'),
    statusCode === undefined ? undefined : `HTTP ${statusCode}`,
    readString(record, 'error_code'),
  ]
    .filter(Boolean)
    .join(' · ')
  return {
    id: readString(record, 'id') ?? `evidence-${index}`,
    label: humanize(readString(record, 'type') ?? `Evidence ${index + 1}`),
    value: readString(record, 'message'),
    detail: detail || undefined,
    timestamp: readString(record, 'timestamp'),
  }
}

/**
 * Normalize `GET /api/runs/{id}/workspace`, the single payload that carries the
 * whole investigation: stages, artefacts, agent events and command log.
 */
export function normalizeWorkspace(payload: unknown): Run | undefined {
  const workspace = asRecord(payload)
  if (!workspace) return undefined

  const runRecord = readRecord(workspace, 'run') ?? {}
  const repositoryRecord = readRecord(workspace, 'repository')
  const inspection = readRecord(workspace, 'inspection')
  const architecture = readRecord(workspace, 'architecture')
  const repository = normalizeRepository(repositoryRecord)
  if (repository) {
    repository.framework = repository.framework ?? readString(architecture, 'framework')
    repository.buildTool = repository.buildTool ?? readString(architecture, 'build_tool')
    repository.language = repository.language ?? readString(architecture, 'language')
    repository.fileCount = readNumber(inspection, 'files_scanned')
    repository.services = readStringList(architecture, 'services')
    repository.files = readRecordList(inspection, 'files')
      .map((file): RepositoryFileEntry => ({
        path: readString(file, 'path') ?? '',
        language: readString(file, 'language'),
      }))
      .filter((file) => file.path !== '')
  }

  const patch = normalizePatch(readRecord(workspace, 'patch'))
  const changedFiles = readRecordList(workspace, 'changed_files').map(normalizeChangedFile)
  const compatibility = normalizeCompatibility(readRecord(workspace, 'compatibility'))
  const deliveryRecord = readRecord(workspace, 'delivery')
  const delivery = normalizeDelivery(
    deliveryRecord && Object.keys(deliveryRecord).length > 0 ? deliveryRecord : undefined,
  )
  if (delivery) {
    delivery.repository = delivery.repository ?? repository?.url ?? repository?.name
  }
  const compatibilityCheck = (label: string): string | undefined =>
    compatibility?.checks.find((check) => check.label.toLowerCase() === label)?.value

  if (patch) {
    patch.file = patch.file ?? patch.affectedFiles[0] ?? changedFiles[0]?.path
    patch.pathSafety = patch.pathSafety ?? compatibilityCheck('path safety')
    patch.languageCompatibility = patch.languageCompatibility ?? compatibilityCheck('language')
    patch.contextMatch = patch.contextMatch ?? compatibilityCheck('source context')
    patch.filesChanged = patch.filesChanged ?? changedFiles.length
    patch.linesAdded =
      patch.linesAdded ?? changedFiles.reduce((total, file) => total + (file.additions ?? 0), 0)
    patch.linesRemoved =
      patch.linesRemoved ?? changedFiles.reduce((total, file) => total + (file.deletions ?? 0), 0)
  }

  return {
    runId: readString(runRecord, 'id') ?? '',
    status: toRunStatus(readString(runRecord, 'status')),
    mode: readString(runRecord, 'mode'),
    scenarioId: readString(runRecord, 'scenario_id'),
    approvalState: readString(runRecord, 'approval_state'),
    deliveryState: readString(runRecord, 'delivery_state'),
    error: readString(runRecord, 'error'),
    currentStage: readString(runRecord, 'current_stage'),
    startedAt: readString(runRecord, 'started_at'),
    completedAt: readString(runRecord, 'completed_at'),
    repositoryUrl: repository?.url,
    repository,
    incident: normalizeIncident(readRecord(workspace, 'incident')),
    stages: readRecordList(workspace, 'stages').map(normalizeStage),
    events: readRecordList(workspace, 'agent_events').map(normalizeAgentEvent),
    commands: readRecordList(workspace, 'command_log').map(normalizeCommand),
    evidence: readRecordList(workspace, 'evidence').map(normalizeWorkspaceEvidence),
    ghostTrace: normalizeWorkspaceTrace(readRecord(workspace, 'trace')),
    stackTrace: normalizeStackTrace(readRecord(workspace, 'stack_trace')),
    sourceFiles: readRecordList(workspace, 'source').map(normalizeSourceFile),
    changedFiles,
    compatibility,
    build: normalizeCommandResult(readRecord(workspace, 'build')),
    tests: normalizeCommandResult(readRecord(workspace, 'tests')),
    memory: normalizeMemory({
      ...(readRecord(readRecord(workspace, 'memory'), 'memory') ?? {}),
      ...(readRecord(workspace, 'memory') ?? {}),
    }),
    investigation: normalizeInvestigation(readRecord(workspace, 'investigation')),
    patch,
    replay: normalizeReplay(readRecord(workspace, 'replay')),
    validation: normalizeWorkspaceValidation(readRecord(workspace, 'validation')),
    delivery,
    memoryUpdate: normalizeMemoryUpdate(
      (() => {
        const record = readRecord(workspace, 'memory_update')
        return record && Object.keys(record).length > 0 ? record : undefined
      })(),
    ),
  }
}
