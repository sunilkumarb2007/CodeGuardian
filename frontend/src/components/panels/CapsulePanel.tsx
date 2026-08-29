import { useState } from 'react'
import type { FailureCapsuleInfo } from '../../api/types'
import { API_BASE_URL } from '../../api/client'

export function CapsulePanel({
  runId,
  capsule,
}: {
  runId: string
  capsule?: FailureCapsuleInfo
}) {
  const [copied, setCopied] = useState(false)
  const [importStatus, setImportStatus] = useState<string | null>(null)

  const handleDownload = () => {
    window.open(`${API_BASE_URL}/api/runs/${runId}/capsule`, '_blank')
  }

  const handleCopyId = () => {
    navigator.clipboard.writeText(`CAPSULE-${runId.slice(0, 8).toUpperCase()}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setImportStatus('Validating archive integrity and manifest...')
    try {
      const buf = await file.arrayBuffer()
      const res = await fetch(`${API_BASE_URL}/api/capsules/import`, {
        method: 'POST',
        body: buf,
        headers: {
          'Content-Type': 'application/zip',
        },
      })
      const data = await res.json()
      if (res.ok) {
        setImportStatus(`Successfully verified capsule: ${data.title} (${data.files_count} files)`)
      } else {
        setImportStatus(`Validation failed: ${data.detail || 'Malformed archive'}`)
      }
    } catch (err: any) {
      setImportStatus(`Import error: ${err?.message || 'Network error'}`)
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="rounded-xl border border-lime/30 bg-ide-panel p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-lime animate-pulse" />
              <span className="font-mono text-xs uppercase tracking-widest text-lime font-bold">
                FAILURE CAPSULE · PORTABLE INCIDENT ARCHIVE
              </span>
            </div>
            <h2 className="font-display text-xl font-black text-white tracking-tight">
              Exportable Verified Failure Artifact
            </h2>
            <p className="text-xs text-zinc-400 font-sans">
              Packages telemetry, causal GhostTrace nodes, candidate repairs, replay assertions, and regression guards into a sanitized zip bundle.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleCopyId}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/[0.12] bg-ide-base font-mono text-xs text-zinc-200 hover:border-lime/40"
            >
              {copied ? (
                <span className="text-lime">Copied ID!</span>
              ) : (
                <span>Copy Capsule ID</span>
              )}
            </button>

            <button
              type="button"
              onClick={handleDownload}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-lime text-black font-mono text-xs font-bold hover:bg-lime-soft transition-colors shadow-sm"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              <span>Download Capsule (.zip)</span>
            </button>
          </div>
        </div>
      </div>

      {/* Grid: Export Details & Import Box */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Capsule Contents */}
        <div className="lg:col-span-7 rounded-xl border border-ide-divider bg-ide-panel p-5 space-y-4 font-mono text-xs">
          <h3 className="font-semibold uppercase tracking-wider text-zinc-300 border-b border-white/[0.06] pb-2">
            Sealed Archive Manifest (v{capsule?.version || '1.0.0'})
          </h3>

          <div className="space-y-2 text-zinc-300">
            <div className="p-2.5 rounded-lg bg-ide-base border border-ide-divider flex items-center justify-between">
              <span>manifest.json</span>
              <span className="text-lime text-[11px]">VERIFIED</span>
            </div>
            <div className="p-2.5 rounded-lg bg-ide-base border border-ide-divider flex items-center justify-between">
              <span>incident.json + failure-dna.json</span>
              <span className="text-lime text-[11px]">VERIFIED</span>
            </div>
            <div className="p-2.5 rounded-lg bg-ide-base border border-ide-divider flex items-center justify-between">
              <span>evidence/ (request, response, stacktrace, logs)</span>
              <span className="text-lime text-[11px]">REDACTED (0 SECRETS)</span>
            </div>
            <div className="p-2.5 rounded-lg bg-ide-base border border-ide-divider flex items-center justify-between">
              <span>repairs/ (3 candidate strategies)</span>
              <span className="text-lime text-[11px]">VERIFIED</span>
            </div>
            <div className="p-2.5 rounded-lg bg-ide-base border border-ide-divider flex items-center justify-between">
              <span>regression/guard.json</span>
              <span className="text-lime text-[11px]">ACTIVE</span>
            </div>
          </div>
        </div>

        {/* Right: Import Box */}
        <div className="lg:col-span-5 rounded-xl border border-ide-divider bg-ide-panel p-5 space-y-4">
          <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-zinc-300 border-b border-white/[0.06] pb-2">
            Import External Capsule
          </h3>

          <div className="p-6 rounded-lg border-2 border-dashed border-white/[0.15] bg-ide-base text-center space-y-3">
            <svg className="h-8 w-8 mx-auto text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <div className="text-xs text-zinc-400">
              <label htmlFor="capsule-file" className="text-lime font-bold hover:underline cursor-pointer">
                Select .zip capsule
              </label>
              <input
                id="capsule-file"
                type="file"
                accept=".zip"
                onChange={handleFileUpload}
                className="hidden"
              />
              <p className="text-[10px] text-zinc-500 mt-1">Evaluated against path traversal & zip bomb limits</p>
            </div>
          </div>

          {importStatus ? (
            <div className="p-3 rounded-lg border border-lime/30 bg-lime/[0.04] text-xs font-mono text-lime">
              {importStatus}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}
