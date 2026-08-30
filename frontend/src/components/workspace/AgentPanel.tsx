import type { Run } from '../../api/types'
import { StatusDot } from '../primitives'

function getAgentContent(stageKey?: string) {
  switch (stageKey) {
    case '01_repository':
      return {
        action: 'Inspecting repository',
        analysis: "Reading repository metadata and detecting the application's language, framework, build system and test structure.",
        command: '$ inspect_repository',
        output: 'Java\nSpring Boot\nMaven\n94 files',
        finding: 'Repository structure identified.',
        nextAction: 'Collect failure evidence →',
      }
    case '02_inspection':
    case '03_architecture':
    case '04_failure_detection':
      return {
        action: 'Detecting failure',
        analysis: 'Correlating available runtime failure evidence with the current incident.',
        command: '$ detect_failure --request req-demo-1',
        output: 'HTTP 500\nNULL_OBJECT_ACCESS',
        finding: 'Failure signal detected.',
        nextAction: 'Collect evidence →',
      }
    case '05_evidence':
      return {
        action: 'Collecting failure evidence',
        analysis: 'Filtering request, log and stack-trace signals associated with the affected request.',
        command: '$ collect_evidence --request req-demo-1',
        output: '6 evidence sources collected',
        finding: '4 signals are directly relevant.',
        nextAction: 'GhostTrace reconstruction →',
      }
    case '06_ghost_trace':
      return {
        action: 'Reconstructing failure path',
        analysis: 'Correlating request ID, timestamps and service dependencies.',
        command: '$ ghosttrace --request req-demo-1',
        output: 'Gateway → Order Service → Payment Service → PostgreSQL',
        finding: 'Payment Service is the first application-owned failure point.',
        nextAction: 'Search Failure Memory →',
      }
    case '07_failure_memory':
      return {
        action: 'Searching historical incidents',
        analysis: 'Comparing fingerprint, affected service and causal path against validated incidents.',
        output: '2 candidate matches\nBest match: INC-0918\nSimilarity: 90%',
        finding: 'Previous validated resolution exists for this failure pattern.',
        nextAction: 'Investigate source →',
      }
    case '08_investigation':
      return {
        action: 'Investigating root cause',
        analysis: 'Comparing runtime evidence with the relevant source location.',
        output: 'Root cause location identified in source',
        finding: 'Defect mechanism isolated from runtime failure evidence.',
        nextAction: 'Generate repair candidate →',
      }
    case '09_patch':
      return {
        action: 'Generating repair candidate',
        analysis: 'Preparing the smallest source change that addresses the verified root cause without modifying unrelated code.',
        output: '1 file changed',
        finding: 'Repair candidate targets verified root cause location.',
        nextAction: 'Run compatibility checks →',
      }
    case '10_compatibility':
      return {
        action: 'Checking patch safety',
        analysis: 'Verifying path safety, language compatibility and source context.',
        output: 'Path safety PASS\nLanguage PASS\nContext PASS',
        finding: 'Patch is eligible for replay.',
        nextAction: 'Replay original failure →',
      }
    case '11_replay':
      return {
        action: 'Replaying failure',
        analysis: 'Running the captured failure condition against the original and patched source.',
        command: '$ replay_incident req-demo-1',
        output: 'Baseline failure reproduced\nPatched behavior completed successfully',
        finding: 'Original failure no longer reproduces.',
        nextAction: 'Build and test →',
      }
    case '12_build':
      return {
        action: 'Building patched source',
        command: '$ ./mvnw test', // Using generic build cmd as example or from real event
        output: 'Build PASS',
        finding: 'Patched source compiles successfully.',
        nextAction: 'Run tests →',
      }
    case '13_tests':
      return {
        action: 'Running regression tests',
        output: '8 total\n8 passed\n0 failed',
        finding: 'No regression detected.',
        nextAction: 'Validation →',
      }
    case '14_validation':
      return {
        action: 'Running validation gates',
        output: 'PATCH CONTEXT PASS\nPATCH LANGUAGE PASS\nPATH SAFETY PASS\nBASELINE REPRODUCED PASS\nPATCH APPLIED PASS\nBUILD PASS\nTESTS PASS\nREPLAY PASS',
        finding: 'All required safety gates passed.',
        nextAction: 'Human approval →',
      }
    case '15_human_approval':
      return {
        action: 'Waiting for human approval',
        analysis: 'Automated validation passed. Delivery is intentionally blocked until a human reviews the repair.',
        finding: 'Patch is ready for review.',
        nextAction: 'Approve or reject →',
      }
    case '16_delivery':
      return {
        action: 'Preparing Pull Request',
        output: 'Branch: codeguardian/fix\nFiles changed: 1\nValidation: PASSED',
        finding: 'Repair is ready for source-control delivery.',
        nextAction: 'Create Pull Request →',
      }
    case '17_memory_update':
      return {
        action: 'Updating Failure Memory',
        analysis: 'Persisting the validated failure pattern and confirmed repair for future investigations.',
        output: 'Memory update committed.',
        finding: 'Future investigations can reference this validated resolution.',
        nextAction: 'Investigation complete →',
      }
    default:
      return {
        action: 'Initializing',
        analysis: 'Connecting to workspace and synchronizing state.',
        finding: 'Workspace ready.',
        nextAction: 'Proceed →',
      }
  }
}

