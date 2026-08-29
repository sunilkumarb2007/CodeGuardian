import { useParams, useNavigate } from 'react-router-dom'
import { useRun } from '../hooks/useRun'
import { Shell, BrandLoader, LogoMark } from '../components/Layout'
import { Card } from '../components/primitives'

export default function Approval() {
  const { runId } = useParams()
  const navigate = useNavigate()
  const { run, loading, error, approve, reject, deciding } = useRun(runId)

  if (loading && !run) {
    return (
      <Shell>
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <BrandLoader label="Retrieving Investigation Details..." />
        </div>
      </Shell>
    )
  }

  if (error || !run) {
    return (
      <Shell>
        <div className="flex flex-col items-center justify-center min-h-[60vh]">
          <div className="text-red-400">Error: {error || 'Run not found'}</div>
        </div>
      </Shell>
    )
  }

  const handleApprove = async () => {
    await approve()
    navigate(`/runs/${runId}`)
  }

  const handleReject = async () => {
    await reject()
    navigate(`/runs/${runId}`)
  }

  return (
    <Shell>
      <div className="max-w-4xl mx-auto py-12 space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white mb-2">Review Patch for {run.repository?.name || 'Repository'}</h1>
            <p className="text-zinc-400 text-sm">
              CodeGuardian has isolated the root cause and generated a verified fix.
            </p>
          </div>
          <LogoMark className="h-8 w-8 text-lime" />
        </div>

        <Card accent="lime" className="p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-ide-divider pb-3 mb-4">
            <span className="text-lg">🛡️</span>
            <h2 className="font-display font-bold text-white text-lg">Incident Details</h2>
          </div>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-zinc-500 mb-1">Status</p>
                <span className="px-2 py-1 bg-amber-500/20 text-amber-400 rounded text-xs font-semibold uppercase">
                  {run.status}
                </span>
              </div>
              <div>
                <p className="text-xs text-zinc-500 mb-1">Target Branch</p>
                <p className="text-zinc-300 font-mono text-sm">main</p>
              </div>
            </div>
            {run.error && (
              <div className="p-4 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-sm">
                {run.error}
              </div>
            )}
          </div>
        </Card>

        <Card accent="blue" className="p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-ide-divider pb-3 mb-4">
            <span className="text-lg">⚡</span>
            <h2 className="font-display font-bold text-white text-lg">Human Decision &amp; Delivery</h2>
          </div>
          <div className="flex justify-end gap-4 p-4 bg-ide-panel/30 border border-ink-800 rounded-lg">
            <button
              onClick={handleReject}
              disabled={deciding}
              className="px-6 py-2 rounded-lg bg-ink-800 hover:bg-ink-700 text-white font-medium transition-colors"
            >
              Reject Fix
            </button>
            <button
              onClick={handleApprove}
              disabled={deciding}
              className="px-6 py-2 rounded-lg bg-lime hover:bg-lime-highlight text-ink-900 font-bold transition-all shadow-[0_0_15px_rgba(182,255,107,0.3)] hover:shadow-[0_0_25px_rgba(182,255,107,0.5)] flex items-center gap-2"
            >
              {deciding ? 'Processing...' : 'Approve & Merge'}
            </button>
          </div>
        </Card>
      </div>
    </Shell>
  )
}
