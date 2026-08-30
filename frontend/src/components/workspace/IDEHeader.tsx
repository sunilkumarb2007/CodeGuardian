import { useState } from 'react'
import { Link } from 'react-router-dom'
import { LogoMark } from '../Layout'
import type { Run } from '../../api/types'
import { resolveRunPresentation } from '../../api/presentation'

interface IDEHeaderProps {
  run?: Run
  runId: string
  onToggleFullScreen?: () => void
  isFullScreen?: boolean
  onOpenReceipt?: () => void
}

export function IDEHeader({ run, runId, onToggleFullScreen, isFullScreen, onOpenReceipt }: IDEHeaderProps) {
  const [showRepoMenu, setShowRepoMenu] = useState(false)

  const presentation = resolveRunPresentation(run)
  const activeRepoName = presentation.displayRepositoryName
  const repoUrl = run?.repositoryUrl || run?.repository?.url || ''
  const defaultBranch = run?.repository?.defaultBranch || 'main'

  return (
    <header className="h-14 border-b border-ide-divider bg-ide-base px-4 flex items-center justify-between shrink-0 select-none z-30 relative">
      {/* Left: Brand + Interactive Repo Selector */}
      <div className="flex items-center gap-4">
        <Link to="/" className="flex items-center gap-2.5 group" aria-label="CodeGuardian home">
          <LogoMark className="h-7 w-7 drop-shadow-[0_0_8px_rgba(198,255,61,0.4)] transition-transform group-hover:scale-105" />
          <span className="font-display text-base font-bold tracking-tight text-white">
            Code<span className="text-lime">Guardian</span>
          </span>
        </Link>

        {/* Repository Badge / Selector */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowRepoMenu(!showRepoMenu)}
            className="flex items-center gap-2 rounded-lg border border-ide-divider bg-ide-panel px-3 py-1.5 text-xs text-zinc-200 hover:border-white/[0.2] transition-colors"
          >
            <svg className="h-3.5 w-3.5 text-zinc-400" viewBox="0 0 24 24" fill="currentColor">
              <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
            </svg>
            <span className="font-mono font-medium">{activeRepoName}</span>
            <svg className={`h-3.5 w-3.5 text-zinc-500 transition-transform ${showRepoMenu ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showRepoMenu ? (
            <div className="absolute top-full left-0 mt-1.5 w-72 rounded-xl border border-white/[0.1] bg-[#0C1114] p-3 shadow-2xl z-50 font-mono text-xs space-y-2">
              <div className="text-[10px] text-zinc-400 uppercase font-bold tracking-wider">
                Active Repository Context
              </div>
              <div className="p-2.5 rounded-lg bg-lime/10 border border-lime/30 text-zinc-200">
                <div className="flex items-center justify-between font-bold text-lime">
                  <span>{activeRepoName}</span>
                  <span className="text-[10px] text-zinc-400 font-normal">branch: {defaultBranch}</span>
                </div>
                {repoUrl ? (
                  <div className="mt-1 text-[11px] text-zinc-400 truncate font-sans">
                    {repoUrl}
                  </div>
                ) : null}
              </div>
              <Link
                to="/"
                onClick={() => setShowRepoMenu(false)}
                className="block text-center py-1.5 text-xs text-lime hover:underline font-sans"
              >
                + Switch or Investigate Another Repository
              </Link>
            </div>
          ) : null}
        </div>
      </div>


      {/* Center: Live Running Status Pill */}
      <div className={`flex items-center gap-2 rounded-full border ${presentation.headerBorder} ${presentation.headerBg} px-3.5 py-1 text-xs font-mono tracking-wider font-semibold shadow-sm`}>
        <span className={`h-2 w-2 rounded-full ${presentation.headerDot}`} />
        <span className={presentation.headerTone === 'lime' ? 'text-lime' : presentation.headerTone === 'amber' ? 'text-amber-400' : presentation.headerTone === 'cyan' ? 'text-cyan-400' : presentation.headerTone === 'red' ? 'text-red-400' : 'text-zinc-400'}>
          {presentation.headerStatus}
        </span>
      </div>

      {/* Right: Run ID + Repair Receipt + New Investigation + Interactive Icons */}
      <div className="flex items-center gap-3">
        {onOpenReceipt && (
          <button
            type="button"
            onClick={onOpenReceipt}
            className="flex items-center gap-1.5 rounded-lg border border-lime/40 bg-lime/10 px-3 py-1.5 text-xs font-mono font-bold text-lime hover:bg-lime/20 transition-colors shadow-sm"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Repair Receipt
          </button>
        )}

        <span className="hidden md:inline font-mono text-xs text-zinc-400">
          run {runId ? `${runId.slice(0, 8)}-${runId.slice(8, 12)}-${runId.slice(12, 16)}...` : '710b892e-766-c4b...'}
        </span>

        <Link
          to="/"
          className="rounded-lg border border-white/[0.12] bg-ide-panel px-3 py-1.5 text-xs font-medium text-white hover:bg-[#162024] hover:border-lime/40 transition-colors"
        >
          New Investigation
        </Link>

        {/* Full screen toggle */}
        {onToggleFullScreen ? (
          <button
            type="button"
            aria-label={isFullScreen ? 'Exit Full Screen' : 'Full Screen'}
            onClick={onToggleFullScreen}
            className={`p-1.5 rounded-lg hover:bg-ide-panel transition-colors ${
              isFullScreen ? 'text-lime' : 'text-zinc-400 hover:text-white'
            }`}
            title={isFullScreen ? 'Exit Full Screen' : 'Full Screen'}
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        ) : null}


      </div>
    </header>
  )
}