function Block({ label, children, border = true }: { label: string; children: React.ReactNode, border?: boolean }) {
  return (
    <div className={`px-5 py-4 ${border ? 'border-b border-ink-700' : ''}`}>
      <p className="font-mono text-[10px] uppercase tracking-widest text-ink-500 mb-3">{label}</p>
      <div className="text-sm text-white space-y-2">{children}</div>
    </div>
  )
}

export function AgentPanel({ run }: { run: Run }) {
  const content = getAgentContent(run.currentStage)
  
  // Real backend overrides where appropriate for output (don't override action/analysis to preserve state sync)
  const isComplete = run.status === 'completed'
  const isRejected = run.status === 'rejected'

  return (
    <aside className="flex h-full flex-col overflow-y-auto border-l border-ink-700 bg-ink-850 shrink-0 w-80 lg:w-96">
      <div className="flex items-center justify-between gap-3 border-b border-ink-700 px-5 py-4 sticky top-0 bg-ink-850 z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <StatusDot status={isComplete ? 'passed' : isRejected ? 'failed' : 'running'} />
          <p className="font-display text-sm font-bold tracking-tight">AI AGENT</p>
        </div>
        <span className="font-mono text-[10px] text-lime border border-lime/30 px-2 py-0.5 rounded-sm">CodeGuardian Investigator</span>
      </div>
      
      <Block label="Current Action">
        <span className="font-semibold text-lime">
          {isComplete ? 'Investigation complete' : isRejected ? 'Delivery blocked' : content.action}
        </span>
      </Block>

      {content.analysis && !isComplete && !isRejected ? (
        <Block label="Engineering Analysis">
          <p className="text-ink-300 leading-relaxed text-xs">
            {content.analysis}
          </p>
        </Block>
      ) : null}

      {content.command && !isComplete && !isRejected ? (
        <Block label="Command">
          <div className="bg-ink-900 border border-ink-700 rounded-md p-3 font-mono text-[11px] text-white">
            <span className="text-lime">$</span> {content.command}
          </div>
        </Block>
      ) : null}

      {content.output && !isComplete && !isRejected ? (
        <Block label="Output">
          <pre className="bg-ink-900 border border-ink-700 rounded-md p-3 font-mono text-[11px] text-ink-300 whitespace-pre-wrap">
            {content.output}
          </pre>
        </Block>
      ) : null}

      <Block label="Finding">
        <div className={`bg-lime/10 border border-lime/20 rounded-md p-3 text-xs text-lime flex items-start gap-2 ${isRejected ? 'bg-signal-pink/10 border-signal-pink/20 text-signal-pink' : ''}`}>
          <span className="mt-0.5 shrink-0">{isRejected ? '✕' : '✓'}</span>
          <div>
            <p className="font-bold mb-1">{isRejected ? 'BLOCKED' : 'IDENTIFIED'}</p>
            <p className={isRejected ? 'text-signal-pink/80' : 'text-ink-300'}>
              {isComplete ? 'Verified resolution delivered.' : isRejected ? 'Patch rejected by human reviewer.' : content.finding}
            </p>
          </div>
        </div>
      </Block>

      {!isComplete && !isRejected ? (
        <Block label="Next Action" border={false}>
          <p className="font-mono text-xs text-ink-300 flex items-center gap-2">
            {content.nextAction} <span className="text-lime">→</span>
          </p>
        </Block>
      ) : null}
      
      {/* Quick Actions (Agent Interaction) */}
      <div className="mt-auto border-t border-ink-700 p-4">
        <div className="grid grid-cols-2 gap-2">
           <button type="button" className="btn-ghost py-1.5 text-[10px] font-mono">View details</button>
           <button type="button" className="btn-ghost py-1.5 text-[10px] font-mono">View logs</button>
           <button type="button" className="btn-ghost py-1.5 text-[10px] font-mono">Open source</button>
           <button type="button" className="btn-ghost py-1.5 text-[10px] font-mono">Copy output</button>
        </div>
      </div>
    </aside>
  )
}
