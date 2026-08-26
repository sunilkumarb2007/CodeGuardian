export type StageStatus =
  | 'pending'
  | 'running'
  | 'passed'
  | 'failed'
  | 'waiting_for_approval'
  | 'rejected'
  | 'skipped'
  | 'completed'

export type RunStatus =
  | 'queued'
  | 'running'
  | 'waiting_for_approval'
  | 'completed'
  | 'failed'
  | 'rejected'

export interface Stage {
  key: string
  name: string
  status: StageStatus
  description?: string
  detail?: string
  startedAt?: string
  completedAt?: string
  durationMs?: number
}

export interface TimelineEvent {
  id: string
  timestamp?: string
  channel?: string
  message: string
  level?: string
  status?: StageStatus
  stage?: string
  command?: string
  output?: string
}

export interface CommandEntry {
  id: string
  timestamp?: string
  command: string
  output?: string
  status?: StageStatus
  stage?: string
}

export type FileDecision = 'pending' | 'accepted' | 'rejected'

export interface ChangedFile {
  id: string
  path: string
  name: string
  diff?: string
  additions?: number
  deletions?: number
  decision: FileDecision
}

export interface SourceFile {
  id: string
  path: string
  language?: string
  content?: string
}

export interface StackTrace {
  available: boolean
  service?: string
  errorCode?: string
  content?: string
}

export interface CompatibilityCheck {
  label: string
  value: string
}

export interface Compatibility {
  checks: CompatibilityCheck[]
  result?: string
  checkedFiles: string[]
}

export interface CommandResult {
  command?: string
  output?: string
  result?: string
  summary: CompatibilityCheck[]
}

export interface Incident {
  title?: string
  errorType?: string
  service?: string
  environment?: string
  endpoint?: string
  httpStatus?: number
  firstSeen?: string
  requestId?: string
  attempts?: number
  fingerprint?: string
  category?: string
  summary?: string
}

export interface RepositoryFileEntry {
  path: string
  language?: string
}

export interface Repository {
  owner?: string
  provider?: string
  accessStatus?: string
  application?: string
  environment?: string
  files: RepositoryFileEntry[]
  services: string[]
  name?: string
  url?: string
  language?: string
  framework?: string
  buildTool?: string
  defaultBranch?: string
  fileCount?: number
}

export interface TraceNode {
  id: string
  label: string
  detail?: string
  kind?: string
  isRootCause?: boolean
  isSymptom?: boolean
  status?: string
}

export interface GhostTrace {
  nodes: TraceNode[]
  rootCause?: string
  symptom?: string
  summary?: string
}

export interface EvidenceItem {
  id: string
  label: string
  value?: string
  detail?: string
  timestamp?: string
}

export interface MemoryMatch {
  matchFound?: boolean
  matchReason?: string
  errorPattern?: string
  affectedFiles: string[]
  status?: string
  fingerprint?: string
  similarity?: number
  rootCauseService?: string
  previousFix?: string
  previousIncident?: string
  verified?: boolean
}

export interface InvestigationFinding {
  label: string
  value: string
}

export interface Investigation {
  rootCause?: string
  confidence?: number
  findings: InvestigationFinding[]
  evidence: string[]
  sources: string[]
}

export interface Patch {
  id?: string
  branch?: string
  commitMessage?: string
  generatedBy?: string
  reason?: string
  affectedFiles: string[]
  file?: string
  status?: string
  diff?: string
  filesChanged?: number
  linesAdded?: number
  linesRemoved?: number
  pathSafety?: string
  languageCompatibility?: string
  contextMatch?: string
}

export interface ReplaySide {
  label: string
  httpStatus?: number
  outcome?: string
  detail?: string
  passed?: boolean
}

export interface Replay {
  original?: ReplaySide
  patched?: ReplaySide
  behaviorChanged?: boolean
  summary?: string
}

export interface ValidationGate {
  name: string
  passed?: boolean
  detail?: string
}

export interface Validation {
  gates: ValidationGate[]
  status?: string
  passedCount?: number
  totalCount?: number
}

export interface Delivery {
  note?: string
  files: string[]
  mode?: string
  repository?: string
  baseBranch?: string
  featureBranch?: string
  commitMessage?: string
  pullRequestRef?: string
  pullRequestUrl?: string
  status?: string
}

export interface MemoryUpdate {
  status?: string
  pattern?: string
  rootCause?: string
  affectedFile?: string
  codeChange?: string
  validationResult?: string
  deliveryReference?: string
}

export interface Run {
  runId: string
  status: RunStatus
  mode?: string
  scenarioId?: string
  approvalState?: string
  deliveryState?: string
  error?: string
  commands: CommandEntry[]
  changedFiles: ChangedFile[]
  sourceFiles: SourceFile[]
  stackTrace?: StackTrace
  compatibility?: Compatibility
  build?: CommandResult
  tests?: CommandResult
  currentStage?: string
  repositoryUrl?: string
  startedAt?: string
  completedAt?: string
  repository?: Repository
  incident?: Incident
  stages: Stage[]
  events: TimelineEvent[]
  evidence: EvidenceItem[]
  ghostTrace?: GhostTrace
  memory?: MemoryMatch
  investigation?: Investigation
  patch?: Patch
  replay?: Replay
  validation?: Validation
  delivery?: Delivery
  memoryUpdate?: MemoryUpdate
}
