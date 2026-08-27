import { useState } from 'react'
import type { Run } from '../../api/types'

interface StageAgentConfig {
  action: string
  thought: string
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
    thought: "Analyzing directory structure, language definitions, and build configuration files.",
    command: '$ inspect_repository --branch main',
    output: 'Java 17 / Spring Boot / Maven\n94 files discovered across 3 packages\nRepository root: clean',
    finding: {
      title: 'Repository structure identified.',
      detail: 'Spring Boot web application target with isolated test harness.',
    },
    nextAction: {
      title: 'Analyze application architecture',
      estimatedTime: '1–2s',
    },
  },
  '02_inspection': {
    action: 'Mapping source tree',
    thought: 'Scanning classes, endpoints, service boundaries, and persistence models.',
    command: '$ scan_source_tree --framework spring-boot',
    output: 'PaymentController -> PaymentService -> PaymentRepository\nPostgreSQL datasource detected',
    finding: {
      title: 'Architecture map built.',
      detail: 'Clear layered architecture with database dependency.',
    },
    nextAction: {
      title: 'Detect failure signals',
      estimatedTime: '2–3s',
    },
  },
  '03_architecture': {
    action: 'Evaluating dependencies',
    thought: 'Detecting testing framework, test runners, and runtime requirements.',
    command: '$ check_build_system',
    output: 'Maven Surefire plugin configured\nJUnit 5 + Spring Test detected',
    finding: {
      title: 'Build and test strategies configured.',
      detail: 'Maven wrapper executable and test runners available.',
    },
    nextAction: {
      title: 'Run failure detection',
      estimatedTime: '2s',
    },
  },
  '04_failure_detection': {
    action: 'Failure Detection',
    thought: 'Analyzing error pattern across services and parsing recent logs to confirm the failure signal.',
    command: '$ detect failure --request req-demo-1',
    output: 'NULL_OBJECT_ACCESS detected on\nPOST /payments/charge (HTTP 500).\nNullPointerException in PaymentService.charge\nat line 82.\nOccurrence count: 1\nSeverity: Medium',
    finding: {
      title: 'Null object dereference in business flow.',
      detail: 'paymentRecord is null but accessed.',
    },
    nextAction: {
      title: 'GhostTrace reconstruction',
      estimatedTime: '3–5s',
    },
  },
  '05_evidence': {
    action: 'Collecting failure evidence',
    thought: 'Extracting HTTP request payload, stack trace, runtime exceptions, and surrounding log lines.',
    command: '$ collect_evidence --request req-demo-1',
    output: 'HTTP 500 response captured\nStack trace isolated to PaymentService.java:82\nDatabase query log extracted',
    finding: {
      title: 'Verified execution evidence assembled.',
      detail: 'Causal chain contains 4 verified telemetry nodes.',
    },
    nextAction: {
      title: 'Run GhostTrace reconstruction',
      estimatedTime: '3s',
    },
  },
  '06_ghost_trace': {
    action: 'Reconstructing causal flow',
    thought: 'Tracking execution from Gateway through Order Service, Payment Service to PostgreSQL.',
    command: '$ ghosttrace --request req-demo-1',
    output: 'Gateway (142ms) -> Order Service (87ms) -> Payment Service (17ms [ERR]) -> PostgreSQL [TIMEOUT]',
    finding: {
      title: 'Root cause service identified.',
      detail: 'Database timeout caused null return in PaymentService.',
    },
    nextAction: {
      title: 'Search historical failure memory',
      estimatedTime: '2–4s',
    },
  },
  '07_failure_memory': {
    action: 'Searching failure memory',
    thought: 'Querying vector memory of validated previous repairs for null pointer and timeout patterns.',
    command: '$ memory_search --fingerprint NULL_OBJECT_ACCESS',
    output: 'Match found: INC-0918 (90% similarity)\nPrevious resolution: Null-check validation pattern',
    finding: {
      title: 'Validated memory reference available.',
      detail: 'Historical repair validated with 8/8 test pass rate.',
    },
    nextAction: {
      title: 'Investigate source and bounded context',
      estimatedTime: '4–6s',
    },
  },
  '08_investigation': {
    action: 'Investigating root cause',
    thought: 'Correlating bounded source code at line 82 with GhostTrace evidence and failure memory.',
    command: '$ investigate --source PaymentService.java',
    output: 'Root cause confirmed: repository.findById(id) returned null due to timeout,\ndereferenced without check.',
    finding: {
      title: 'Root cause analysis complete.',
      detail: 'Missing null verification before calling record.getAmount().',
    },
    nextAction: {
      title: 'Generate constrained repair candidate',
      estimatedTime: '5–8s',
    },
  },
  '09_patch': {
    action: 'Generating repair candidate',
    thought: 'Synthesizing minimal, defensive patch adhering to repository idioms and conventions.',
    command: '$ generate_patch --target PaymentService.java',
    output: '1 file modified: PaymentService.java\n+3 lines added, 0 lines removed\nDefensive PaymentNotFoundException added',
    finding: {
      title: 'Candidate patch generated.',
      detail: 'Constrained to PaymentService.java without modifying interfaces.',
    },
    nextAction: {
      title: 'Run patch compatibility check',
      estimatedTime: '2s',
    },
  },
  '10_compatibility': {
    action: 'Checking patch safety',
    thought: 'Verifying syntax, imports, method signatures, path bounds, and safety limits.',
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
    thought: 'Applying patch in isolated workspace and replaying the exact production request.',
    command: '$ replay_failure --workspace /tmp/patch_ws',
    output: 'Baseline: HTTP 500 (NPE)\nPatched: HTTP 404 (PaymentNotFoundException)\nFailure resolved.',
    finding: {
      title: 'Failure resolution proven.',
      detail: 'Controlled error response returned instead of uncaught exception.',
    },
    nextAction: {
      title: 'Compile and build patched workspace',
      estimatedTime: '5s',
    },
  },
  '12_build': {
    action: 'Compiling patched repository',
    thought: 'Running Maven compilation in isolated sandbox container.',
    command: '$ ./mvnw clean compile -DskipTests',
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
    thought: 'Executing all unit and integration tests to verify no regressions were introduced.',
    command: '$ ./mvnw test',
    output: 'Tests run: 8, Failures: 0, Errors: 0, Skipped: 0\nAll tests passed in 3.4s',
    finding: {
      title: 'Regression tests passed.',
      detail: '8 of 8 automated tests passed without regressions.',
    },
    nextAction: {
      title: 'Evaluate validation safety gates',
      estimatedTime: '2s',
    },
  },
  '14_validation': {
    action: 'Evaluating validation gates',
    thought: 'Verifying build, test, replay, and safety metrics against promotion criteria.',
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
    thought: 'All deterministic gates passed. Human approval is required before delivery.',
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
    thought: 'Creating Git feature branch, committing patch, pushing to GitHub and opening PR.',
    command: '$ git checkout -b codeguardian/fix-payment-npe && git push',
    output: 'Branch: codeguardian/fix-payment-npe\nCommit: 8f42d19 fix(payment): handle null payment record\nPR #42 created on GitHub',
    finding: {
      title: 'Pull Request published.',
      detail: 'Branch created on GitHub with detailed evidence report.',
    },
    nextAction: {
      title: 'Persist validated resolution to memory',
      estimatedTime: '1s',
    },
  },
  '17_memory_update': {
    action: 'Updating failure memory',
    thought: 'Indexing incident evidence, causal fingerprint, and validated patch into failure memory.',
    command: '$ memory_persist --incident INV-1042',
    output: 'Knowledge base updated: INC-1042 recorded\nMemory embedding indexed',
    finding: {
      title: 'Failure memory updated.',
      detail: 'Proven solution is now available to accelerate future investigations.',
    },
    nextAction: {
      title: 'Investigation complete',
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
  const stageKey = run?.currentStage || '04_failure_detection'
  const config = STAGE_AGENT_MAP[stageKey] || STAGE_AGENT_MAP['04_failure_detection']

  const handleCopy = () => {
    if (config.command) {
      navigator.clipboard.writeText(config.command)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  return (
    <aside className="w-[300px] xl:w-[320px] shrink-0 border-l border-white/[0.08] bg-[#070A0B] flex flex-col justify-between overflow-y-auto select-none z-20">
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="border-b border-white/[0.08] pb-3 space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-lime animate-pulse" />
              <span className="font-mono text-xs font-bold text-white tracking-wide">
                AI AGENT
              </span>
            </div>
            <div className="flex items-center gap-2 text-zinc-400">
              <button
                type="button"
                aria-label="Pause"
                className="hover:text-white transition-colors p-1"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </button>
              <button
                type="button"
                aria-label="Reset"
                className="hover:text-white transition-colors p-1"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 font-display text-sm font-bold text-white">
              <svg className="h-4 w-4 text-purple-400" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
              </svg>
              <span>AutoFix</span>
            </div>
            <span className="rounded bg-purple-500/20 px-1.5 py-0.2 font-mono text-[10px] font-semibold text-purple-300">
              beta
            </span>
          </div>
        </div>

        {/* Current Action */}
        <div>
          <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-widest block mb-1 font-bold">
            CURRENT ACTION
          </span>
          <div className="flex items-center justify-between">
            <span className="font-display text-xs font-bold text-white tracking-wide">
              {config.action}
            </span>
            <span className="relative flex h-3 w-3">
              <span className="animate-spin inline-flex h-full w-full rounded-full border-2 border-lime border-t-transparent" />
            </span>
          </div>
        </div>

        {/* Thought */}
        <div>
          <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-widest block mb-1 font-bold">
            THOUGHT
          </span>
          <p className="text-xs text-zinc-300 leading-relaxed font-sans">
            {config.thought}
          </p>
        </div>

        {/* Command */}
        {config.command ? (
          <div>
            <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-widest block mb-1 font-bold">
              COMMAND
            </span>
            <div className="flex items-center justify-between p-2 rounded-lg border border-white/[0.08] bg-[#0F1518] font-mono text-xs text-zinc-200">
              <span className="truncate pr-2">
                <span className="text-lime mr-1.5">$</span>
                {config.command.replace(/^\$\s*/, '')}
              </span>
              <button
                type="button"
                onClick={handleCopy}
                aria-label="Copy command"
                className="text-zinc-500 hover:text-white shrink-0"
              >
                {copied ? (
                  <svg className="h-3.5 w-3.5 text-lime" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        ) : null}

        {/* Output */}
        {config.output ? (
          <div>
            <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-widest block mb-1 font-bold">
              OUTPUT
            </span>
            <pre className="p-2.5 rounded-lg border border-white/[0.08] bg-[#0F1518] text-[11px] font-mono text-zinc-300 leading-relaxed overflow-x-auto whitespace-pre-wrap">
              {config.output}
            </pre>
          </div>
        ) : null}

        {/* Finding */}
        {config.finding ? (
          <div>
            <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-widest block mb-1 font-bold">
              FINDING
            </span>
            <div className="p-3 rounded-lg border border-lime/30 bg-lime/[0.04] space-y-1">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-lime">
                <svg className="h-3.5 w-3.5 shrink-0" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span>{config.finding.title}</span>
              </div>
              <p className="text-[11px] text-zinc-300 font-sans pl-5">
                {config.finding.detail}
              </p>
            </div>
          </div>
        ) : null}

        {/* Next Action */}
        <div className="pt-2 border-t border-white/[0.06]">
          <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-widest block mb-1 font-bold">
            NEXT ACTION
          </span>
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs font-semibold text-white">{config.nextAction.title}</p>
              <p className="text-[10px] font-mono text-zinc-500">
                Estimated time: {config.nextAction.estimatedTime}
              </p>
            </div>
            <span className="text-xs font-mono text-lime hover:underline cursor-pointer">
              View details →
            </span>
          </div>
        </div>
      </div>

      {/* Quick Actions (2x2 Grid at Bottom) */}
      <div className="p-4 border-t border-white/[0.08]">
        <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-widest block mb-2 font-bold">
          QUICK ACTIONS
        </span>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <button
            type="button"
            onClick={() => onQuickAction?.('ghosttrace')}
            className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg border border-white/[0.08] bg-[#0F1518] text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
          >
            <svg className="h-3.5 w-3.5 text-lime" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            </svg>
            <span className="text-[11px] truncate">Run GhostTrace</span>
          </button>

          <button
            type="button"
            onClick={() => onQuickAction?.('logs')}
            className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg border border-white/[0.08] bg-[#0F1518] text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
          >
            <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            </svg>
            <span className="text-[11px] truncate">View Full Logs</span>
          </button>

          <button
            type="button"
            onClick={() => onQuickAction?.('source')}
            className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg border border-white/[0.08] bg-[#0F1518] text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
          >
            <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
            <span className="text-[11px] truncate">Open in Source</span>
          </button>

          <button
            type="button"
            onClick={() => onQuickAction?.('issue')}
            className="flex items-center gap-1.5 px-2.5 py-2 rounded-lg border border-white/[0.08] bg-[#0F1518] text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
          >
            <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <span className="text-[11px] truncate">Create Issue Draft</span>
          </button>
        </div>
      </div>
    </aside>
  )
}
