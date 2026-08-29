import { useState, useRef, useEffect } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { ApiError, startRun, API_BASE_URL } from '../api/client'
import { asRecord, readString } from '../api/json'
import { Footer, LogoMark, Shell } from '../components/Layout'

const DEFAULT_REPOSITORY = ''

const PILLARS = [
  {
    id: '01',
    title: 'Observe the production failure',
    body: 'Start from the actual symptom: unhandled HTTP 500, failed transaction, exception stack trace, or test regression in your service.',
    visual: (
      <div className="p-6 font-mono text-xs space-y-3">
        <div className="flex items-center justify-between border-b border-ink-700 pb-2 text-ink-400">
          <span>INGRESS TELEMETRY</span>
          <span className="text-red-400 font-bold">CRASH REPRODUCED</span>
        </div>
        <div className="bg-ink-900 p-4 rounded-xl border border-red-500/30 space-y-2">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-400 font-bold">HTTP 500</span>
            <span className="text-zinc-200">POST /payments/charge</span>
          </div>
          <p className="text-zinc-400 text-[11px]">java.lang.NullPointerException: Cannot invoke &quot;Merchant.getId()&quot;</p>
          <p className="text-zinc-500 text-[10px]">Trace ID: tx_live_9941a · Service: payment-service</p>
        </div>
      </div>
    ),
  },
  {
    id: '02',
    title: 'Reconstruct causal flow (GhostTrace)',
    body: 'A stack trace only shows where execution stopped. GhostTrace traces upstream execution to isolate the true root cause component.',
    visual: (
      <div className="p-6 font-mono text-xs space-y-3">
        <div className="flex items-center justify-between border-b border-ink-700 pb-2 text-ink-400">
          <span>CAUSAL GRAPH RECONSTRUCTION</span>
          <span className="text-lime font-bold">ROOT CAUSE ISOLATED</span>
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-ink-900 border border-ink-700">
            <span className="text-zinc-300">1. API Gateway</span>
            <span className="text-lime font-semibold">200 OK (142ms)</span>
          </div>
          <div className="text-center text-zinc-500 text-xs">↓</div>
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-ink-900 border border-ink-700">
            <span className="text-zinc-300">2. OrderService</span>
            <span className="text-lime font-semibold">200 OK (87ms)</span>
          </div>
          <div className="text-center text-zinc-500 text-xs">↓</div>
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-red-500/10 border border-red-500/40">
            <span className="text-red-400 font-bold">3. PaymentService (Root Cause)</span>
            <span className="text-red-400 font-bold">500 NullPointer</span>
          </div>
        </div>
      </div>
    ),
  },
  {
    id: '03',
    title: 'Investigate with bounded context',
    body: 'Sarvam AI analyzes the exact failing AST, exception fingerprint, and historical repair memory without unrestricted repository edits.',
    visual: (
      <div className="p-6 font-mono text-xs space-y-3">
        <div className="flex items-center justify-between border-b border-ink-700 pb-2 text-ink-400">
          <span>BOUNDED REPAIR SYNTHESIS</span>
          <span className="text-purple-400 font-bold">SARVAM 105B</span>
        </div>
        <div className="bg-ink-900 p-4 rounded-xl border border-purple-500/30 space-y-2 text-zinc-300">
          <p className="text-[11px] text-zinc-400">// Synthesizing minimal defensive guard</p>
          <pre className="text-xs text-lime font-mono">
            {`+ if (merchant == null) {\n+     throw new InvalidMerchantException();\n+ }`}
          </pre>
          <p className="text-[10px] text-zinc-500 pt-1 border-t border-ink-800">Target: PaymentService.java:30 (4 lines bounded)</p>
        </div>
      </div>
    ),
  },
  {
    id: '04',
    title: 'Prove the repair in sandboxed replay',
    body: 'The candidate patch is re-executed in an isolated sandbox against both original failure replay and the full project build and test suite.',
    visual: (
      <div className="p-6 font-mono text-xs space-y-3">
        <div className="flex items-center justify-between border-b border-ink-700 pb-2 text-ink-400">
          <span>DETERMINISTIC VERIFICATION</span>
          <span className="text-lime font-bold">6/6 GATES PASSED</span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-ink-900 p-3 rounded-lg border border-red-500/30 text-center">
            <span className="text-[10px] text-zinc-500 block">ORIGINAL REPLAY</span>
            <span className="text-red-400 font-bold text-sm">HTTP 500</span>
          </div>
          <div className="bg-ink-900 p-3 rounded-lg border border-lime/30 text-center">
            <span className="text-[10px] text-zinc-500 block">PATCHED REPLAY</span>
            <span className="text-lime font-bold text-sm">HTTP 200</span>
          </div>
        </div>
        <div className="bg-ink-900 p-2.5 rounded-lg border border-ink-700 flex items-center justify-between text-[11px]">
          <span className="text-zinc-300">Sandboxed Build (mvnw test)</span>
          <span className="text-lime font-semibold">8/8 Passed (1.4s)</span>
        </div>
      </div>
    ),
  },
  {
    id: '05',
    title: 'Deliver only after human approval',
    body: 'No code is pushed blindly. The engineer reviews the verified diff, confirms the replay proof, and approves creating a GitHub Pull Request.',
    visual: (
      <div className="p-6 font-mono text-xs space-y-3">
        <div className="flex items-center justify-between border-b border-ink-700 pb-2 text-ink-400">
          <span>HUMAN-IN-THE-LOOP GATE</span>
          <span className="text-lime font-bold">PR #4 CREATED</span>
        </div>
        <div className="bg-ink-900 p-4 rounded-xl border border-lime/30 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-white font-bold text-xs">fix/payment-null-check</span>
            <span className="text-lime text-[10px] px-2 py-0.5 rounded bg-lime/10 border border-lime/30 font-bold">DELIVERED</span>
          </div>
          <p className="text-zinc-400 text-[11px]">github.com/org/repo/pull/4</p>
          <p className="text-zinc-500 text-[10px] pt-1 border-t border-ink-800">Memory Immunization: NULL_OBJECT_ACCESS saved</p>
        </div>
      </div>
    ),
  },
]

