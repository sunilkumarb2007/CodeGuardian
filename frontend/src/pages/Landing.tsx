import { useState, useRef, useEffect } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { ApiError, startRun, API_BASE_URL } from '../api/client'
import { asRecord, readString } from '../api/json'
import { Footer, LogoMark, Shell } from '../components/Layout'
import { Eyebrow, Reveal } from '../components/primitives'

const DEFAULT_REPOSITORY = ''

const PILLARS = [
  {
    id: '01',
    title: 'Observe the failure',
    body: 'Start from the production symptom: HTTP error, failed request, exception, stack trace, or test failure.',
    visual: <div className="p-8 text-center"><p className="display-md text-signal-pink">HTTP 500</p><p className="mt-4 font-mono text-sm">POST /payments/charge</p><p className="mt-2 font-mono text-xs text-ink-400">req-1042-abc</p></div>,
  },
  {
    id: '02',
    title: 'Reconstruct the failure',
    body: 'GhostTrace follows the failure through the system until the actual component and source location become identifiable.',
    visual: <div className="p-8 text-center space-y-2"><div className="pill border-ink-500 border-2 inline-block font-bold">Gateway</div><div className="text-ink-400 font-bold text-lg">↓</div><div className="pill border-ink-500 border-2 inline-block font-bold">Order Service</div><div className="text-ink-400 font-bold text-lg">↓</div><div className="pill border-ink-500 border-2 inline-block font-bold">Payment Service</div><div className="text-ink-400 font-bold text-lg">↓</div><div className="pill border-signal-pink border-2 text-signal-pink inline-block font-bold">Failure</div></div>,
  },
  {
    id: '03',
    title: 'Investigate with verified context',
    body: 'The investigator receives only relevant repository context, failure evidence, GhostTrace information, and historical memory.',
    visual: <div className="p-8 text-center"><p className="display-sm text-lime">AI investigates.</p><p className="mt-4 text-ink-300">CodeGuardian controls the evidence.</p></div>,
  },
  {
    id: '04',
    title: 'Prove the repair',
    body: 'The candidate patch is applied in isolation and compared against the original behavior using real build, test, and replay evidence.',
    visual: <div className="grid grid-cols-2 gap-px bg-ink-700 border-2 border-ink-700 rounded-lg overflow-hidden m-4"><div className="bg-ink-850 p-6"><p className="eyebrow">ORIGINAL</p><p className="mt-4 display-sm text-signal-pink">HTTP 500</p></div><div className="bg-ink-850 p-6"><p className="eyebrow">PATCHED</p><p className="mt-4 display-sm text-lime">HTTP 200</p></div></div>,
  },
  {
    id: '05',
    title: 'Deliver only after validation',
    body: 'A validated patch becomes a feature branch, commit, and pull request for human review.',
    visual: <div className="p-8 text-center space-y-2"><div className="pill border-lime border-2 text-lime inline-block font-bold">VALIDATED</div><div className="text-ink-400 font-bold text-lg">↓</div><div className="pill border-ink-500 border-2 inline-block font-bold">FEATURE BRANCH</div><div className="text-ink-400 font-bold text-lg">↓</div><div className="pill border-ink-500 border-2 inline-block font-bold">COMMIT</div><div className="text-ink-400 font-bold text-lg">↓</div><div className="pill border-ink-500 border-2 inline-block font-bold">PULL REQUEST</div><div className="text-ink-400 font-bold text-lg">↓</div><div className="pill border-ink-500 border-2 inline-block font-bold">HUMAN MERGE</div></div>,
  },
]

