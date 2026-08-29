import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { runFailureScenario } from '../../api/client'

interface ScenarioItem {
  id: string
  name: string
  category: string
  description: string
}


const SCENARIOS: ScenarioItem[] = [
  {
    id: 'null_object_access',
    name: 'Null Object Access (NPE)',
    category: 'Domain Logic',
    description: 'Merchant lookup returns null and is dereferenced in business flow.',
  },
  {
    id: 'database_timeout',
    name: 'Database Lock Timeout',
    category: 'Persistence',
    description: 'PostgreSQL transaction lock contention causes query timeout after 3000ms.',
  },
  {
    id: 'rate_limit_429',
    name: 'Upstream Rate Limit (HTTP 429)',
    category: 'External Dependency',
    description: 'Payment gateway throttles traffic burst exceeding 50 req/sec quota.',
  },
  {
    id: 'invalid_payload',
    name: 'Malformed Payload Schema',
    category: 'API Gateway',
    description: 'Client payload omits mandatory currency field, causing serialization failure.',
  },
  {
    id: 'redis_failure',
    name: 'Redis Lock Drop Failover',
    category: 'Infrastructure',
    description: 'Redis master failover drops distributed run lock lease prematurely.',
  },
]

export function FailureLabPanel() {
  const navigate = useNavigate()
  const [selectedId, setSelectedId] = useState<string>('null_object_access')
  const [launching, setLaunching] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  const handleLaunch = async (scenarioId: string) => {
    setLaunching(true)
    setError(null)
    try {
      const res = await runFailureScenario(scenarioId)
      if (res.run_id) {
        navigate(`/runs/${res.run_id}`)
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to launch controlled scenario')
    } finally {
      setLaunching(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-lime/30 bg-ide-panel p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-lime animate-pulse" />
              <span className="font-mono text-xs uppercase tracking-widest text-lime font-bold">
                FAILURE LAB · CONTROLLED DEMONSTRATION SCENARIOS
              </span>
            </div>
            <h2 className="font-display text-xl font-black text-white tracking-tight">
              Deterministic Engineering Scenarios
            </h2>
            <p className="text-xs text-zinc-400 font-sans">
              Controlled failure injection harness executing live through the full 17-stage deterministic investigation and repair pipeline.
            </p>
          </div>
        </div>
      </div>

      {error ? (
        <div className="p-3 rounded-lg border border-red-500/40 bg-red-950/20 text-xs font-mono text-red-400">
          {error}
        </div>
      ) : null}

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {SCENARIOS.map((sc) => {
          const isSelected = sc.id === selectedId
          return (
            <div
              key={sc.id}
              onClick={() => setSelectedId(sc.id)}
              className={`p-5 rounded-xl border transition-all cursor-pointer flex flex-col justify-between space-y-4 ${
                isSelected
                  ? 'border-lime/80 bg-lime/[0.04] shadow-[0_0_16px_rgba(198,255,61,0.15)]'
                  : 'border-ide-divider bg-ide-panel hover:border-white/[0.18]'
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="px-2 py-0.5 rounded font-mono text-[10px] font-bold bg-white/[0.06] text-zinc-300">
                    {sc.category}
                  </span>
                </div>

                <h3 className="font-display text-base font-bold text-white leading-snug">
                  {sc.name}
                </h3>
                <p className="text-xs text-zinc-400 font-sans leading-relaxed">
                  {sc.description}
                </p>
              </div>

              <div className="border-t border-white/[0.06] pt-3 space-y-2">
                <button
                  type="button"
                  disabled={launching}
                  onClick={(e) => {
                    e.stopPropagation()
                    void handleLaunch(sc.id)
                  }}
                  className="w-full py-2 rounded-lg bg-lime text-black font-display text-xs font-bold hover:bg-lime-soft transition-colors disabled:opacity-50"
                >
                  {launching && isSelected ? 'Launching...' : 'Run Scenario →'}
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