const PIPELINE = [
  { name: 'Repository', purpose: 'Provisions isolated sandbox and clones target Git repository.', input: 'Repository URL.', output: 'Isolated workspace.' },
  { name: 'Inspection', purpose: 'Scans source tree, directory manifests, and AST indexing.', input: 'Isolated workspace.', output: 'Source file maps.' },
  { name: 'Architecture', purpose: 'Detects language, framework, build orchestrator, and test runner.', input: 'Source tree.', output: 'Microservice topology.' },
  { name: 'Failure Detection', purpose: 'Normalizes observed incident into structured fingerprint.', input: 'Telemetry data.', output: 'Failure fingerprint.' },
  { name: 'Evidence', purpose: 'Extracts formatted exception traces, request bodies, and headers.', input: 'Incident context.', output: 'Verified evidence.' },
  { name: 'GhostTrace', purpose: 'Reconstructs causal execution flow from ingress to failing class.', input: 'Evidence graph.', output: 'Root cause node.' },
  { name: 'Failure Memory', purpose: 'Searches vector memory for previously validated engineering repairs.', input: 'Fingerprint.', output: 'Historical matches.' },
  { name: 'Investigation', purpose: 'Analyzes bounded context with Sarvam 105B AI investigator.', input: 'Context & Trace.', output: 'Root cause diagnosis.' },
  { name: 'Patch', purpose: 'Synthesizes minimal, constrained defensive repair candidate.', input: 'Diagnosis.', output: 'Unified diff candidate.' },
  { name: 'Compatibility', purpose: 'Enforces syntax bounds, file scope, and API safety rules.', input: 'Candidate diff.', output: 'Safety clearance.' },
  { name: 'Replay', purpose: 'Executes original vs patched behavior in sandboxed replay.', input: 'Patched source.', output: 'Behavioral proof.' },
  { name: 'Build', purpose: 'Compiles project in sandbox container with zero error tolerance.', input: 'Patched source.', output: 'Compilation result.' },
  { name: 'Tests', purpose: 'Runs complete regression test suite against patched workspace.', input: 'Patched source.', output: 'Test suite output.' },
  { name: 'Validation', purpose: 'Evaluates all 6 deterministic safety verification gates.', input: 'Verification proof.', output: 'VALIDATED gate state.' },
  { name: 'Human Approval', purpose: 'Requires explicit human operator approval before delivery.', input: 'Validated patch.', output: 'Delivery authorization.' },
  { name: 'Delivery', purpose: 'Creates Git feature branch, commit, and published GitHub PR.', input: 'Approved patch.', output: 'GitHub Pull Request.' },
  { name: 'Memory Update', purpose: 'Persists proven repair knowledge for permanent immunization.', input: 'Delivered patch.', output: 'Durable memory record.' },
]

const PIPELINE_GROUPS = [
  { name: 'Discover', stages: PIPELINE.slice(0, 3) },
  { name: 'Diagnose', stages: PIPELINE.slice(3, 8) },
  { name: 'Repair & Verify', stages: PIPELINE.slice(8, 14) },
  { name: 'Deliver & Immunize', stages: PIPELINE.slice(14, 17) },
]

const STACK_LANGUAGES = [
  { name: 'Java', badge: 'JAVA', desc: 'JDK 8–21 · Spring Boot · Maven · Gradle' },
  { name: 'Python', badge: 'PY', desc: 'Python 3.10+ · FastAPI · Django · Pytest' },
  { name: 'TypeScript', badge: 'TS', desc: 'Node.js · React · Next.js · Vitest · Jest' },
  { name: 'Go', badge: 'GO', desc: 'Go 1.20+ · Gin · Echo · Standard testing' },
  { name: 'Rust', badge: 'RS', desc: 'Cargo · Tokio · Actix · Rust test suites' },
  { name: 'C / C++', badge: 'C++', desc: 'GCC · Clang · CMake · GoogleTest' },
  { name: 'Kotlin', badge: 'KT', desc: 'Kotlin JVM · Android · Ktor · JUnit 5' },
  { name: 'Swift', badge: 'SW', desc: 'Swift 5.9+ · Vapor · XCTest · SwiftPM' },
]