const PIPELINE = [
  { name: 'Repository', purpose: 'Identifies the target GitHub repository.', input: 'Repository URL.', output: 'Repository metadata and isolated workspace.' },
  { name: 'Inspection', purpose: 'Scan source tree.', input: 'Isolated workspace.', output: 'File structure and configuration maps.' },
  { name: 'Architecture', purpose: 'Detect language, framework, build and test system.', input: 'Source tree.', output: 'Build and test strategies.' },
  { name: 'Failure Detection', purpose: 'Normalize the observed failure.', input: 'Raw error details.', output: 'Structured failure fingerprint.' },
  { name: 'Evidence', purpose: 'Collect logs, stack trace, command output and metadata.', input: 'Symptom context.', output: 'Verified execution evidence.' },
  { name: 'GhostTrace', purpose: 'Reconstruct causal execution flow.', input: 'Evidence.', output: 'Identified root cause component.' },
  { name: 'Failure Memory', purpose: 'Search previously validated repairs.', input: 'Failure fingerprint.', output: 'Historical matches.' },
  { name: 'Investigation', purpose: 'Analyze bounded context with the configured investigator.', input: 'Context, GhostTrace, Memory.', output: 'Root cause analysis.' },
  { name: 'Patch', purpose: 'Generate constrained patch candidate.', input: 'Root cause analysis.', output: 'Code change candidate.' },
  { name: 'Compatibility', purpose: 'Check patch language, paths, target files and context.', input: 'Candidate.', output: 'Safety clearance.' },
  { name: 'Replay', purpose: 'Compare original and patched behavior.', input: 'Workspace + patch.', output: 'Replay evidence.' },
  { name: 'Build', purpose: 'Compile/build the patched workspace.', input: 'Patched source.', output: 'Build success or failure.' },
  { name: 'Tests', purpose: 'Run relevant tests.', input: 'Patched source.', output: 'Test results.' },
  { name: 'Validation', purpose: 'Evaluate all deterministic safety gates.', input: 'Build, test, and replay evidence.', output: 'VALIDATED or REJECTED state.' },
  { name: 'Human Approval', purpose: 'Require explicit human approval.', input: 'Validated patch.', output: 'Approval to deliver.' },
  { name: 'Delivery', purpose: 'Create branch, commit, push and PR.', input: 'Approved patch.', output: 'GitHub Pull Request.' },
  { name: 'Memory Update', purpose: 'Persist successful repair knowledge.', input: 'Delivered patch.', output: 'Stored repair memory.' },
]

const PIPELINE_GROUPS = [
  { name: 'Discover', stages: PIPELINE.slice(0, 3) },
  { name: 'Diagnose', stages: PIPELINE.slice(3, 8) },
  { name: 'Repair', stages: PIPELINE.slice(8, 14) },
  { name: 'Deliver', stages: PIPELINE.slice(14, 17) },
]

const FAQ = [
  { q: 'Why is CodeGuardian different from a standard AI code fixer?', a: 'Because the AI is not the authority. CodeGuardian reconstructs the failure, bounds the context, evaluates multiple repair candidates, replays the original behavior, validates the change through deterministic gates, and requires explicit human approval before delivery.' },
  { q: 'What is Failure DNA?', a: 'Failure DNA assigns a stable behavioral fingerprint and causal hash to an incident, allowing CodeGuardian to match current errors against previously validated resolutions.' },
  { q: 'Why does GhostTrace exist?', a: 'A stack trace tells you where execution stopped. GhostTrace reconstructs the causal execution flow from the ingress gateway down to the actual failing component.' },
  { q: 'What happens when AI generates a bad repair?', a: 'The repair is rejected by deterministic safety, compatibility, build, test, and replay gates. Generation alone never makes a repair deliverable.' },
  { q: 'Why generate multiple repair candidates?', a: 'The first syntactically working repair is not always the safest. The Counterfactual Repair Lab compares alternative strategies using concrete test and replay evidence.' },
  { q: 'What is Failure Immunization?', a: 'After a repair is validated, CodeGuardian synthesizes an automated regression guard so the same failure pattern cannot silently recur in future builds.' },
  { q: 'Can CodeGuardian merge changes automatically?', a: 'No. Delivery requires a fully validated repair and explicit human approval.' },
  { q: 'What happens when CodeGuardian cannot prove a failure?', a: 'It stops safely rather than inventing an unverified fix.' },
]

