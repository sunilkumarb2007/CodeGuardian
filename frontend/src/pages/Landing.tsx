import { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { ApiError, startRun } from '../api/client'
import { asRecord, readString } from '../api/json'
import { Footer, LogoMark, Shell } from '../components/Layout'
import { Card, Eyebrow, Marquee, Reveal } from '../components/primitives'

const DEFAULT_REPOSITORY = 'https://github.com/sunilkumarb2007/JavaAPICheck'

const PILLARS = [
  {
    id: '01',
    title: 'Reconstruct the hidden failure path.',
    body: 'GhostTrace correlates evidence across services and rebuilds the causal chain from the visible symptom back to the code that actually broke.',
    accent: 'bg-lime',
    chip: '✳',
  },
  {
    id: '02',
    title: 'Reuse verified engineering memory.',
    body: 'Every resolved incident becomes a fingerprinted memory record, so a failure pattern that returns months later is recognised instantly.',
    accent: 'bg-signal-purple',
    chip: '★',
  },
  {
    id: '03',
    title: 'Investigate with evidence, not vibes.',
    body: 'Observation, evidence, hypothesis, decision, result. The investigation reads like an engineering report, never a chat transcript.',
    accent: 'bg-signal-blue',
    chip: '◆',
  },
  {
    id: '04',
    title: 'Prove the repair by replaying it.',
    body: 'The original request is replayed against the patched source. If the behaviour does not change, the patch does not ship.',
    accent: 'bg-signal-orange',
    chip: '▲',
  },
  {
    id: '05',
    title: 'Ship only what a human approves.',
    body: 'Build, tests and validation gates must pass, and a human must approve, before a branch, commit or pull request is ever created.',
    accent: 'bg-signal-pink',
    chip: '●',
  },
]

const PIPELINE = [
  'Repository',
  'Inspection',
  'Architecture',
  'Failure detection',
  'Evidence',
  'GhostTrace',
  'Failure memory',
  'Investigation',
  'Patch',
  'Compatibility',
  'Replay',
  'Build',
  'Tests',
  'Validation',
  'Human approval',
  'Delivery',
  'Memory update',
]

const FAQ = [
  {
    q: 'Where does the data on these screens come from?',
    a: 'Every value is read from the CodeGuardian backend run record. When the backend does not report a field, the interface says “not reported” instead of inventing a value.',
  },
  {
    q: 'Can it deliver a patch on its own?',
    a: 'No. The pipeline halts at the human approval gate. Branch creation, commit and pull request only happen after an explicit approval action.',
  },
  {
    q: 'What happens when validation fails?',
    a: 'The failing gate is surfaced and the run is marked failed. Infrastructure failures are reported separately so they are not counted as a bad repair.',
  },
]

export default function Landing() {
  const navigate = useNavigate()
  const [repositoryUrl, setRepositoryUrl] = useState(DEFAULT_REPOSITORY)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | undefined>(undefined)
  const [activePillar, setActivePillar] = useState(0)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    setSubmitting(true)
    setError(undefined)
    try {
      const payload = await startRun(repositoryUrl.trim())
      const runId = readString(asRecord(payload), 'run_id', 'runId', 'id')
      if (!runId) {
        setError('The backend accepted the request but did not return a run id.')
        return
      }
      navigate(`/runs/${encodeURIComponent(runId)}`)
    } catch (submitError) {
      setError(
        submitError instanceof ApiError
          ? submitError.message
          : submitError instanceof Error
            ? submitError.message
            : 'Unknown error',
      )
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
        <section className="relative overflow-hidden px-4 pb-24 pt-16 sm:px-8">
          <div className="grid-bg animate-gridDrift pointer-events-none absolute inset-0 opacity-70" />
          <div className="relative mx-auto max-w-[1400px]">
            <motion.div
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
              className="mx-auto max-w-4xl text-center"
            >
              <LogoMark className="mx-auto h-24 w-24 animate-logoFloat sm:h-32 sm:w-32" />
              <span className="pill mt-8 border-ink-600 text-ink-300">
                <span className="h-2 w-2 rounded-pill bg-lime" />
                Autonomous engineering failure investigation
              </span>
              <h1 className="display-xl mt-8">
                From failure to <span className="text-lime">verified repair.</span>
              </h1>
              <p className="mx-auto mt-7 max-w-2xl text-lg text-ink-300">
                Trace production failures back to the service that actually broke, investigate the root cause
                with evidence, replay the repair, and deliver a pull request only a human approves.
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
              <div className="flex flex-col gap-3 rounded-card border-2 border-ink-700 bg-ink-850 p-3 sm:flex-row sm:items-center sm:rounded-pill">
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
                  className="btn-primary shrink-0"
                  disabled={submitting}
                  aria-busy={submitting}
                >
                  {submitting ? (
                    <>
                      <LogoMark className="h-5 w-5 animate-logoPulse drop-shadow-none" />
                      Starting…
                    </>
                  ) : (
                    'Investigate failure →'
                  )}
                </button>
              </div>
              {error ? (
                <p className="mt-4 rounded-2xl border-2 border-signal-pink/50 bg-signal-pink/10 px-5 py-4 font-mono text-xs text-signal-pink">
                  {error}
                </p>
              ) : null}
            </motion.form>

            <div className="mx-auto mt-10 flex max-w-3xl flex-wrap justify-center gap-3">
              {['Inspect', 'Trace', 'Investigate', 'Repair'].map((word, index) => (
                <span key={word} className="pill border-ink-600 text-ink-300">
                  <span className="text-lime">0{index + 1}</span>
                  {word}
                </span>
              ))}
            </div>

            <div className="mt-20 grid gap-5 md:grid-cols-3">
              <Reveal>
                <Card className="h-full p-7">
                  <Eyebrow>Visible symptom</Eyebrow>
                  <p className="display-md mt-4 text-signal-pink">HTTP 500</p>
                  <p className="mt-4 text-sm text-ink-300">
                    What the user and the gateway report — almost never where the defect lives.
                  </p>
                </Card>
              </Reveal>
              <Reveal delay={0.08}>
                <Card accent="lime" className="h-full bg-lime p-7 text-ink-900">
                  <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-ink-900/60">
                    Reconstructed root cause
                  </p>
                  <p className="display-md mt-4">Null object access</p>
                  <p className="mt-4 text-sm text-ink-900/70">
                    GhostTrace walks the causal chain until the failure has a file, a method and a line.
                  </p>
                </Card>
              </Reveal>
              <Reveal delay={0.16}>
                <Card className="h-full p-7">
                  <Eyebrow>Delivery gate</Eyebrow>
                  <p className="display-md mt-4">Human approved</p>
                  <p className="mt-4 text-sm text-ink-300">
                    Validated patch, replayed behaviour change, then — and only then — a pull request.
                  </p>
                </Card>
              </Reveal>
            </div>
          </div>
        </section>

        <Marquee items={['GhostTrace', 'Failure memory', 'Replay', 'Validation gates', 'Human approval']} />

        <section id="platform" className="px-4 py-28 sm:px-8">
          <div className="mx-auto grid max-w-[1400px] gap-14 lg:grid-cols-[minmax(0,420px)_minmax(0,1fr)]">
            <div>
              <h2 className="display-lg">Control every failure in production.</h2>
              <div className="mt-8 flex flex-wrap gap-3">
                {PILLARS.map((pillar, index) => (
                  <button
                    key={pillar.id}
                    type="button"
                    onClick={() => setActivePillar(index)}
                    className={`h-12 w-12 rounded-pill border-2 font-mono text-xs transition-colors ${
                      index === activePillar
                        ? 'border-lime bg-lime text-ink-900'
                        : 'border-ink-600 text-ink-300 hover:border-white hover:text-white'
                    }`}
                  >
                    {pillar.id}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-px overflow-hidden rounded-card border-2 border-ink-700 bg-ink-700">
              {PILLARS.map((pillar, index) => {
                const open = index === activePillar
                return (
                  <div key={pillar.id} className="bg-ink-900">
                    <button
                      type="button"
                      onClick={() => setActivePillar(index)}
                      className="flex w-full items-center gap-5 px-7 py-7 text-left"
                    >
                      <span
                        className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-ink-900 ${pillar.accent}`}
                      >
                        {pillar.chip}
                      </span>
                      <span className="font-display text-xl font-bold tracking-tight sm:text-2xl">
                        {pillar.title}
                      </span>
                    </button>
                    <motion.div
                      initial={false}
                      animate={{ height: open ? 'auto' : 0, opacity: open ? 1 : 0 }}
                      transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                      className="overflow-hidden"
                    >
                      <p className="max-w-2xl px-7 pb-8 pl-[76px] text-ink-300">{pillar.body}</p>
                    </motion.div>
                  </div>
                )
              })}
            </div>
          </div>
        </section>

        <section id="pipeline" className="px-4 py-24 sm:px-8">
          <div className="mx-auto max-w-[1400px]">
            <Reveal>
              <Eyebrow>The pipeline</Eyebrow>
              <h2 className="display-lg mt-4 max-w-3xl">
                Seventeen stages. Every one of them observable.
              </h2>
            </Reveal>
            <div className="mt-12 grid gap-px overflow-hidden rounded-card border-2 border-ink-700 bg-ink-700 sm:grid-cols-2 lg:grid-cols-4">
              {PIPELINE.map((stage, index) => (
                <Reveal key={stage} delay={Math.min(index * 0.02, 0.3)}>
                  <div className="group h-full bg-ink-850 p-6 transition-colors hover:bg-lime hover:text-ink-900">
                    <span className="font-mono text-[11px] text-ink-400 group-hover:text-ink-900/60">
                      {String(index + 1).padStart(2, '0')}
                    </span>
                    <p className="mt-4 font-display text-base font-bold tracking-tight">{stage}</p>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        <section id="investigation" className="px-4 py-24 sm:px-8">
          <div className="mx-auto grid max-w-[1400px] gap-6 lg:grid-cols-2">
            <Reveal>
              <Card className="h-full overflow-hidden">
                <div className="border-b-2 border-ink-700 px-7 py-6">
                  <Eyebrow>GhostTrace</Eyebrow>
                </div>
                <div className="space-y-3 p-7">
                  {[
                    { label: 'API Gateway', detail: 'POST /checkout', root: false },
                    { label: 'Order Service', detail: '/orders/checkout', root: false },
                    { label: 'Payment Service', detail: '/payments/charge', root: false },
                    { label: 'PaymentProcessingService.charge()', detail: 'unvalidated dereference', root: true },
                  ].map((node) => (
                    <div
                      key={node.label}
                      className={`rounded-2xl border-2 px-5 py-4 ${
                        node.root ? 'border-lime bg-lime text-ink-900' : 'border-ink-700 bg-ink-800'
                      }`}
                    >
                      <p className="font-display text-sm font-bold tracking-tight">{node.label}</p>
                      <p className={`font-mono text-xs ${node.root ? 'text-ink-900/70' : 'text-ink-400'}`}>
                        {node.detail}
                      </p>
                    </div>
                  ))}
                </div>
              </Card>
            </Reveal>
            <Reveal delay={0.1}>
              <Card className="h-full overflow-hidden">
                <div className="border-b-2 border-ink-700 px-7 py-6">
                  <Eyebrow>Autofix candidate</Eyebrow>
                </div>
                <pre className="code p-7">
                  <div className="bg-signal-pink/10 px-2 text-signal-pink">- process(paymentRecord);</div>
                  <div className="bg-lime/10 px-2 text-lime">+ if (paymentRecord != null) {'{'}</div>
                  <div className="bg-lime/10 px-2 text-lime">+ &nbsp;&nbsp;&nbsp;&nbsp;process(paymentRecord);</div>
                  <div className="bg-lime/10 px-2 text-lime">+ {'}'}</div>
                </pre>
                <div className="grid grid-cols-3 gap-px border-t-2 border-ink-700 bg-ink-700">
                  {[
                    ['Replay', '500 → 200'],
                    ['Gates', 'All pass'],
                    ['Delivery', 'On approval'],
                  ].map(([label, value]) => (
                    <div key={label} className="bg-ink-850 p-6">
                      <p className="eyebrow">{label}</p>
                      <p className="mt-2 font-display text-base font-bold text-lime">{value}</p>
                    </div>
                  ))}
                </div>
              </Card>
            </Reveal>
          </div>
        </section>

        <section id="faq" className="px-4 py-24 sm:px-8">
          <div className="mx-auto max-w-[1400px]">
            <h2 className="display-lg max-w-2xl">Straight answers.</h2>
            <div className="mt-12 divide-y-2 divide-ink-700 border-y-2 border-ink-700">
              {FAQ.map((item) => (
                <details key={item.q} className="group py-7">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-6">
                    <span className="font-display text-xl font-bold tracking-tight sm:text-2xl">{item.q}</span>
                    <span className="font-mono text-2xl text-lime transition-transform group-open:rotate-45">
                      +
                    </span>
                  </summary>
                  <p className="mt-4 max-w-3xl text-ink-300">{item.a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </Shell>
  )
}
