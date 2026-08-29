import type { ReactNode } from 'react'
import { useState, useEffect } from 'react'
import type { Run } from '../../api/types'
import { getStoredTheme, applyTheme, type ThemeMode } from '../../utils/theme'

export type WorkspaceSection =
  | 'Overview'
  | 'Failure DNA'
  | 'Repair Lab'
  | 'Blast Radius'
  | 'Immunization'
  | 'Failure Lab'
  | 'Capsule'
  | 'Repository'
  | 'Inspection'
  | 'Architecture'
  | 'Failure Detection'
  | 'Evidence'
  | 'GhostTrace'
  | 'Memory'
  | 'Investigation'
  | 'Source'
  | 'Patch'
  | 'Compatibility'
  | 'Replay'
  | 'Build'
  | 'Tests'
  | 'Validation'
  | 'Human Approval'
  | 'Delivery'
  | 'Memory Update'

export const WORKSPACE_NAV_ITEMS: { id: WorkspaceSection; label: string; icon: ReactNode }[] = [
  {
    id: 'Overview',
    label: 'Overview',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    id: 'Failure DNA',
    label: 'Failure DNA',
    icon: (
      <svg className="h-4 w-4 shrink-0 text-lime" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1H17a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
      </svg>
    ),
  },
  {
    id: 'Repair Lab',
    label: 'Repair Lab',
    icon: (
      <svg className="h-4 w-4 shrink-0 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
      </svg>
    ),
  },
  {
    id: 'Blast Radius',
    label: 'Blast Radius',
    icon: (
      <svg className="h-4 w-4 shrink-0 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
  },
  {
    id: 'Immunization',
    label: 'Immunization',
    icon: (
      <svg className="h-4 w-4 shrink-0 text-lime" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    id: 'Failure Lab',
    label: 'Failure Lab',
    icon: (
      <svg className="h-4 w-4 shrink-0 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    id: 'Capsule',
    label: 'Capsule',
    icon: (
      <svg className="h-4 w-4 shrink-0 text-zinc-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
      </svg>
    ),
  },
  {
    id: 'Source',
    label: 'Source',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
      </svg>
    ),
  },
]

export const CANONICAL_17_STAGES: { id: string; key: string; label: string; section: WorkspaceSection }[] = [
  { id: '01', key: '01_repository', label: 'Repository', section: 'Repository' },
  { id: '02', key: '02_inspection', label: 'Inspection', section: 'Inspection' },
  { id: '03', key: '03_architecture', label: 'Architecture', section: 'Architecture' },
  { id: '04', key: '04_failure_detection', label: 'Failure Detection', section: 'Failure Detection' },
  { id: '05', key: '05_evidence', label: 'Evidence', section: 'Evidence' },
  { id: '06', key: '06_ghost_trace', label: 'GhostTrace', section: 'GhostTrace' },
  { id: '07', key: '07_failure_memory', label: 'Failure Memory', section: 'Memory' },
  { id: '08', key: '08_investigation', label: 'Investigation', section: 'Investigation' },
  { id: '09', key: '09_patch', label: 'Patch', section: 'Patch' },
  { id: '10', key: '10_compatibility', label: 'Compatibility', section: 'Compatibility' },
  { id: '11', key: '11_replay', label: 'Replay', section: 'Replay' },
  { id: '12', key: '12_build', label: 'Build', section: 'Build' },
  { id: '13', key: '13_tests', label: 'Tests', section: 'Tests' },
  { id: '14', key: '14_validation', label: 'Validation', section: 'Validation' },
  { id: '15', key: '15_human_approval', label: 'Human Approval', section: 'Human Approval' },
  { id: '16', key: '16_delivery', label: 'Delivery', section: 'Delivery' },
  { id: '17', key: '17_memory_update', label: 'Memory Update', section: 'Memory Update' },
]

export function IDESidebar({
  activeSection,
  onSelectSection,
  run,
  onSelectStage,
}: {
  activeSection: WorkspaceSection
  onSelectSection: (s: WorkspaceSection) => void
  run?: Run
  onSelectStage?: (stageKey: string) => void
}) {
  const [themeMode, setThemeMode] = useState<ThemeMode>('dark')

  useEffect(() => {
    setThemeMode(getStoredTheme())
  }, [])

  const handleCycleTheme = () => {
    const next: ThemeMode = themeMode === 'dark' ? 'light' : themeMode === 'light' ? 'system' : 'dark'
    setThemeMode(next)
    applyTheme(next)
  }

  return (
    <aside
      aria-label="Pipeline navigation"
      className="w-[210px] xl:w-[225px] shrink-0 border-r border-ide-divider bg-ide-base flex flex-col justify-between overflow-y-auto select-none z-20"
    >
      <div className="py-3 px-2 space-y-5">
        {/* Workspace Navigation */}
        <div>
          <p className="font-mono text-[10px] uppercase tracking-widest text-zinc-500 px-2.5 mb-1.5 font-bold">
            WORKSPACE
          </p>
          <nav className="space-y-0.5">
            {WORKSPACE_NAV_ITEMS.map((item) => {
              const isActive = activeSection === item.id
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onSelectSection(item.id)}
                  className={`w-full flex items-center gap-2.5 px-2.5 py-1.5 text-xs rounded-lg transition-all text-left font-medium ${
                    isActive
                      ? 'bg-lime text-black font-semibold shadow-sm'
                      : 'text-zinc-400 hover:text-zinc-200 hover:bg-ide-panel'
                  }`}
                >
                  <span className={isActive ? 'text-black' : 'text-zinc-400'}>{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* 17 Pipeline Stages */}
        <div>
          <div className="flex items-center justify-between px-2.5 mb-2">
            <p className="font-mono text-[10px] uppercase tracking-widest text-zinc-500 font-bold">
              PIPELINE STAGES
            </p>
            <span className="text-[10px] font-mono text-zinc-500 font-bold">(17)</span>
          </div>
          <div className="space-y-0.5 relative pl-1">
            {CANONICAL_17_STAGES.map((stageItem) => {
              const stageBaseName = stageItem.key.replace(/^\d+_/, '')
              const runStage = run?.stages?.find(
                (s) =>
                  s.key === stageItem.key ||
                  s.key === stageBaseName ||
                  s.key.replace(/^\d+_/, '') === stageBaseName ||
                  s.name?.toLowerCase() === stageItem.label.toLowerCase() ||
                  s.name?.toLowerCase().replace(/[_\s]+/g, '') === stageItem.label.toLowerCase().replace(/[_\s]+/g, '')
              )
              
              const isTerminalRun =
                run?.status === 'completed' ||
                run?.status === 'failed' ||
                run?.status === 'rejected' ||
                run?.status === 'baseline_failure_not_reproduced'

              const status = runStage?.status ?? (isTerminalRun ? 'passed' : 'pending')
              const isPassed = status === 'passed' || status === 'completed' || status === 'skipped'
              const isFailed = status === 'failed' || status === 'rejected'
              const isWaiting = status === 'waiting_for_approval'
              const isRunning = !isTerminalRun && (status === 'running' || (run?.currentStage === stageBaseName && !isPassed && !isFailed && !isWaiting))

              const isSelected = activeSection === stageItem.section || activeSection.toLowerCase() === stageItem.label.toLowerCase()

              return (
                <button
                  key={stageItem.id}
                  type="button"
                  onClick={() => {
                    if (onSelectStage) {
                      onSelectStage(stageItem.key)
                    } else {
                      onSelectSection(stageItem.section)
                    }
                  }}
                  className={`w-full flex items-center gap-2 px-2 py-1 text-left text-xs font-mono rounded transition-colors group ${
                    isSelected ? 'text-white font-bold bg-ide-panel border border-ide-divider' : isPassed ? 'text-zinc-300 hover:bg-ide-panel/60' : 'text-zinc-500 hover:bg-ide-panel/40'
                  }`}
                >
                  {/* Status Indicator */}
                  <span className="shrink-0 flex items-center justify-center w-3.5 h-3.5">
                    {isPassed ? (
                      <svg className="w-3.5 h-3.5 text-lime" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : isRunning ? (
                      <span className="relative flex h-2.5 w-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-lime opacity-75" />
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-lime drop-shadow-[0_0_6px_rgba(198,255,61,0.8)]" />
                      </span>
                    ) : isWaiting ? (
                      <span className="relative flex h-2.5 w-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-400" />
                      </span>
                    ) : isFailed ? (
                      <span className="inline-flex rounded-full h-2.5 w-2.5 bg-red-500" />
                    ) : (
                      <span className="inline-flex rounded-full h-2 w-2 border border-zinc-600" />
                    )}
                  </span>

                  <span className={`text-[11px] truncate ${isRunning ? 'text-lime font-bold' : isFailed ? 'text-red-400' : ''}`}>
                    <span className="text-zinc-500 mr-1.5">{stageItem.id}</span>
                    <span>{stageItem.label}</span>
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Bottom of Sidebar: 3-State Theme Switcher */}
      <div className="p-2.5 border-t border-ide-divider">
        <button
          type="button"
          onClick={handleCycleTheme}
          className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg border border-ide-divider bg-ide-panel text-xs text-zinc-300 hover:text-white hover:border-white/[0.2] transition-colors"
          title="Toggle Dark / Light / System Theme"
        >
          <div className="flex items-center gap-2">
            <svg className="h-3.5 w-3.5 text-lime" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <span className="capitalize">{themeMode} Theme</span>
          </div>
          <span className="font-mono text-[10px] text-lime font-semibold uppercase">Toggle ▾</span>
        </button>
      </div>
    </aside>
  )
}