const STACK = [
  { name: 'PostgreSQL', role: 'System of record', desc: 'Persists repository metadata, investigation state, evidence, validation results, delivery history, and verified failure memory.', icon: 'PG' },
  { name: 'Git', role: 'Workspace + patch control', desc: 'Creates isolated workspaces, applies candidate patches safely, verifies diffs, and records exact repository changes.', icon: 'GIT' },
  { name: 'GitHub', role: 'Repository + delivery', desc: 'Fetches repository metadata and optionally receives a validated branch, commit, and pull request after human approval.', icon: 'GH' },
  { name: 'Redis', role: 'Distributed coordination', desc: 'Coordinates active runs through short-lived locks and heartbeat renewal to prevent duplicate orchestration.', icon: 'RDS' },
  { name: 'Docker', role: 'Isolated infrastructure', desc: 'Provides reproducible local infrastructure for the CodeGuardian backend, PostgreSQL, and Redis services.', icon: 'DKR' },
  { name: 'OpenRouter', role: 'Investigation provider', desc: 'Provides the model used to analyze bounded evidence and propose a structured repair. CodeGuardian remains authoritative over validation and execution.', icon: 'AI' },
  { name: 'Python', role: 'Investigation engine', desc: 'Runs orchestration, repository inspection, execution control, validation, memory, and delivery services.', icon: 'PY' },
  { name: 'FastAPI', role: 'Backend API', desc: 'Exposes the run lifecycle, repository processing, approval, validation, system health, and delivery interfaces.', icon: 'API' },
  { name: 'Java + Maven', role: 'Example execution target', desc: 'One supported application stack used by the CodeGuardian reference failure scenario and replay/validation pipeline.', icon: 'JAV' },
  { name: 'React + TypeScript', role: 'Operator workspace', desc: 'Powers the CodeGuardian engineering interface where investigators inspect evidence, agent activity, patches, replay, validation, and delivery.', icon: 'TS' },
]

const SUPPORTED_PLATFORMS = [
  { name: 'Android', icon: '🤖' },
  { name: 'Kotlin', icon: '🟣' },
  { name: 'Python', icon: '🐍' },
  { name: 'Apple / Swift', icon: '🍎' },
  { name: 'Native (C/C++)', icon: '⚙️' },
  { name: 'React Native', icon: '⚛️' },
  { name: 'Dart / Flutter', icon: '🎯' },
  { name: '.NET / C#', icon: '🔷' },
  { name: 'Ruby', icon: '💎' },
  { name: 'Elixir', icon: '💧' },
  { name: 'Rust', icon: '🦀' },
  { name: 'Go', icon: '🔵' },
  { name: 'PHP', icon: '🐘' },
  { name: 'Java / Spring', icon: '☕' },
  { name: 'JavaScript / Node', icon: '🟨' },
  { name: 'TypeScript / React', icon: '🟦' },
  { name: 'PowerShell', icon: '💻' },
  { name: 'Docker / Compose', icon: '🐳' },
]

