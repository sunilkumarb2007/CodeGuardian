import { useState } from 'react'
import type { FailureDNA } from '../../api/types'

export function FailureDNAPanel({ dna }: { dna?: FailureDNA }) {
  const [copied, setCopied] = useState(false)

  const fingerprint = dna?.fingerprint || 'PENDING_FINGERPRINT'
  const trigger = dna?.trigger || 'Pending structural analysis'
  const exceptionClass = dna?.exception?.class || 'Pending'
  const endpoint = dna?.request?.endpoint || 'Pending'
  const httpStatus = dna?.request?.http_status || 'N/A'
  const failurePoint = dna?.failure_point || 'Pending'
  const dependency = dna?.dependency || 'Pending'
  const recurrence = dna?.recurrence_count || 0
  const resolved = dna?.resolved_count || 0

  const propagationChain = dna?.propagation_chain || []

  const handleCopy = () => {
    navigator.clipboard.writeText(fingerprint)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleExport = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(dna || { fingerprint }, null, 2))
    const downloadAnchor = document.createElement('a')
    downloadAnchor.setAttribute('href', dataStr)
    downloadAnchor.setAttribute('download', `failure-dna-${fingerprint}.json`)
    document.body.appendChild(downloadAnchor)
    downloadAnchor.click()
    downloadAnchor.remove()
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
                FAILURE DNA · PERMANENT BEHAVIORAL IDENTITY
              </span>
            </div>
            <div className="flex items-center gap-3">
              <h2 className="font-display text-xl font-black text-white tracking-tight">
                {fingerprint}
              </h2>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-lime/15 border border-lime/40 text-lime">
                RESOLVED · IMMUNIZED
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-sans">
              Deterministic multi-dimensional fingerprint preserved for historical traceability and regression immunity.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopy}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/[0.12] bg-ide-base text-xs font-mono text-zinc-200 hover:border-lime/40 transition-colors"
            >
              {copied ? (
                <>
                  <svg className="h-3.5 w-3.5 text-lime" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="text-lime">Copied!</span>
                </>
              ) : (
                <>
                  <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                  <span>Copy Fingerprint</span>
                </>
              )}
            </button>

            <button
              type="button"
              onClick={handleExport}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-lime/40 bg-lime/10 text-xs font-mono text-lime hover:bg-lime/20 transition-colors font-semibold"
            >
              <svg className="h-3.5 w-3.5 text-lime" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>Export DNA</span>
            </button>
          </div>
        </div>
      </div>

      {/* Grid: 2 Columns */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Signature & Dimensions */}
        <div className="lg:col-span-6 rounded-xl border border-ide-divider bg-ide-panel p-5 space-y-4">
          <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-zinc-300 border-b border-white/[0.06] pb-2">
            Observable Dimensions
          </h3>

          <div className="space-y-3 font-mono text-xs">
            <div>
              <span className="text-zinc-500 block text-[10px] uppercase">Trigger</span>
              <span className="text-zinc-200">{trigger}</span>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Exception Class</span>
                <span className="text-red-400 font-semibold">{exceptionClass}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Observed HTTP Status</span>
                <span className="text-red-400 font-semibold">{httpStatus}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Endpoint</span>
                <span className="text-zinc-200">{endpoint}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Failure Point</span>
                <span className="text-zinc-200">{failurePoint}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Causal Dependency</span>
                <span className="text-amber-400 font-semibold">{dependency}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Historical Recurrence</span>
                <span className="text-zinc-200">{recurrence} occurrence{recurrence > 1 ? 's' : ''} ({resolved} resolved)</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Propagation Chain */}
        <div className="lg:col-span-6 rounded-xl border border-ide-divider bg-ide-panel p-5 space-y-4">
          <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-zinc-300 border-b border-white/[0.06] pb-2">
            Causal Propagation Chain
          </h3>

          <div className="space-y-2 relative font-mono text-xs">
            {propagationChain.map((node, i) => {
              const isFailed = node.status === 'failed' || node.status === 'timeout'
              return (
                <div key={node.service} className="flex flex-col items-center">
                  <div
                    className={`w-full flex items-center justify-between p-3 rounded-lg border ${
                      isFailed
                        ? 'border-red-500/40 bg-red-950/20 text-red-300'
                        : 'border-ide-divider bg-ide-base text-zinc-200'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {isFailed ? (
                        <span className="h-2 w-2 rounded-full bg-red-500" />
                      ) : (
                        <span className="h-2 w-2 rounded-full bg-lime" />
                      )}
                      <span className="font-semibold">{node.service}</span>
                    </div>

                    <div className="flex items-center gap-3 text-[11px]">
                      {node.duration_ms !== undefined ? (
                        <span className="text-zinc-400">{node.duration_ms}ms</span>
                      ) : null}
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] uppercase font-bold ${
                          isFailed
                            ? 'bg-red-500/20 text-red-400'
                            : 'bg-lime/20 text-lime'
                        }`}
                      >
                        {node.status}
                      </span>
                    </div>
                  </div>

                  {i < propagationChain.length - 1 ? (
                    <span className="text-zinc-600 text-xs py-0.5">↓</span>
                  ) : null}
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
