import { Link } from 'react-router-dom'
import { LogoMark } from '../Layout'
import type { Run, RunStatus } from '../../api/types'

const STATUS_CONFIG: Record<RunStatus, { label: string; dot: string; text: string; bg: string; border: string }> = {
  queued: {
    label: 'INVESTIGATION QUEUED',
    dot: 'bg-zinc-400',
    text: 'text-zinc-400',
    bg: 'bg-zinc-900/80',
    border: 'border-zinc-700',
  },
  running: {
    label: 'INVESTIGATION RUNNING',
    dot: 'bg-lime animate-pulse',
    text: 'text-lime',
    bg: 'bg-black/60',
    border: 'border-lime/40',
  },
  waiting_for_approval: {
    label: 'AWAITING HUMAN APPROVAL',
    dot: 'bg-amber-400 animate-pulse',
    text: 'text-amber-400',
    bg: 'bg-amber-950/40',
    border: 'border-amber-500/40',
  },
  completed: {
    label: 'INVESTIGATION COMPLETED',
    dot: 'bg-lime',
    text: 'text-lime',
    bg: 'bg-lime/10',
    border: 'border-lime/40',
  },
  failed: {
    label: 'RUN FAILED',
    dot: 'bg-red-400',
    text: 'text-red-400',
    bg: 'bg-red-950/40',
    border: 'border-red-500/40',
  },
  rejected: {
    label: 'PATCH REJECTED',
    dot: 'bg-red-400',
    text: 'text-red-400',
    bg: 'bg-red-950/40',
    border: 'border-red-500/40',
  },
}

export function IDEHeader({ run, runId }: { run?: Run; runId: string }) {
  const status = run?.status ?? 'running'
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.running
  const repoName = run?.repository?.name || run?.repositoryUrl?.split('/').pop() || 'payment-service'

  return (
    <header className="h-14 border-b border-white/[0.08] bg-[#070A0B] px-4 flex items-center justify-between shrink-0 select-none z-30">
      {/* Left: Brand + Repo Selector */}
      <div className="flex items-center gap-4">
        <Link to="/" className="flex items-center gap-2.5 group" aria-label="CodeGuardian home">
          <LogoMark className="h-7 w-7 drop-shadow-[0_0_8px_rgba(198,255,61,0.4)] transition-transform group-hover:scale-105" />
          <span className="font-display text-base font-bold tracking-tight text-white">
            Code<span className="text-lime">Guardian</span>
          </span>
        </Link>

        {/* Repository selector */}
        <div className="flex items-center gap-2 rounded-lg border border-white/[0.08] bg-[#0F1518] px-3 py-1.5 text-xs text-zinc-200 hover:border-white/[0.15] transition-colors cursor-pointer">
          <svg className="h-3.5 w-3.5 text-zinc-400" viewBox="0 0 24 24" fill="currentColor">
            <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
          </svg>
          <span className="font-mono">{repoName}</span>
          <svg className="h-3.5 w-3.5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {/* Center: Live Running Status Pill */}
      <div className={`flex items-center gap-2 rounded-full border ${config.border} ${config.bg} px-3.5 py-1 text-xs font-mono tracking-wider font-semibold shadow-sm`}>
        <span className={`h-2 w-2 rounded-full ${config.dot}`} />
        <span className={config.text}>{config.label}</span>
      </div>

      {/* Right: Run ID + New Investigation + Icons */}
      <div className="flex items-center gap-3">
        <span className="hidden md:inline font-mono text-xs text-zinc-400">
          run {runId ? `${runId.slice(0, 8)}-${runId.slice(8, 12)}-${runId.slice(12, 16)}...` : 'e23827cd-68c1...'}
        </span>

        <Link
          to="/"
          className="rounded-lg border border-white/[0.12] bg-[#0F1518] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#162024] hover:border-lime/40 transition-colors"
        >
          New Investigation
        </Link>

        {/* Notifications */}
        <button
          type="button"
          aria-label="Notifications"
          className="p-1.5 text-zinc-400 hover:text-white rounded-lg hover:bg-[#0F1518] transition-colors"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
        </button>

        {/* Settings */}
        <button
          type="button"
          aria-label="Settings"
          className="p-1.5 text-zinc-400 hover:text-white rounded-lg hover:bg-[#0F1518] transition-colors"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </div>
    </header>
  )
}
