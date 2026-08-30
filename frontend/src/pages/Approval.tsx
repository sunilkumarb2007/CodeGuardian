import { useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { useRun } from '../hooks/useRun'
import { Shell, BrandLoader } from '../components/Layout'
import { RepairReceiptModal } from '../components/workspace/RepairReceiptModal'
import { API_BASE_URL } from '../api/client'

export default function Approval() {
  const { runId } = useParams<{ runId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { run, loading, error } = useRun(runId)

  const [isReceiptOpen, setIsReceiptOpen] = useState(false)
  const [actionProcessing, setActionProcessing] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const [actionSuccess, setActionSuccess] = useState<string | null>(null)

  const token = searchParams.get('token')

  const handleApprove = async () => {
    if (!runId) return
    setActionProcessing(true)
    setActionError(null)

    try {
      const url = `${API_BASE_URL}/api/runs/${runId}/approve${token ? `?token=${encodeURIComponent(token)}` : ''}`
      const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `HTTP ${res.status}: Failed to approve patch`)
      }
      setActionSuccess('Patch approved successfully. Initiating GitHub delivery and post-merge replay...')
      setTimeout(() => {
        navigate(`/runs/${runId}`)
      }, 1200)
    } catch (err: any) {
      setActionError(err.message || 'Failed to approve patch')
      setActionProcessing(false)
    }
  }

  const handleReject = async () => {
    if (!runId) return
    setActionProcessing(true)
    setActionError(null)

    try {
      const url = `${API_BASE_URL}/api/runs/${runId}/reject${token ? `?token=${encodeURIComponent(token)}` : ''}`
      const res = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' } })
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.detail || `HTTP ${res.status}: Failed to reject patch`)
      }
      setActionSuccess('Patch rejected. Delivery cancelled.')
      setTimeout(() => {
        navigate(`/runs/${runId}`)
      }, 1200)
    } catch (err: any) {
      setActionError(err.message || 'Failed to reject patch')
      setActionProcessing(false)
    }
  }

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
        <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 font-mono text-sm max-w-lg text-center">
            {error || 'Investigation Run not found'}
          </div>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-white/[0.08] hover:bg-white/[0.15] text-white rounded-lg font-sans text-xs transition-colors"
          >
            Return to Dashboard
          </button>
        </div>
      </Shell>
    )
  }

  const isAwaitingApproval = run.status?.toLowerCase() === 'waiting_for_approval'
  const hasValidatedPatch = Boolean(
    run.patch?.id &&
    (run.patch?.status?.toLowerCase() === 'validated' || run.patch?.status === 'VALIDATED') &&
    (run.patch?.affectedFiles?.length || run.patch?.file)
  )
  const validationPassed = run.validation?.status?.toLowerCase() === 'passed' || (run.validation?.passedCount && run.validation.passedCount >= 6)
  const canApprove = isAwaitingApproval && hasValidatedPatch && Boolean(validationPassed)

  const replayGate = run.validation?.gates?.find(g => g.name.toLowerCase().includes('replay'))
  const buildGate = run.validation?.gates?.find(g => g.name.toLowerCase().includes('build'))
  const testGate = run.validation?.gates?.find(g => g.name.toLowerCase().includes('test') || g.name.toLowerCase().includes('regression'))
  const replayStatus = replayGate?.passed ? 'PASS' : (replayGate ? 'FAIL' : (validationPassed ? 'PASS' : 'PENDING'))
  const buildStatus = buildGate?.passed ? 'PASS' : (buildGate ? 'FAIL' : (validationPassed ? 'PASS' : 'PENDING'))
  const testsStatus = testGate?.passed ? 'PASS' : (testGate ? 'FAIL' : (validationPassed ? 'PASS' : 'PENDING'))
  const deliveryStatus = canApprove ? 'READY' : 'BLOCKED'

  return (
    <Shell>
      <div className="max-w-4xl mx-auto py-10 space-y-6 text-white font-sans">
        {/* Header Bar */}
        <div className="flex items-center justify-between border-b border-ide-divider pb-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-white">
                Human Approval Review
              </h1>
              <span className={`px-2.5 py-0.5 text-[11px] font-mono font-bold uppercase rounded border ${
                isAwaitingApproval ? 'bg-amber-400/10 text-amber-300 border-amber-400/30' : 'bg-lime/10 text-lime border-lime/30'
              }`}>
                {run.status?.replace(/_/g, ' ')}
              </span>
            </div>
            <p className="text-zinc-400 text-xs font-mono mt-1">
              Target: <span className="text-zinc-200 font-bold">{run.repository?.name || 'Repository'}</span> &middot; Run ID: <span className="text-lime">{runId}</span>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsReceiptOpen(true)}
              className="px-3.5 py-1.5 text-xs font-mono bg-lime/10 hover:bg-lime/20 border border-lime/40 text-lime rounded-lg transition-colors flex items-center gap-1.5 font-bold"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              View Repair Receipt
            </button>
          </div>
        </div>

        {/* Action Alerts */}
        {actionSuccess && (
          <div className="p-4 bg-lime/10 border border-lime/40 rounded-xl text-lime text-xs font-mono">
            {actionSuccess}
          </div>
        )}
        {actionError && (
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 text-xs font-mono">
            <strong>Action Blocked:</strong> {actionError}
          </div>
        )}
        {!canApprove && isAwaitingApproval && (
          <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300 text-xs font-mono">
            <strong>Safety Gate Warning:</strong> Approval action is unavailable because this run has not passed all required deterministic validation gates or the patch candidate is invalid.
          </div>
        )}

        {/* Incident Summary Card */}
        <div className="p-6 rounded-2xl border border-ide-divider bg-ide-panel/80 space-y-4">
          <div className="flex items-center justify-between border-b border-ide-divider pb-3">
            <div className="flex items-center gap-2">
              <span className="text-sm">🛡️</span>
              <h2 className="font-mono font-bold text-xs uppercase text-zinc-300 tracking-wider">
                Incident &amp; Failure Isolation
              </h2>
            </div>
            <span className="text-xs font-mono text-red-400 font-bold bg-red-500/10 px-2 py-0.5 rounded border border-red-500/30">
              {run.incident?.httpStatus ? `HTTP ${run.incident.httpStatus}` : 'Active Incident'}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
            <div className="space-y-1 text-zinc-400">
              <p>Title: <span className="text-zinc-200 font-bold">{run.incident?.title || 'Runtime Defect'}</span></p>
              <p>Service: <span className="text-lime">{run.incident?.service || 'N/A'}</span></p>
              <p>Environment: <span className="text-zinc-200 uppercase">{run.incident?.environment || 'production'}</span></p>
            </div>
            <div className="space-y-1 text-zinc-400">
              <p>Fingerprint: <span className="text-lime">{run.incident?.fingerprint || run.incident?.errorType || 'ACTIVE_DEFECT'}</span></p>
              <p>Target Branch: <span className="text-zinc-200">{run.repository?.defaultBranch || 'main'}</span></p>
              <p>Patch Status: <span className={hasValidatedPatch ? 'text-lime font-bold' : 'text-amber-400 font-bold'}>{run.patch?.status || 'PENDING'}</span></p>
            </div>
          </div>

          {run.incident?.summary && (
            <div className="p-3 bg-black/40 rounded-xl border border-ide-divider text-xs text-zinc-300 font-mono">
              <strong className="text-lime">Root Cause:</strong> {run.incident.summary}
            </div>
          )}
        </div>

        {/* Deterministic Safety Verification Card */}
        <div className="p-6 rounded-2xl border border-ide-divider bg-ide-panel/80 space-y-4">
          <div className="flex items-center justify-between border-b border-ide-divider pb-3">
            <div className="flex items-center gap-2">
              <span className="text-sm">⚡</span>
              <h2 className="font-mono font-bold text-xs uppercase text-zinc-300 tracking-wider">
                Deterministic Multi-Gate Verification Proof
              </h2>
            </div>
            <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
              validationPassed ? 'bg-lime/10 text-lime border-lime/30' : 'bg-red-500/10 text-red-400 border-red-500/30'
            }`}>
              {run.validation?.passedCount ?? (validationPassed ? 6 : 0)} / {run.validation?.totalCount ?? 6} GATES PASSED
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center font-mono">
            <div className="p-3 rounded-xl bg-black/40 border border-ide-divider">
              <span className="text-[10px] text-zinc-400 uppercase block">GHOST REPLAY</span>
              <span className={`text-xs font-bold mt-1 block ${replayStatus === 'PASS' ? 'text-lime' : 'text-red-400'}`}>{replayStatus}</span>
            </div>
            <div className="p-3 rounded-xl bg-black/40 border border-ide-divider">
              <span className="text-[10px] text-zinc-400 uppercase block">SANDBOXED BUILD</span>
              <span className={`text-xs font-bold mt-1 block ${buildStatus === 'PASS' ? 'text-lime' : 'text-red-400'}`}>{buildStatus}</span>
            </div>
            <div className="p-3 rounded-xl bg-black/40 border border-ide-divider">
              <span className="text-[10px] text-zinc-400 uppercase block">REGRESSION TESTS</span>
              <span className={`text-xs font-bold mt-1 block ${testsStatus === 'PASS' ? 'text-lime' : 'text-red-400'}`}>{testsStatus}</span>
            </div>
            <div className="p-3 rounded-xl bg-black/40 border border-ide-divider">
              <span className="text-[10px] text-zinc-400 uppercase block">DELIVERY GATE</span>
              <span className={`text-xs font-bold mt-1 block ${deliveryStatus === 'READY' ? 'text-lime' : 'text-amber-400'}`}>{deliveryStatus}</span>
            </div>
          </div>
        </div>

        {/* Human Decision Gate & Actions */}
        <div className="p-6 rounded-2xl border border-ide-divider bg-ide-panel/80 space-y-4">
          <div className="flex items-center justify-between border-b border-ide-divider pb-3">
            <div className="flex items-center gap-2">
              <span className="text-sm">🔐</span>
              <h2 className="font-mono font-bold text-xs uppercase text-zinc-300 tracking-wider">
                Human Decision &amp; Delivery Authorization
              </h2>
            </div>
          </div>

          <p className="text-xs text-zinc-400 font-sans">
            Approving this patch will trigger the CodeGuardian GitHub App to create the verified pull request on <code className="text-lime">{run.repository?.name || 'Repository'}</code>, execute post-merge verification, and update production memory.
          </p>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              onClick={handleReject}
              disabled={actionProcessing || !isAwaitingApproval}
              className="px-5 py-2.5 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] border border-red-500/30 text-red-400 font-medium text-xs font-mono transition-colors disabled:opacity-50"
            >
              {actionProcessing ? 'Processing...' : 'Reject Fix'}
            </button>
            <button
              onClick={handleApprove}
              disabled={actionProcessing || !canApprove}
              className="px-6 py-2.5 rounded-xl bg-lime hover:bg-lime/90 text-black font-bold text-xs font-mono transition-all shadow-[0_0_20px_rgba(198,255,61,0.25)] flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {actionProcessing ? 'Processing...' : '✓ Approve & Merge to Production'}
            </button>
          </div>
        </div>
      </div>

      {/* Repair Receipt Modal */}
      {runId && (
        <RepairReceiptModal
          isOpen={isReceiptOpen}
          onClose={() => setIsReceiptOpen(false)}
          runId={runId}
        />
      )}
    </Shell>
  )
}
