import type { Run } from '../../api/types'

export function IDEStatusBar({
  run,
  runId,
}: {
  run?: Run
  runId: string
}) {
  const completedStages = run?.stages?.filter((s) => s.status === 'passed' || s.status === 'completed' || s.status === 'skipped').length || 4
  const totalStages = 17
  const progressPercent = Math.round((completedStages / totalStages) * 100)
  const displayRunId = runId ? `INV-${runId.slice(0, 4).toUpperCase()}` : 'INV-1042'

  return (
    <footer className="h-9 border-t border-white/[0.08] bg-[#070A0B] px-4 flex items-center justify-between shrink-0 select-none z-30 text-xs font-mono text-zinc-400">
      {/* Left: Investigation Stage Progress */}
      <div className="flex items-center gap-4">
        <span>
          Investigation <span className="text-zinc-200 font-semibold">{displayRunId}</span>
        </span>
        <span className="text-zinc-500">·</span>
        <span>
          Stage <span className="text-zinc-200">{completedStages}</span> / {totalStages}
        </span>
        <div className="w-24 h-1.5 bg-[#0F1518] border border-white/[0.08] rounded-full overflow-hidden">
          <div
            className="h-full bg-lime transition-all duration-500 rounded-full"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <span className="text-zinc-200 font-bold">{progressPercent}%</span>
      </div>

      {/* Right: Telemetry & Auto-save Status */}
      <div className="flex items-center gap-5 text-[11px]">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-lime animate-pulse" />
          <span className="text-zinc-300">Auto-save enabled</span>
        </span>

        <span className="flex items-center gap-1.5 text-zinc-400">
          <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          <span>Last updated: 2s ago</span>
        </span>
      </div>
    </footer>
  )
}