const STACK_FRAMEWORKS = [
  { name: 'Spring Boot', tag: 'Microservices', desc: 'Dependency injection, JPA, actuator telemetry' },
  { name: 'React 19 & Next.js', tag: 'Web Frontend', desc: 'Full-stack SSR, API routes, component trees' },
  { name: 'FastAPI', tag: 'Python Backend', desc: 'Async execution, Pydantic schemas, OpenAPI' },
  { name: 'Docker & Compose', tag: 'Containers', desc: 'Sandboxed compilation, isolated runtimes' },
]

const CAPABILITIES = [
  {
    tag: 'FAILURE DNA',
    color: 'text-lime',
    title: 'Fingerprint Hashing',
    desc: 'Assigns stable behavioral identity to production errors, mapping recurring incidents directly to known historical resolutions.',
  },
  {
    tag: 'GHOSTTRACE',
    color: 'text-blue-400',
    title: 'Causal Flow Reconstruction',
    desc: 'Traces execution from outer API gateway through microservices down to the exact failing line, separating symptoms from root cause.',
  },
  {
    tag: 'REPAIR LAB',
    color: 'text-purple-400',
    title: 'Counterfactual Synthesis',
    desc: 'Synthesizes minimal defensive candidate diffs constrained strictly to the target AST context without modifying unrelated files.',
  },
  {
    tag: 'GHOST REPLAY',
    color: 'text-lime',
    title: 'Deterministic Proof',
    desc: 'Re-executes original failure telemetry against both baseline and patched workspaces to verify error resolution (HTTP 500 → 200).',
  },
  {
    tag: 'VALIDATION',
    color: 'text-amber-400',
    title: '6/6 Safety Gate Matrix',
    desc: 'Enforces strict clearance across Path Safety, Patch Context, Language Compatibility, Sandboxed Build, and Regression Suites.',
  },
  {
    tag: 'DELIVERY & MEMORY',
    color: 'text-lime',
    title: 'Human Sign-off & Immunization',
    desc: 'Publishes reviewed GitHub Pull Requests and stores proven solutions into durable PostgreSQL memory to prevent recurrence.',
  },
]

const FAQ = [
  { q: 'Why is CodeGuardian different from standard AI coding assistants?', a: 'Standard AI assistants guess code changes in the dark without execution feedback. CodeGuardian clones the repository into an isolated sandbox, traces causal execution (GhostTrace), bounds the context, proves the fix via sandboxed replay and compilation, requires explicit human sign-off, and opens a verified GitHub PR.' },
  { q: 'What is the difference between a symptom and a root cause?', a: 'A crash symptom is where the execution halted (such as an API Gateway returning HTTP 500 or an uncaught NullPointerException). The root cause is the specific upstream component or state that triggered the defect. GhostTrace reconstructs the causal chain to isolate the true root cause.' },
  { q: 'How does CodeGuardian prove a repair before opening a Pull Request?', a: 'CodeGuardian executes the failing request in an isolated container against the patched code (verifying behavior changes from HTTP 500 to 200), runs project compilation (e.g., Maven/Gradle), and runs the entire regression test suite (6/6 deterministic safety gates).' },
  { q: 'Can CodeGuardian push code to production automatically?', a: 'No. CodeGuardian enforces a strict Human-in-the-Loop approval gate (Stage 15). The engineer inspects the verified diff, replay outcome, and test logs in the Web IDE before approving creation of the feature branch and GitHub Pull Request.' },
  { q: 'What happens if a repository has no reproducible failure?', a: 'CodeGuardian completes baseline analysis, reports NO_FAILURE_FOUND, changes 0 files, and creates 0 Pull Requests. It never invents fake defects or unnecessary edits.' },
  { q: 'What is Failure Immunization?', a: 'After a verified patch is delivered, CodeGuardian indexes the incident fingerprint, root cause service, and proven repair into durable PostgreSQL memory. Future matching incidents are instantly diagnosed and immunized.' },
]

function ScrollStory() {
  return (
    <div className="relative mx-auto max-w-5xl space-y-12">
      {PILLARS.map((pillar) => (
        <ScrollCard key={pillar.id} pillar={pillar} />
      ))}
    </div>
  )
}

function ScrollCard({ pillar }: { pillar: typeof PILLARS[0] }) {
  const ref = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ['start center', 'end center'],
  })
  const opacity = useTransform(scrollYProgress, [0, 0.3, 0.7, 1], [0.4, 1, 1, 0.4])
  const scale = useTransform(scrollYProgress, [0, 0.5, 1], [0.97, 1, 0.97])

  return (
    <motion.div ref={ref} style={{ opacity, scale }} className="py-6">
      <div className="grid md:grid-cols-2 gap-8 items-center bg-[#0C1114] p-8 rounded-2xl border border-white/[0.08] shadow-xl">
        <div>
          <span className="font-mono text-xs uppercase tracking-[0.24em] text-lime mb-3 block font-bold">
            PHASE {pillar.id}
          </span>
          <h2 className="font-display text-2xl font-bold text-white tracking-tight">{pillar.title}</h2>
          <p className="mt-4 text-sm text-zinc-400 leading-relaxed">{pillar.body}</p>
        </div>
        <div className="bg-ide-base rounded-xl border border-ide-divider overflow-hidden shadow-inner">
          {pillar.visual}
        </div>
      </div>
    </motion.div>
  )
}

