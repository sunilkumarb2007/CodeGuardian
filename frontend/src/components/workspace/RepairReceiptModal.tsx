import React, { useState, useEffect } from 'react'

export interface RepairReceiptData {
  receipt_id: string
  receipt_hash: string
  generated_at: string
  run_id: string
  receipt_type: string
  lifecycle_status: string
  outcome: string
  environment: string
  incident: {
    id: string
    incident_number?: string
    title?: string
    endpoint?: string
    http_method?: string
    observed_status_code?: number
    error_fingerprint?: string
    root_cause_summary?: string
  }
  repository: {
    id?: string
    name: string
    url: string
    default_branch: string
    commit_sha?: string
    language?: string
    framework?: string
    build_system?: string
  }
  failure: {
    type: string
    message: string
    symptom_service?: string
    stack_trace_snippet?: string
  }
  root_cause: {
    service: string
    summary: string
    affected_file?: string
    line_number?: number
    causal_chain?: string[]
  }
  repair: {
    patch_id?: string
    patch_number?: number
    affected_files: string[]
    lines_added: number
    lines_removed: number
    diff_snippet?: string
    summary?: string
  }
  verification: {
    replay: string
    build: string
    tests: string
    validation: string
    gates_passed: number
    gates_total: number
    gate_details: Array<{ gate: string; status: string }>
    validated_at?: string
  }
  approval: {
    status: string
    approved_by?: string
    approved_at?: string
    policy?: string
  }
  delivery: {
    status: string
    provider?: string
    branch_name?: string
    pr_number?: number
    pr_url?: string
    merge_status?: string
    delivered_at?: string
    failure_reason?: string
  }
  post_merge: {
    verified: boolean
    exit_code?: number
    merge_sha?: string
    verified_at?: string
  }
  memory: {
    updated: boolean
    memory_id?: string
    error_fingerprint?: string
    updated_at?: string
  }
  ascii_receipt: string
}

interface RepairReceiptModalProps {
  isOpen: boolean
  onClose: () => void
  runId: string
}