function ScrollStory() {
  return (
    <div className="relative mx-auto max-w-5xl">
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
    offset: ["start center", "end center"]
  })
  const opacity = useTransform(scrollYProgress, [0, 0.4, 0.6, 1], [0.3, 1, 1, 0.3])
  const scale = useTransform(scrollYProgress, [0, 0.5, 1], [0.95, 1, 0.95])

  return (
    <motion.div ref={ref} style={{ opacity, scale }} className="min-h-[60vh] flex items-center py-10">
      <div className="grid md:grid-cols-2 gap-10 items-center">
        <div>
          <span className="font-mono text-xs uppercase tracking-[0.28em] text-lime mb-4 block">
            Phase {pillar.id}
          </span>
          <h2 className="display-md text-white">{pillar.title}</h2>
          <p className="mt-6 text-lg text-ink-300 leading-relaxed">{pillar.body}</p>
        </div>
        <div className="bg-ink-850 rounded-2xl border-2 border-ink-700 overflow-hidden shadow-2xl">
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
    navigator.clipboard.writeText('code --install-extension codeguardian.vsix')
    setCopiedCli(true)
    setTimeout(() => setCopiedCli(false), 2000)
  }

  return (
    <Shell
      cta={
        <a href="#investigate" className="btn-primary hidden py-3 text-sm sm:inline-flex">
          Investigate a failure →
        </a>
      }
    >
      <main>
        {/* HERO */}
        <section className="relative overflow-hidden px-4 pb-16 pt-16 sm:px-8">
          <div className="grid-bg animate-gridDrift pointer-events-none absolute inset-0 opacity-70" />
          <div className="relative mx-auto max-w-[1400px]">
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              className="mx-auto max-w-4xl text-center"
            >
              <LogoMark className="mx-auto h-24 w-24 animate-logoFloat sm:h-32 sm:w-32" />
              <h1 className="display-xl mt-8">
                From failure to <span className="text-lime">verified repair.</span>
              </h1>
              <p className="mx-auto mt-7 max-w-3xl text-lg text-ink-300">
                CodeGuardian reconstructs production failures, finds their root cause, generates a constrained repair, replays the failure, validates the change, and prepares delivery only after proof.
              </p>
            </motion.div>

            <motion.form
              id="investigate"
              onSubmit={handleSubmit}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.12, ease: [0.16, 1, 0.3, 1] }}
              className="mx-auto mt-12 max-w-3xl"
            >
              <div className="flex flex-col gap-3 rounded-card border-2 border-ink-700 bg-ink-850 p-3 sm:flex-row sm:items-center sm:rounded-pill shadow-2xl">
                <label htmlFor="repo" className="sr-only">
                  GitHub repository URL
                </label>
                <input
                  id="repo"
                  value={repositoryUrl}
                  onChange={(event) => setRepositoryUrl(event.target.value)}
                  placeholder="https://github.com/org/repository"
                  className="w-full bg-transparent px-6 py-4 font-mono text-sm text-white outline-none placeholder:text-ink-500"
                />
                <button
                  type="submit"
                  className="btn-primary shrink-0 px-8"
                  disabled={submitting}
                  aria-busy={submitting}
                >
                  {submitting ? (
                    <>
                      <LogoMark className="h-5 w-5 animate-logoPulse drop-shadow-none" />
                      Analyzing…
                    </>
                  ) : (
                    'INVESTIGATE FAILURE'
                  )}
                </button>
              </div>
              <p className="text-center mt-4 text-sm text-ink-400">
                GitHub repositories, stack traces, and reproducible failures.
              </p>
              {error ? (
                <div className="mt-6 rounded-xl border border-ink-700 bg-ink-900/80 p-6 text-left shadow-2xl backdrop-blur-sm">
                  <h2 className="font-display text-lg font-bold text-signal-pink mb-2">
                    {error.title}
                  </h2>
                  <p className="text-ink-300 text-sm mb-6">
                    {error.message}
                  </p>
                  <button
                    type="button"
                    aria-label="Retry investigation"
                    onClick={(e) => { setError(undefined); handleSubmit(e) }}
                    className="inline-flex items-center justify-center rounded-lg border border-lime bg-ink-800 px-5 py-2.5 text-xs font-bold uppercase tracking-widest text-white transition-colors hover:bg-lime hover:text-ink-900"
                  >
                    RETRY
                  </button>
                  <p className="mt-4 font-mono text-xs text-ink-300 border-t border-ink-800 pt-3">
                    Status &middot; {error.status}
                  </p>
                </div>
              ) : null}
            </motion.form>
          </div>
        </section>

        {/* ENGINEERING STACK */}
        <section className="px-4 pt-16 pb-24 sm:px-8 border-t-2 border-ink-800 bg-ink-900">
          <div className="mx-auto max-w-[1400px]">
            <Reveal>
              <Eyebrow>Engineering stack</Eyebrow>
              <h2 className="display-md mt-4 max-w-3xl">
                Built around the tools that make repair verifiable.
              </h2>
              <p className="mt-6 text-lg text-ink-300 max-w-3xl leading-relaxed">
                CodeGuardian connects repository analysis, execution, AI investigation, validation, and delivery through a controlled engineering pipeline.
              </p>
            </Reveal>
            
            <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {STACK.map((tech, i) => (
                <Reveal key={tech.name} delay={Math.min(i * 0.05, 0.4)}>
                  <div className="group relative flex h-full flex-col bg-ink-850 p-6 border border-ink-700 rounded-xl hover:border-ink-500 hover:-translate-y-1 transition-all shadow-sm">
                    <div 
                      className="mb-6 flex shrink-0 items-center font-mono text-2xl font-bold text-lime"
                      role="img" 
                      aria-label={`${tech.name} icon`}
                    >
                      {tech.icon}
                    </div>
                    <h3 className="font-display text-lg font-bold tracking-tight text-white uppercase">{tech.name}</h3>
                    <p className="mt-1 font-mono text-xs text-lime uppercase tracking-widest">{tech.role}</p>
                    <p className="mt-4 text-sm text-ink-300 leading-relaxed">{tech.desc}</p>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        {/* FIVE-CARD SCROLL STORY */}
        <section id="platform" className="px-4 py-28 sm:px-8 border-y-2 border-ink-800 bg-ink-900/50">
          <div className="mx-auto max-w-[1400px]">
            <h2 className="display-lg text-center mb-24">How CodeGuardian Works</h2>
            <ScrollStory />
          </div>
        </section>

        {/* 17 STAGE PIPELINE */}
        <section id="pipeline" className="px-4 py-24 sm:px-8">
          <div className="mx-auto max-w-[1400px]">
            <Reveal>
              <Eyebrow>The architecture</Eyebrow>
              <h2 className="display-lg mt-4 max-w-3xl">
                Seventeen stages. Every one of them observable.
              </h2>
            </Reveal>
            <div className="mt-16 flex flex-col gap-12">
              {PIPELINE_GROUPS.map((group, groupIndex) => (
                <div key={group.name} className="relative">
                  {groupIndex > 0 && (
                    <div className="absolute -top-8 left-4 h-4 w-px bg-lime/30 sm:left-8" />
                  )}
                  <div className="mb-6 flex items-center gap-4">
                    <h3 className="font-mono text-sm font-bold text-lime uppercase tracking-widest">{group.name}</h3>
                    <div className="h-px flex-1 bg-ink-800" />
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                    {group.stages.map((stage) => {
                      const absoluteIndex = PIPELINE.findIndex(s => s.name === stage.name) + 1;
                      return (
                        <Reveal key={stage.name} delay={Math.min(absoluteIndex * 0.02, 0.3)}>
                          <div 
                            className="group relative h-full bg-ink-850 p-4 border border-ink-700 rounded-lg hover:border-lime hover:bg-ink-800 transition-all cursor-default focus:outline-none focus:ring-2 focus:ring-lime"
                            tabIndex={0}
                            aria-label={`Stage ${absoluteIndex}: ${stage.name}`}
                          >
                            <span className="font-mono text-xs text-ink-400 group-hover:text-lime group-focus:text-lime transition-colors">
                              {String(absoluteIndex).padStart(2, '0')}
                            </span>
                            <p className="mt-2 font-display text-sm font-bold tracking-tight text-white">{stage.name}</p>
                            
                            {/* Tooltip */}
                            <div className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-64 bg-ink-900 border-2 border-ink-700 rounded-lg p-4 opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto group-focus:opacity-100 group-focus:pointer-events-auto transition-opacity z-20 shadow-2xl">
                              <p className="font-bold text-white mb-2">{stage.name}</p>
                              <p className="text-xs text-ink-300 mb-2">{stage.purpose}</p>
                              <div className="space-y-1">
                                <p className="text-xs font-mono text-ink-400"><span className="text-lime">INPUT:</span> {stage.input}</p>
                                <p className="text-xs font-mono text-ink-400"><span className="text-lime">OUTPUT:</span> {stage.output}</p>
                              </div>
                            </div>
                          </div>
                        </Reveal>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* PLATFORM-SPECIFIC ARCHITECTURE & VS CODE EXTENSION (Sentry-style dark card grid) */}
        <section className="px-4 py-28 sm:px-8 border-t-2 border-ink-800 bg-[#06080A]">
          <div className="mx-auto max-w-[1400px] space-y-20">
            {/* Header & Quick Setup Cards */}
            <div className="text-center max-w-4xl mx-auto space-y-4">
              <span className="font-mono text-xs uppercase tracking-[0.28em] text-lime font-bold">
                INTEGRATION ECOSYSTEM
              </span>
              <h2 className="display-lg text-white">Get started with CodeGuardian</h2>
              <p className="text-lg text-ink-300 leading-relaxed">
                Everything you need to reconstruct failures, replay causal traces, and deploy verified fixes directly in your workflow.
              </p>
            </div>

            {/* 2 Setup Cards */}
            <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              <div className="p-8 rounded-2xl border border-white/[0.1] bg-[#0C1114] space-y-6 hover:border-lime/40 transition-all shadow-xl">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-lg bg-lime/10 border border-lime/30 flex items-center justify-center text-lime font-bold text-lg">
                    ⚡
                  </div>
                  <div>
                    <h3 className="font-display font-bold text-white text-lg">CodeGuardian for VS Code</h3>
                    <p className="text-xs text-ink-400">Inspect incidents and replay fixes directly in your editor</p>
                  </div>
                </div>
                <div className="p-3 bg-ide-base rounded-xl border border-ide-divider flex items-center justify-between font-mono text-xs text-zinc-300">
                  <span className="truncate pr-2">code --install-extension codeguardian.vsix</span>
                  <button
                    type="button"
                    onClick={handleCopyCli}
                    className="p-1 text-zinc-400 hover:text-lime transition-colors shrink-0"
                    title="Copy command"
                  >
                    {copiedCli ? '✓' : '📋'}
                  </button>
                </div>
                <div className="flex items-center gap-3 pt-2">
                  <a
                    href={`${API_BASE_URL}/api/extension/download`}
                    target="_blank"
                    rel="noreferrer"
                    className="px-4 py-2 rounded-lg bg-lime text-ink-900 font-bold text-xs hover:bg-lime/90 transition-colors inline-block"
                  >
                    Install Extension (.vsix) →
                  </a>
                </div>
              </div>

              <div className="p-8 rounded-2xl border border-white/[0.1] bg-[#0C1114] space-y-6 hover:border-white/[0.2] transition-all shadow-xl">
                <div className="flex items-center gap-3">
                  <div className="h-9 w-9 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400 font-bold text-lg">
                    🌐
                  </div>
                  <div>
                    <h3 className="font-display font-bold text-white text-lg">Launch Web IDE Workspace</h3>
                    <p className="text-xs text-ink-400">Autonomous 17-stage investigation in your browser</p>
                  </div>
                </div>
                <p className="text-sm text-zinc-400 leading-relaxed">
                  Paste any public or authenticated GitHub repository URL to initiate full GhostTrace causal mapping, Failure DNA generation, and replay proof.
                </p>
                <div className="pt-2">
                  <a
                    href="#investigate"
                    className="px-4 py-2 rounded-lg bg-ink-800 border border-white/[0.12] text-white font-bold text-xs hover:bg-ink-700 transition-colors inline-block"
                  >
                    Start Investigation →
                  </a>
                </div>
              </div>
            </div>

            {/* Platform-Specific Architecture Grid (Matching Sentry reference) */}
            <div className="space-y-8">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-ide-divider pb-6">
                <div>
                  <h3 className="font-display text-2xl font-bold text-white">Supported Engineering Stacks</h3>
                  <p className="text-sm text-ink-400 mt-1">If you write code in it, CodeGuardian can inspect and prove repairs for it.</p>
                </div>
                <div className="font-mono text-xs text-zinc-500 px-3 py-1.5 rounded-lg bg-[#0C1114] border border-ide-divider">
                  18 Environments Supported
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {SUPPORTED_PLATFORMS.map((platform) => (
                  <div
                    key={platform.name}
                    className="flex items-center justify-between p-3.5 rounded-xl border border-ide-divider bg-[#0B0F12] hover:bg-[#12181C] hover:border-lime/40 cursor-pointer transition-all group"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span className="text-base">{platform.icon}</span>
                      <span className="font-mono text-xs font-semibold text-zinc-200 group-hover:text-white truncate">
                        {platform.name}
                      </span>
                    </div>
                    <span className="text-zinc-600 group-hover:text-lime transition-colors text-sm font-bold">
                      ›
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* 4 Bottom Product Pillar Cards (Matching Sentry Docs bottom cards) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4 border-t border-ide-divider">
              <div className="p-5 rounded-xl border border-ide-divider bg-[#0A0E10] space-y-2">
                <span className="font-mono text-[10px] uppercase font-bold text-lime">FAILURE DNA</span>
                <h4 className="font-display text-sm font-bold text-white">Fingerprint Hashing</h4>
                <p className="text-xs text-zinc-400">Stable behavioral identity maps production errors directly to known historical resolutions.</p>
              </div>

              <div className="p-5 rounded-xl border border-ide-divider bg-[#0A0E10] space-y-2">
                <span className="font-mono text-[10px] uppercase font-bold text-purple-400">REPAIR LAB</span>
                <h4 className="font-display text-sm font-bold text-white">Counterfactual Proof</h4>
                <p className="text-xs text-zinc-400">Evaluates Candidates A, B, and C against isolated replay runs and compiler verification gates.</p>
              </div>

              <div className="p-5 rounded-xl border border-ide-divider bg-[#0A0E10] space-y-2">
                <span className="font-mono text-[10px] uppercase font-bold text-amber-400">IMMUNIZATION</span>
                <h4 className="font-display text-sm font-bold text-white">Regression Guards</h4>
                <p className="text-xs text-zinc-400">Synthesizes executable JUnit 5 and Vitest suites to permanently prevent defect recurrence.</p>
              </div>

              <div className="p-5 rounded-xl border border-ide-divider bg-[#0A0E10] space-y-2">
                <span className="font-mono text-[10px] uppercase font-bold text-blue-400">CAPSULES</span>
                <h4 className="font-display text-sm font-bold text-white">Portable Artifacts</h4>
                <p className="text-xs text-zinc-400">Sanitized, path-traversal-safe zip packages containing complete verifiable incident evidence.</p>
              </div>
            </div>
          </div>
        </section>

        {/* FAQ */}
        <section id="faq" className="px-4 py-24 sm:px-8 border-t-2 border-ink-800">
          <div className="mx-auto max-w-[1000px]">
            <Reveal>
              <Eyebrow>Straight Answers</Eyebrow>
              <h2 className="display-lg mt-4">Why CodeGuardian is different.</h2>
            </Reveal>
            <div className="mt-12 divide-y-2 divide-ink-700 border-y-2 border-ink-700">
              {FAQ.map((item) => (
                <details key={item.q} className="group py-7">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-6 outline-none">
                    <span className="font-display text-xl font-bold tracking-tight sm:text-2xl">{item.q}</span>
                    <span className="font-mono text-2xl text-lime transition-transform group-open:rotate-45">
                      +
                    </span>
                  </summary>
                  <p className="mt-4 max-w-3xl text-ink-300 text-lg leading-relaxed">{item.a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        {/* FINAL GREEN SECTION */}
        <section className="bg-lime text-ink-900 py-32 px-4 sm:px-8 border-t-2 border-ink-700">
          <div className="mx-auto max-w-[1400px] text-center">
            <LogoMark className="mx-auto h-20 w-20 mb-8 drop-shadow-none" />
            <h2 className="display-xl uppercase tracking-tighter max-w-4xl mx-auto">
              FROM FAILURE TO VERIFIED REPAIR
            </h2>
            <div className="mt-12 max-w-xl mx-auto text-left space-y-3 font-mono text-sm tracking-wide font-semibold opacity-80 border-l-4 border-ink-900 pl-6">
              <p>Observe the production symptom.</p>
              <p>Trace the causal path.</p>
              <p>Reuse validated memory.</p>
              <p>Investigate with bounded context.</p>
              <p>Generate a constrained repair.</p>
              <p>Replay the failure.</p>
              <p>Validate the behavior.</p>
              <p>Deliver a reviewed change.</p>
            </div>
            <p className="mt-16 text-xl max-w-3xl mx-auto font-medium opacity-90 leading-relaxed">
              CodeGuardian is not an AI that edits your repository blindly.
              It is an evidence-driven repair system that proves a change before
              it reaches your engineering workflow.
            </p>
          </div>
        </section>

      </main>
      <Footer />
    </Shell>
  )
}