interface ErrorState {
  title: string
  message: string
  status: string
}

export default function Landing() {
  const navigate = useNavigate()
  const [repositoryUrl, setRepositoryUrl] = useState(DEFAULT_REPOSITORY)
  const [failureInput, setFailureInput] = useState<Record<string, unknown> | undefined>(undefined)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<ErrorState | undefined>(undefined)
  const [copiedCli, setCopiedCli] = useState(false)

  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search)
      const repo = params.get('repo')
      if (repo) {
        setRepositoryUrl(repo)
      }
      const requestId = params.get('requestId')
      const errorCode = params.get('errorCode')
      const failureType = params.get('failureType') || errorCode
      const message = params.get('message')
      const service = params.get('service')
      const source = params.get('source') || 'RUNTIME'
      const file = params.get('file')
      const line = params.get('line')
      const timestamp = params.get('timestamp') || new Date().toISOString()
      const exception = params.get('exception')

      if (failureType || message || file) {
        setFailureInput({
          failure_type: failureType || 'NULL_OBJECT_ACCESS',
          message: message || `Unhandled runtime error in ${file || service || 'application'}`,
          source: source || 'RUNTIME',
          timestamp: timestamp,
          request_id: requestId || undefined,
          service: service || undefined,
          source_file: file || undefined,
          source_line: line ? parseInt(line, 10) : undefined,
          exception: exception || undefined,
          stack_trace: exception ? `${exception}: Null pointer dereference at ${file || 'service'}:${line || 1}` : undefined,
        })
      }
    } catch {
      // Ignore URL parsing errors
    }
  }, [])

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    const trimmedUrl = repositoryUrl.trim()
    if (!trimmedUrl) {
      setError({
        title: 'Repository URL required',
        message: 'Please enter a GitHub repository URL to begin investigation.',
        status: 'Validation · 422',
      })
      return
    }

    setSubmitting(true)
    setError(undefined)
    try {
      const payload = await startRun(trimmedUrl, failureInput)
      const runId = readString(asRecord(payload), 'run_id', 'runId', 'id')
      if (!runId) {
        setError({
          title: 'Investigation unavailable',
          message: 'The backend accepted the request but did not return a valid run ID.',
          status: 'Invalid response',
        })
        return
      }
      navigate(`/runs/${encodeURIComponent(runId)}`)
    } catch (submitError) {
      if (submitError instanceof ApiError) {
        setError({
          title: submitError.title,
          message: submitError.message,
          status: submitError.statusText,
        })
      } else if (submitError instanceof Error) {
        setError({
          title: 'Investigation error',
          message: submitError.message,
          status: 'Client error',
        })
      } else {
        setError({
          title: 'Investigation error',
          message: 'An unexpected error occurred.',
          status: 'Unknown error',
        })
      }
    } finally {
      setSubmitting(false)
    }
  }

  const handleCopyCli = () => {
    navigator.clipboard.writeText('code --install-extension vscode-extension/codeguardian-vscode-1.0.0.vsix')
    setCopiedCli(true)
    setTimeout(() => setCopiedCli(false), 2000)
  }

  return (
    <Shell
      cta={
        <a href="#investigate" className="btn-primary hidden py-2.5 text-xs font-bold sm:inline-flex">
          Investigate a failure →
        </a>
      }
    >
      <main className="bg-ide-base text-white font-sans selection:bg-lime selection:text-ink-900">
        {/* 1. HERO SECTION */}
        <section className="relative overflow-hidden px-4 pt-16 pb-20 sm:px-8 border-b border-ide-divider">
          <div className="grid-bg animate-gridDrift pointer-events-none absolute inset-0 opacity-40" />
          
          <div className="relative mx-auto max-w-5xl text-center space-y-6">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-lime/30 bg-lime/10 text-lime font-mono text-xs font-bold tracking-wider uppercase">
              <span className="h-2 w-2 rounded-full bg-lime animate-pulse" />
              Evidence-Driven Autonomous Software Repair
            </div>

            <h1 className="font-display text-4xl sm:text-6xl font-bold tracking-tight text-white max-w-4xl mx-auto leading-[1.1]">
              Find the failure. <br />
              <span className="text-lime">Prove the fix.</span> Ship it safely.
            </h1>

            <p className="mx-auto max-w-2xl text-sm sm:text-base text-zinc-400 leading-relaxed">
              CodeGuardian connects repository ingestion, runtime evidence, Sarvam AI investigation, deterministic sandboxed replay, validation, and GitHub delivery into one controlled engineering workflow.
            </p>

            {/* Ingestion Form */}
            <form
              id="investigate"
              onSubmit={handleSubmit}
              className="mx-auto mt-8 max-w-2xl"
            >
              <div className="flex flex-col sm:flex-row gap-2 rounded-xl border border-white/[0.12] bg-[#0C1114] p-2 shadow-2xl focus-within:border-lime/60 transition-colors">
                <label htmlFor="repo" className="sr-only">
                  GitHub repository URL
                </label>
                <input
                  id="repo"
                  value={repositoryUrl}
                  onChange={(event) => setRepositoryUrl(event.target.value)}
                  placeholder="https://github.com/org/repository"
                  className="w-full bg-transparent px-4 py-3 font-mono text-xs sm:text-sm text-white outline-none placeholder:text-zinc-500"
                />
                <button
                  type="submit"
                  className="btn-primary shrink-0 px-6 py-3 text-xs font-bold uppercase tracking-wider"
                  disabled={submitting}
                  aria-busy={submitting}
                >
                  {submitting ? (
                    <span className="flex items-center gap-2">
                      <LogoMark className="h-4 w-4 animate-logoPulse drop-shadow-none" />
                      Analyzing…
                    </span>
                  ) : (
                    'INVESTIGATE FAILURE →'
                  )}
                </button>
              </div>

              <div className="flex flex-wrap items-center justify-center gap-4 mt-3 text-xs font-mono text-zinc-500">
                <span>✓ Isolated Git Sandbox</span>
                <span>·</span>
                <span>✓ GhostTrace Causal Engine</span>
                <span>·</span>
                <span>✓ 6/6 Deterministic Gates</span>
              </div>

              {error ? (
                <div className="mt-4 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-left font-mono text-xs">
                  <p className="text-red-400 font-bold mb-1">{error.title}</p>
                  <p className="text-zinc-300 mb-3">{error.message}</p>
                  <button
                    type="button"
                    onClick={(e) => { setError(undefined); handleSubmit(e) }}
                    className="px-3 py-1.5 rounded bg-red-500/20 border border-red-500/40 text-red-300 font-bold hover:bg-red-500/30"
                  >
                    Retry Submission
                  </button>
                </div>
              ) : null}
            </form>

            {/* Real-world Interactive Hero Visual Artifact */}
            <div className="pt-8 max-w-4xl mx-auto text-left">
              <div className="rounded-xl border border-ide-divider bg-[#0A0E10] shadow-2xl overflow-hidden font-mono text-xs">
                {/* Window Top Bar */}
                <div className="px-4 py-2.5 bg-[#0D1215] border-b border-ide-divider flex items-center justify-between text-[11px] text-zinc-400">
                  <div className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-full bg-red-500/80" />
                    <span className="h-2.5 w-2.5 rounded-full bg-amber-500/80" />
                    <span className="h-2.5 w-2.5 rounded-full bg-lime/80" />
                    <span className="ml-2 text-zinc-300 font-semibold">JavaAPICheck / payment-service</span>
                  </div>
                  <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-400 font-bold border border-red-500/30">
                    HTTP 500 CRASH REPRODUCED
                  </span>
                </div>

                {/* Artifact Content Body */}
                <div className="p-5 space-y-4">
                  {/* Causal Flow Chain */}
                  <div>
                    <span className="text-[10px] text-zinc-500 uppercase tracking-widest block mb-2 font-bold">
                      GhostTrace Causal Flow (Ingress → Root Cause)
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      <div className="p-2.5 rounded-lg bg-ink-900 border border-ide-divider flex items-center justify-between">
                        <span className="text-zinc-300">1. API Gateway</span>
                        <span className="text-lime font-bold text-[11px]">200 OK</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-ink-900 border border-ide-divider flex items-center justify-between">
                        <span className="text-zinc-300">2. OrderService</span>
                        <span className="text-lime font-bold text-[11px]">200 OK</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/40 flex items-center justify-between">
                        <span className="text-red-400 font-bold">3. PaymentService</span>
                        <span className="text-red-400 font-bold text-[11px]">500 ROOT</span>
                      </div>
                    </div>
                  </div>

                  {/* Verification Proof Matrix */}
                  <div className="pt-3 border-t border-ide-divider grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px]">
                    <div className="p-2 rounded bg-ink-900 border border-ide-divider">
                      <span className="text-zinc-500 block text-[9px] uppercase">Patch Scope</span>
                      <span className="text-zinc-200 font-semibold">1 file, 4 lines</span>
                    </div>
                    <div className="p-2 rounded bg-ink-900 border border-ide-divider">
                      <span className="text-zinc-500 block text-[9px] uppercase">Replay Proof</span>
                      <span className="text-lime font-semibold">500 → 200 OK</span>
                    </div>
                    <div className="p-2 rounded bg-ink-900 border border-ide-divider">
                      <span className="text-zinc-500 block text-[9px] uppercase">Sandboxed Build</span>
                      <span className="text-lime font-semibold">mvnw: SUCCESS</span>
                    </div>
                    <div className="p-2 rounded bg-ink-900 border border-ide-divider">
                      <span className="text-zinc-500 block text-[9px] uppercase">Delivery</span>
                      <span className="text-lime font-semibold">PR #4 Ready</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 2. TWO WAYS TO USE CODEGUARDIAN */}
        <section className="px-4 py-20 sm:px-8 border-b border-ide-divider bg-[#070A0C]">
          <div className="mx-auto max-w-5xl space-y-12">
            <div className="text-center space-y-3">
              <span className="font-mono text-xs uppercase tracking-[0.24em] text-lime font-bold">
                INTEGRATION OPTIONS
              </span>
              <h2 className="font-display text-3xl font-bold text-white">Two ways to use CodeGuardian</h2>
              <p className="text-sm text-zinc-400 max-w-xl mx-auto">
                Investigate failures directly inside your code editor or explore full 17-stage causal traces in the Web IDE.
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              {/* Card 1: VS Code */}
              <div className="p-7 rounded-2xl border border-white/[0.1] bg-[#0C1114] space-y-5 hover:border-lime/40 transition-all shadow-xl flex flex-col justify-between">
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center font-bold text-blue-400 font-mono text-sm">
                      VS
                    </div>
                    <div>
                      <h3 className="font-display font-bold text-white text-lg">CodeGuardian for VS Code</h3>
                      <p className="text-xs text-zinc-400">Context-aware failure investigation inside your editor</p>
                    </div>
                  </div>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    Highlight any failing method or stack trace, right-click, and trigger bounded investigation. View live incidents and sealed failure capsules directly in the activity bar.
                  </p>
                  <div className="p-3 bg-ide-base rounded-xl border border-ide-divider flex items-center justify-between font-mono text-xs text-zinc-300">
                    <span className="truncate pr-2">code --install-extension vscode-extension/codeguardian-vscode-1.0.0.vsix</span>
                    <button
                      type="button"
                      onClick={handleCopyCli}
                      className="p-1 text-zinc-400 hover:text-lime transition-colors shrink-0"
                      title="Copy command"
                    >
                      {copiedCli ? '✓' : '📋'}
                    </button>
                  </div>
                </div>
                <div className="pt-2">
                  <a
                    href={`${API_BASE_URL}/api/extension/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="px-4 py-2.5 rounded-lg bg-lime text-ink-900 font-bold text-xs hover:bg-lime/90 transition-colors inline-block font-mono"
                  >
                    Download Extension (.vsix) →
                  </a>
                </div>
              </div>

              {/* Card 2: Web Workspace */}
              <div className="p-7 rounded-2xl border border-white/[0.1] bg-[#0C1114] space-y-5 hover:border-white/[0.2] transition-all shadow-xl flex flex-col justify-between">
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-lime/10 border border-lime/30 flex items-center justify-center font-bold text-lime font-mono text-sm">
                      IDE
                    </div>
                    <div>
                      <h3 className="font-display font-bold text-white text-lg">Autonomous Web Workspace</h3>
                      <p className="text-xs text-zinc-400">Full 17-stage causal investigation console</p>
                    </div>
                  </div>
                  <p className="text-xs text-zinc-400 leading-relaxed">
                    Paste any public or authenticated GitHub repository URL to initiate full GhostTrace causal mapping, Failure DNA generation, and replay proof in an isolated container.
                  </p>
                  <div className="p-3 bg-ide-base rounded-xl border border-ide-divider font-mono text-xs text-zinc-400 flex items-center justify-between">
                    <span>Target: Public / Private GitHub Repos</span>
                    <span className="text-lime font-bold">17 Stages</span>
                  </div>
                </div>
                <div className="pt-2">
                  <a
                    href="#investigate"
                    className="px-4 py-2.5 rounded-lg bg-ink-800 border border-white/[0.12] text-white font-bold text-xs hover:bg-ink-700 transition-colors inline-block font-mono"
                  >
                    Launch Web Investigation →
                  </a>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* 3. HOW CODEGUARDIAN WORKS (5-Step Sequence) */}
        <section id="platform" className="px-4 py-24 sm:px-8 border-b border-ide-divider bg-[#06080A]">
          <div className="mx-auto max-w-5xl space-y-12">
            <div className="text-center space-y-3">
              <span className="font-mono text-xs uppercase tracking-[0.24em] text-lime font-bold">
                LIFECYCLE FLOW
              </span>
              <h2 className="font-display text-3xl font-bold text-white">How CodeGuardian Works</h2>
              <p className="text-sm text-zinc-400 max-w-xl mx-auto">
                An evidence-driven sequence from observable runtime failure to verified, delivered Pull Request.
              </p>
            </div>
            <ScrollStory />
          </div>
        </section>

        {/* 4. THE SIGNATURE STATEMENT CENTERPIECE (Integrated Visual Centerpiece, No discontinuous bands) */}
        <section className="px-4 py-20 sm:px-8 border-b border-ide-divider bg-[#0B0F12] relative overflow-hidden">
          <div className="mx-auto max-w-4xl text-center space-y-6">
            <LogoMark className="h-12 w-12 mx-auto drop-shadow-none" />
            <h2 className="font-display text-3xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
              Symptom is where you look. <br />
              <span className="text-lime">Root cause is where it broke.</span>
            </h2>
            <p className="text-sm sm:text-base text-zinc-400 max-w-2xl mx-auto leading-relaxed">
              CodeGuardian follows the evidence from the observed production crash down to the exact code modification that actually needs to be made.
            </p>
          </div>
        </section>

        {/* 5. SUPPORTED ENGINEERING STACKS */}
        <section className="px-4 py-24 sm:px-8 border-b border-ide-divider bg-[#070A0C]">
          <div className="mx-auto max-w-5xl space-y-12">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-ide-divider pb-6">
              <div>
                <span className="font-mono text-xs uppercase tracking-[0.24em] text-lime font-bold">
                  MULTI-LANGUAGE REPAIR
                </span>
                <h2 className="font-display text-2xl font-bold text-white mt-1">Supported Engineering Stacks</h2>
              </div>
              <p className="text-xs text-zinc-400 font-mono">
                Isolated compilation, test execution, and AST analysis
              </p>
            </div>

            {/* Languages Grid */}
            <div className="space-y-4">
              <span className="font-mono text-xs uppercase text-zinc-500 font-bold block">
                Languages &amp; Core Runtimes
              </span>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {STACK_LANGUAGES.map((lang) => (
                  <div
                    key={lang.name}
                    className="p-3.5 rounded-xl border border-ide-divider bg-[#0A0E10] hover:border-lime/40 transition-colors space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-display font-bold text-sm text-white">{lang.name}</span>
                      <span className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-[10px] font-mono text-lime font-bold">
                        {lang.badge}
                      </span>
                    </div>
                    <p className="text-[11px] text-zinc-400 font-mono">{lang.desc}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Frameworks & Infrastructure */}
            <div className="space-y-4 pt-4">
              <span className="font-mono text-xs uppercase text-zinc-500 font-bold block">
                Frameworks &amp; Sandboxed Infrastructure
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
                {STACK_FRAMEWORKS.map((fw) => (
                  <div
                    key={fw.name}
                    className="p-3.5 rounded-xl border border-ide-divider bg-[#0A0E10] hover:border-white/20 transition-colors space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-display font-bold text-sm text-white">{fw.name}</span>
                      <span className="text-[10px] font-mono text-zinc-400">{fw.tag}</span>
                    </div>
                    <p className="text-[11px] text-zinc-400">{fw.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* 6. ENGINEERING ARCHITECTURE & INTEGRATION STRIP (Accurate Sarvam 105B & real PostgreSQL architecture) */}
        <section className="px-4 py-24 sm:px-8 border-b border-ide-divider bg-[#06080A]">
          <div className="mx-auto max-w-5xl space-y-12">
            <div className="text-center space-y-3">
              <span className="font-mono text-xs uppercase tracking-[0.24em] text-lime font-bold">
                SYSTEM ARCHITECTURE
              </span>
              <h2 className="font-display text-3xl font-bold text-white">Built for verifiable enterprise repair</h2>
              <p className="text-sm text-zinc-400 max-w-xl mx-auto">
                No hallucinated code. Every subsystem is strictly coordinated between isolated execution sandboxes and durable state.
              </p>
            </div>

            {/* Architecture Strip */}
            <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 text-center font-mono text-xs">
              <div className="p-4 rounded-xl border border-ide-divider bg-[#0A0E10] space-y-2">
                <span className="text-lime font-bold block text-sm">GITHUB</span>
                <p className="text-[11px] text-zinc-400">Target Ingestion &amp; Repository AST Clone</p>
              </div>
              <div className="hidden sm:flex items-center justify-center text-zinc-600 text-lg">→</div>
              <div className="p-4 rounded-xl border border-lime/40 bg-lime/5 space-y-2">
                <span className="text-lime font-bold block text-sm">ORCHESTRATOR</span>
                <p className="text-[11px] text-zinc-300">17-Stage State Machine &amp; Sandbox</p>
              </div>
              <div className="hidden sm:flex items-center justify-center text-zinc-600 text-lg">→</div>
              <div className="p-4 rounded-xl border border-purple-500/40 bg-purple-500/5 space-y-2">
                <span className="text-purple-400 font-bold block text-sm">SARVAM AI</span>
                <p className="text-[11px] text-zinc-300">105B Bounded Repair Synthesis</p>
              </div>
            </div>

            {/* Supporting Core Components */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
              <div className="p-5 rounded-xl border border-ide-divider bg-[#0A0E10] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-display font-bold text-white text-sm">PostgreSQL 17</span>
                  <span className="text-[10px] font-mono text-lime font-bold px-2 py-0.5 rounded bg-lime/10 border border-lime/30">
                    SYSTEM OF RECORD
                  </span>
                </div>
                <p className="text-xs text-zinc-400">
                  Durable persistence for incident telemetry, runs, evidence events, patches, validation results, and failure memory.
                </p>
              </div>

              <div className="p-5 rounded-xl border border-ide-divider bg-[#0A0E10] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-display font-bold text-white text-sm">Sarvam 105B Engine</span>
                  <span className="text-[10px] font-mono text-purple-400 font-bold px-2 py-0.5 rounded bg-purple-500/10 border border-purple-500/30">
                    REPAIR INTELLIGENCE
                  </span>
                </div>
                <p className="text-xs text-zinc-400">
                  High-accuracy code reasoning engine synthesizing minimal, defensive AST modifications without hallucinations.
                </p>
              </div>

              <div className="p-5 rounded-xl border border-ide-divider bg-[#0A0E10] space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-display font-bold text-white text-sm">GitHub REST Delivery</span>
                  <span className="text-[10px] font-mono text-blue-400 font-bold px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/30">
                    DELIVERY ENGINE
                  </span>
                </div>
                <p className="text-xs text-zinc-400">
                  Creates dedicated feature branches, commits verified diffs, and opens structured Pull Requests after human approval.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 7. CORE ENGINEERING CAPABILITIES (6 Cards) */}
        <section className="px-4 py-24 sm:px-8 border-b border-ide-divider bg-[#070A0C]">
          <div className="mx-auto max-w-5xl space-y-12">
            <div className="text-center space-y-3">
              <span className="font-mono text-xs uppercase tracking-[0.24em] text-lime font-bold">
                ENGINEERING PILLARS
              </span>
              <h2 className="font-display text-3xl font-bold text-white">Six core capabilities</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {CAPABILITIES.map((cap) => (
                <div
                  key={cap.title}
                  className="p-6 rounded-xl border border-ide-divider bg-[#0A0E10] space-y-3 hover:border-white/20 transition-all shadow-sm flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <span className={`font-mono text-[10px] uppercase font-bold ${cap.color}`}>
                      {cap.tag}
                    </span>
                    <h3 className="font-display text-base font-bold text-white">{cap.title}</h3>
                    <p className="text-xs text-zinc-400 leading-relaxed">{cap.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 8. 17-STAGE OBSERVABLE PIPELINE OVERVIEW */}
        <section id="pipeline" className="px-4 py-24 sm:px-8 border-b border-ide-divider bg-[#06080A]">
          <div className="mx-auto max-w-5xl space-y-12">
            <div className="text-center space-y-3">
              <span className="font-mono text-xs uppercase tracking-[0.24em] text-lime font-bold">
                EXECUTION PIPELINE
              </span>
              <h2 className="font-display text-3xl font-bold text-white">
                Seventeen stages. Every one of them observable.
              </h2>
              <p className="text-sm text-zinc-400 max-w-xl mx-auto">
                Explore the deterministic stages executed for every investigated incident.
              </p>
            </div>

            <div className="space-y-8">
              {PIPELINE_GROUPS.map((group, groupIndex) => (
                <div key={group.name} className="space-y-3">
                  <div className="flex items-center gap-3 border-b border-ide-divider pb-2">
                    <span className="font-mono text-xs font-bold text-lime uppercase tracking-widest">
                      {groupIndex + 1}. {group.name}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5">
                    {group.stages.map((stage) => {
                      const absoluteIndex = PIPELINE.findIndex((s) => s.name === stage.name) + 1
                      return (
                        <div
                          key={stage.name}
                          className="p-3 rounded-lg border border-ide-divider bg-[#0A0E10] hover:border-lime/40 transition-colors"
                        >
                          <span className="font-mono text-[10px] text-zinc-500 block font-bold">
                            {String(absoluteIndex).padStart(2, '0')}
                          </span>
                          <span className="font-display font-bold text-xs text-white block mt-1">
                            {stage.name}
                          </span>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 9. FREQUENTLY ASKED QUESTIONS */}
        <section id="faq" className="px-4 py-24 sm:px-8 border-b border-ide-divider bg-[#070A0C]">
          <div className="mx-auto max-w-3xl space-y-10">
            <div className="text-center space-y-3">
              <span className="font-mono text-xs uppercase tracking-[0.24em] text-lime font-bold">
                FAQ &amp; PRINCIPLES
              </span>
              <h2 className="font-display text-3xl font-bold text-white">Why CodeGuardian is different</h2>
            </div>

            <div className="divide-y divide-ide-divider border-y border-ide-divider">
              {FAQ.map((item) => (
                <details key={item.q} className="group py-6">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-4 outline-none">
                    <span className="font-display text-base sm:text-lg font-bold text-white">{item.q}</span>
                    <span className="font-mono text-xl text-lime transition-transform group-open:rotate-45">
                      +
                    </span>
                  </summary>
                  <p className="mt-3 text-sm text-zinc-400 leading-relaxed">{item.a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        {/* 10. FINAL CALL TO ACTION (Clean, Dark, High-Signal) */}
        <section className="px-4 py-24 sm:px-8 bg-ide-base text-center">
          <div className="mx-auto max-w-3xl space-y-6">
            <LogoMark className="h-12 w-12 mx-auto drop-shadow-none" />
            <h2 className="font-display text-3xl sm:text-4xl font-bold text-white tracking-tight">
              Have a production failure?
            </h2>
            <p className="text-sm text-zinc-400 max-w-lg mx-auto">
              Give CodeGuardian the repository. Reconstruct causal flow, prove the patch in sandboxed replay, and deliver a verified Pull Request.
            </p>
            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
              <a
                href="#investigate"
                className="btn-primary px-8 py-3 text-xs font-bold uppercase tracking-wider w-full sm:w-auto"
              >
                Investigate a Failure →
              </a>
              <a
                href="https://github.com/sunilkumarb2007/CodeGuardian"
                target="_blank"
                rel="noreferrer"
                className="px-6 py-3 rounded-lg border border-white/[0.12] bg-[#0C1114] text-white font-bold text-xs hover:bg-[#141A1E] transition-colors font-mono w-full sm:w-auto"
              >
                View on GitHub
              </a>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </Shell>
  )
}