export const RepairReceiptModal: React.FC<RepairReceiptModalProps> = ({ isOpen, onClose, runId }) => {
  const [receipt, setReceipt] = useState<RepairReceiptData | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'visual' | 'raw' | 'ascii'>('visual')
  const [copied, setCopied] = useState<boolean>(false)

  useEffect(() => {
    if (!isOpen || !runId) return

    setLoading(true)
    setError(null)
    
    const apiBase = import.meta.env.VITE_API_URL || ''
    fetch(`${apiBase}/api/runs/${runId}/repair-receipt`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to load receipt`)
        return res.json()
      })
      .then((data) => {
        setReceipt(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [isOpen, runId])

  if (!isOpen) return null

  const handleDownload = (format: 'json' | 'markdown') => {
    const apiBase = import.meta.env.VITE_API_URL || ''
    window.open(`${apiBase}/api/runs/${runId}/repair-receipt/download?format=${format}`, '_blank')
  }

  const handleCopyHash = () => {
    if (receipt?.receipt_hash) {
      navigator.clipboard.writeText(receipt.receipt_hash)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'PASS':
      case '6 / 6 PASS':
      case 'COMPLETED':
      case 'DELIVERED':
      case 'APPROVED':
      case 'UPDATED':
      case 'FAILURE_REPAIRED':
      case 'NO_FAILURE_FOUND':
        return 'bg-lime/10 text-lime border-lime/30'
      case 'PENDING':
      case 'AWAITING_APPROVAL':
        return 'bg-amber-400/10 text-amber-300 border-amber-400/30'
      case 'FAIL':
      case 'FAILED':
      case 'BLOCKED':
      case 'DELIVERY_BLOCKED':
      case 'DELIVERY_FAILED':
      case 'VALIDATION_FAILED':
        return 'bg-red-500/10 text-red-400 border-red-500/30'
      default:
        return 'bg-zinc-800 text-zinc-400 border-zinc-700'
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-ide-base border border-ide-divider rounded-2xl shadow-2xl flex flex-col overflow-hidden text-white font-sans">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-ide-divider bg-ide-panel">
          <div className="flex items-center gap-3">
            <div className="w-3 h-3 rounded-full bg-lime animate-pulse" />
            <div>
              <h2 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
                <span>{receipt?.receipt_type?.replace(/_/g, ' ') || 'REPAIR RECEIPT'}</span>
                {receipt && (
                  <span className={`text-[10px] uppercase font-mono px-2 py-0.5 rounded border ${getStatusBadge(receipt.outcome)}`}>
                    {receipt.outcome.replace(/_/g, ' ')}
                  </span>
                )}
              </h2>
              <p className="text-xs text-zinc-400 font-mono">
                Receipt ID: <span className="text-zinc-200">{receipt?.receipt_id || 'Generating...'}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handleDownload('json')}
              className="px-3 py-1.5 text-xs font-mono bg-white/[0.05] hover:bg-white/[0.1] border border-ide-divider rounded-lg transition-colors text-zinc-300 hover:text-white flex items-center gap-1.5"
              title="Download JSON Artifact"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              JSON
            </button>
            <button
              onClick={() => handleDownload('markdown')}
              className="px-3 py-1.5 text-xs font-mono bg-white/[0.05] hover:bg-white/[0.1] border border-ide-divider rounded-lg transition-colors text-zinc-300 hover:text-white flex items-center gap-1.5"
              title="Download Markdown Artifact"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              Markdown
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg hover:bg-white/[0.08] text-zinc-400 hover:text-white transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Audit Hash Bar */}
        {receipt && (
          <div className="px-6 py-2 bg-black/40 border-b border-ide-divider flex items-center justify-between text-[11px] font-mono text-zinc-400">
            <div className="flex items-center gap-2 truncate">
              <span className="text-zinc-300 font-bold uppercase">SHA-256 Audit Hash:</span>
              <span className="text-lime/90 truncate">{receipt.receipt_hash}</span>
            </div>
            <button
              onClick={handleCopyHash}
              className="shrink-0 text-xs text-zinc-400 hover:text-white transition-colors px-2 py-0.5 rounded hover:bg-white/[0.05]"
            >
              {copied ? 'Copied!' : 'Copy Hash'}
            </button>
          </div>
        )}

        {/* View Tabs */}
        <div className="flex items-center px-6 border-b border-ide-divider bg-ide-panel/50 text-xs font-mono">
          <button
            onClick={() => setActiveTab('visual')}
            className={`py-2.5 px-4 border-b-2 font-medium transition-colors ${
              activeTab === 'visual'
                ? 'border-lime text-lime font-bold'
                : 'border-transparent text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Engineering Proof
          </button>
          <button
            onClick={() => setActiveTab('ascii')}
            className={`py-2.5 px-4 border-b-2 font-medium transition-colors ${
              activeTab === 'ascii'
                ? 'border-lime text-lime font-bold'
                : 'border-transparent text-zinc-400 hover:text-zinc-200'
            }`}
          >
            ASCII Receipt
          </button>
          <button
            onClick={() => setActiveTab('raw')}
            className={`py-2.5 px-4 border-b-2 font-medium transition-colors ${
              activeTab === 'raw'
                ? 'border-lime text-lime font-bold'
                : 'border-transparent text-zinc-400 hover:text-zinc-200'
            }`}
          >
            Canonical JSON
          </button>
        </div>

        {/* Body Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16 text-zinc-400 space-y-3">
              <div className="w-8 h-8 border-2 border-lime border-t-transparent rounded-full animate-spin" />
              <p className="text-xs font-mono">Loading authoritative repair receipt...</p>
            </div>
          )}

          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-300 text-xs">
              <p className="font-bold">Error loading receipt</p>
              <p className="mt-1 font-mono text-zinc-400">{error}</p>
            </div>
          )}

          {!loading && !error && receipt && (
            <>
              {activeTab === 'visual' && (
                <div className="space-y-6 text-xs">
                  {/* Grid 1: Incident & Repository */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl border border-ide-divider bg-ide-panel/80 space-y-2">
                      <span className="font-mono text-[10px] text-zinc-300 font-bold uppercase tracking-wider block">
                        INCIDENT & TARGET
                      </span>
                      <div className="space-y-1 font-mono text-[11px]">
                        <p><span className="text-zinc-400">Incident:</span> <span className="text-zinc-200">{receipt.incident.id}</span></p>
                        <p><span className="text-zinc-400">Endpoint:</span> <span className="text-zinc-200">{receipt.incident.endpoint || 'N/A'}</span></p>
                        <p><span className="text-zinc-400">Observed Status:</span> <span className="text-amber-400 font-bold">{receipt.incident.observed_status_code || 500}</span></p>
                        <p><span className="text-zinc-400">Fingerprint:</span> <span className="text-lime">{receipt.incident.error_fingerprint}</span></p>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border border-ide-divider bg-ide-panel/80 space-y-2">
                      <span className="font-mono text-[10px] text-zinc-300 font-bold uppercase tracking-wider block">
                        REPOSITORY INTELLIGENCE
                      </span>
                      <div className="space-y-1 font-mono text-[11px]">
                        <p><span className="text-zinc-400">Repository:</span> <span className="text-zinc-200">{receipt.repository.name}</span></p>
                        <p><span className="text-zinc-400">Branch / Commit:</span> <span className="text-zinc-200">{receipt.repository.default_branch} @ {receipt.repository.commit_sha?.slice(0, 8) || 'HEAD'}</span></p>
                        <p><span className="text-zinc-400">Stack:</span> <span className="text-zinc-200">{receipt.repository.language || 'java'} / {receipt.repository.framework || 'spring'} / {receipt.repository.build_system || 'maven'}</span></p>
                        <p><span className="text-zinc-400">Environment:</span> <span className="text-zinc-200 uppercase">{receipt.environment}</span></p>
                      </div>
                    </div>
                  </div>

                  {/* Failure & Root Cause */}
                  <div className="p-4 rounded-xl border border-ide-divider bg-ide-panel/80 space-y-2">
                    <span className="font-mono text-[10px] text-zinc-300 font-bold uppercase tracking-wider block">
                      FAILURE & ROOT CAUSE ANALYSIS
                    </span>
                    <div className="space-y-2">
                      <p className="text-zinc-300 text-[12px] font-semibold text-red-300">
                        {receipt.failure.message}
                      </p>
                      <p className="text-zinc-300 text-[12px] bg-black/40 p-2.5 rounded-lg border border-ide-divider font-mono">
                        <span className="text-lime font-bold">Root Cause:</span> {receipt.root_cause.summary}
                      </p>
                      {receipt.root_cause.affected_file && (
                        <p className="font-mono text-[11px] text-zinc-400">
                          Affected Source: <span className="text-zinc-200">{receipt.root_cause.affected_file}</span> (Line {receipt.root_cause.line_number || 'N/A'})
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Proof Gates */}
                  <div className="p-4 rounded-xl border border-ide-divider bg-ide-panel/80 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-zinc-300 font-bold uppercase tracking-wider block">
                        VERIFICATION & DETERMINISTIC SAFETY GATES
                      </span>
                      <span className={`font-mono text-xs px-2.5 py-0.5 rounded border ${getStatusBadge(receipt.verification.validation)}`}>
                        {receipt.verification.validation}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-center font-mono">
                      <div className="p-2.5 rounded-lg bg-black/30 border border-ide-divider">
                        <span className="text-[10px] text-zinc-400 block">REPLAY</span>
                        <span className={`text-xs font-bold ${receipt.verification.replay === 'PASS' ? 'text-lime' : 'text-zinc-400'}`}>
                          {receipt.verification.replay}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-black/30 border border-ide-divider">
                        <span className="text-[10px] text-zinc-400 block">BUILD</span>
                        <span className={`text-xs font-bold ${receipt.verification.build === 'PASS' ? 'text-lime' : 'text-zinc-400'}`}>
                          {receipt.verification.build}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-black/30 border border-ide-divider">
                        <span className="text-[10px] text-zinc-400 block">TESTS</span>
                        <span className={`text-xs font-bold ${receipt.verification.tests === 'PASS' ? 'text-lime' : 'text-zinc-400'}`}>
                          {receipt.verification.tests}
                        </span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-black/30 border border-ide-divider">
                        <span className="text-[10px] text-zinc-400 block">POST-MERGE</span>
                        <span className={`text-xs font-bold ${receipt.post_merge.verified ? 'text-lime' : 'text-zinc-400'}`}>
                          {receipt.post_merge.verified ? 'VERIFIED' : 'N/A'}
                        </span>
                      </div>
                    </div>

                    {receipt.verification.gate_details && receipt.verification.gate_details.length > 0 && (
                      <div className="mt-2 space-y-1 font-mono text-[11px]">
                        {receipt.verification.gate_details.map((g, idx) => (
                          <div key={idx} className="flex items-center justify-between py-1 border-b border-ide-divider/50">
                            <span className="text-zinc-400">{idx + 1}. {g.gate}</span>
                            <span className={g.status === 'PASS' ? 'text-lime font-bold' : 'text-red-400'}>{g.status}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Delivery & Memory */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl border border-ide-divider bg-ide-panel/80 space-y-2">
                      <span className="font-mono text-[10px] text-zinc-300 font-bold uppercase tracking-wider block">
                        GITHUB DELIVERY
                      </span>
                      <div className="space-y-1 font-mono text-[11px]">
                        <p><span className="text-zinc-400">Status:</span> <span className={`font-bold ${receipt.delivery.status === 'DELIVERED' ? 'text-lime' : 'text-zinc-300'}`}>{receipt.delivery.status}</span></p>
                        {receipt.delivery.pr_url ? (
                          <p><span className="text-zinc-400">PR:</span> <a href={receipt.delivery.pr_url} target="_blank" rel="noreferrer" className="text-lime underline">#{receipt.delivery.pr_number} ({receipt.delivery.branch_name})</a></p>
                        ) : (
                          <p><span className="text-zinc-400">PR:</span> <span className="text-zinc-400">None</span></p>
                        )}
                        {receipt.delivery.failure_reason && (
                          <p><span className="text-red-400">Block Reason:</span> <span className="text-zinc-300">{receipt.delivery.failure_reason}</span></p>
                        )}
                      </div>
                    </div>

                    <div className="p-4 rounded-xl border border-ide-divider bg-ide-panel/80 space-y-2">
                      <span className="font-mono text-[10px] text-zinc-300 font-bold uppercase tracking-wider block">
                        FAILURE MEMORY
                      </span>
                      <div className="space-y-1 font-mono text-[11px]">
                        <p><span className="text-zinc-400">Memory Status:</span> <span className={`font-bold ${receipt.memory.updated ? 'text-lime' : 'text-zinc-400'}`}>{receipt.memory.updated ? 'UPDATED' : 'NOT UPDATED'}</span></p>
                        <p><span className="text-zinc-400">Fingerprint:</span> <span className="text-zinc-300">{receipt.memory.error_fingerprint}</span></p>
                      </div>
                    </div>
                  </div>

                  {/* Diff Snippet if present */}
                  {receipt.repair.diff_snippet && (
                    <div className="space-y-2">
                      <span className="font-mono text-[10px] text-zinc-300 font-bold uppercase tracking-wider block">
                        VERIFIED CODE CHANGE (+{receipt.repair.lines_added} / -{receipt.repair.lines_removed})
                      </span>
                      <pre className="p-3 bg-black/60 rounded-xl border border-ide-divider font-mono text-[11px] text-zinc-300 overflow-x-auto">
                        {receipt.repair.diff_snippet}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'ascii' && (
                <div className="bg-black/90 p-4 rounded-xl border border-ide-divider overflow-x-auto">
                  <pre className="font-mono text-xs text-lime leading-relaxed whitespace-pre select-all">
                    {receipt.ascii_receipt}
                  </pre>
                </div>
              )}

              {activeTab === 'raw' && (
                <div className="bg-black/90 p-4 rounded-xl border border-ide-divider overflow-x-auto">
                  <pre className="font-mono text-xs text-zinc-300 leading-relaxed whitespace-pre select-all">
                    {JSON.stringify(receipt, null, 2)}
                  </pre>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-ide-divider bg-ide-panel flex items-center justify-between text-xs font-mono text-zinc-400">
          <span>CodeGuardian v2.0 Production Assurance</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-white/[0.08] hover:bg-white/[0.15] text-white rounded-lg transition-colors font-sans"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
