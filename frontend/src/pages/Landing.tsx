import { useState, useRef } from 'react'
import { motion, useScroll, useTransform } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { ApiError, startRun } from '../api/client'
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
  { q: 'WHY DOES CODEGUARDIAN NEED GHOSTTRACE?', a: 'Because the visible error is often only the symptom. GhostTrace reconstructs the causal path so investigation begins at the component that actually failed.' },
  { q: 'WHAT DOES THE AI ACTUALLY DO?', a: 'The investigator interprets verified evidence, identifies the likely root cause, and proposes a constrained patch. It does not directly execute code or declare the repair valid.' },
  { q: 'HOW DOES CODEGUARDIAN STOP UNSAFE AI PATCHES?', a: 'Every patch is checked for file scope, language compatibility, path safety, patch context, build behavior, tests, and replay results before delivery.' },
  { q: 'WHY IS FAILURE MEMORY DIFFERENT FROM A NORMAL AI CHAT HISTORY?', a: 'Failure Memory stores validated engineering repairs and their evidence, allowing future investigations to reference previously proven solutions.' },
  { q: 'WHAT HAPPENS IF THE PATCH FAILS?', a: 'The patch is rejected, the validation evidence becomes repair context, and the investigator can produce another candidate within the bounded repair loop.' },
  { q: 'CAN CODEGUARDIAN MERGE THE PR BY ITSELF?', a: 'No. CodeGuardian can prepare and deliver a validated feature branch and PR, but human review remains the final merge boundary.' },
  { q: 'WHY NOT LET THE AI DIRECTLY EDIT THE REPOSITORY?', a: 'Because generation and verification are separate responsibilities. The AI proposes the repair; CodeGuardian controls execution and proof.' },
  { q: 'WHAT MAKES CODEGUARDIAN DIFFERENT?', a: 'It connects evidence, causal tracing, historical repair memory, constrained AI investigation, isolated replay, validation, and human-reviewed Git delivery into one deterministic repair pipeline.' },
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
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<ErrorState | undefined>(undefined)

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
      const payload = await startRun(trimmedUrl)
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
                  {/* Subtle progression indicator */}
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


        {/* FAQ */}
        <section id="faq" className="px-4 py-24 sm:px-8">
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
