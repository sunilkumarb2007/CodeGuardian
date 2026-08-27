import type { ReactNode } from 'react'
import type { Run } from '../../api/types'

export type WorkspaceSection =
  | 'Overview'
  | 'Repository'
  | 'Evidence'
  | 'GhostTrace'
  | 'Memory'
  | 'Investigation'
  | 'Source'
  | 'Patch'
  | 'Replay'
  | 'Validation'
  | 'Delivery'

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
    id: 'Repository',
    label: 'Repository',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
      </svg>
    ),
  },
  {
    id: 'Evidence',
    label: 'Evidence',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
  {
    id: 'GhostTrace',
    label: 'GhostTrace',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
  },
  {
    id: 'Memory',
    label: 'Memory',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
      </svg>
    ),
  },
  {
    id: 'Investigation',
    label: 'Investigation',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
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
  {
    id: 'Patch',
    label: 'Patch',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
    ),
  },
  {
    id: 'Replay',
    label: 'Replay',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    id: 'Validation',
    label: 'Validation',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    id: 'Delivery',
    label: 'Delivery',
    icon: (
      <svg className="h-4 w-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 4H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-2m-4-1v8m0 0l3-3m-3 3L9 8m-5 5h2.586a1 1 0 01.707.293l2.414 2.414a1 1 0 00.707.293h3.172a1 1 0 00.707-.293l2.414-2.414a1 1 0 01.707-.293H20" />
      </svg>
    ),
  },
]

export const CANONICAL_17_STAGES = [
  { id: '01', key: '01_repository', label: 'Repository' },
  { id: '02', key: '02_inspection', label: 'Inspection' },
  { id: '03', key: '03_architecture', label: 'Architecture' },
  { id: '04', key: '04_failure_detection', label: 'Failure Detection' },
  { id: '05', key: '05_evidence', label: 'Evidence' },
  { id: '06', key: '06_ghost_trace', label: 'GhostTrace' },
  { id: '07', key: '07_failure_memory', label: 'Failure Memory' },
  { id: '08', key: '08_investigation', label: 'Investigation' },
  { id: '09', key: '09_patch', label: 'Patch' },
  { id: '10', key: '10_compatibility', label: 'Compatibility' },
  { id: '11', key: '11_replay', label: 'Replay' },
  { id: '12', key: '12_build', label: 'Build' },
  { id: '13', key: '13_tests', label: 'Tests' },
  { id: '14', key: '14_validation', label: 'Validation' },
  { id: '15', key: '15_human_approval', label: 'Human Approval' },
  { id: '16', key: '16_delivery', label: 'Delivery' },
  { id: '17', key: '17_memory_update', label: 'Memory Update' },
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
  return (
    <aside className="w-[195px] shrink-0 border-r border-white/[0.08] bg-[#070A0B] flex flex-col justify-between overflow-y-auto select-none z-20">
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
                      : 'text-zinc-400 hover:text-zinc-200 hover:bg-[#0F1518]'
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
          <p className="font-mono text-[10px] uppercase tracking-widest text-zinc-500 px-2.5 mb-2 font-bold">
            PIPELINE STAGES (17)
          </p>
          <div className="space-y-1 relative pl-1">
            {CANONICAL_17_STAGES.map((stageItem, index) => {
              // Match stage by key or index
              const runStage = run?.stages?.find(
                (s) => s.key === stageItem.key || s.name?.toLowerCase().includes(stageItem.label.toLowerCase()),
              )
              const isActive =
                run?.currentStage === stageItem.key ||
                run?.currentStage?.includes(stageItem.id) ||
                (run?.currentStage === undefined && index === 3) // Default to stage 4 as in reference image if not specified
              const isPassed =
                runStage?.status === 'passed' ||
                runStage?.status === 'completed' ||
                runStage?.status === 'skipped' ||
                (!runStage && index < 3) // Fallback for reference display
              const isFailed = runStage?.status === 'failed' || runStage?.status === 'rejected'

              return (
                <button
                  key={stageItem.id}
                  type="button"
                  onClick={() => {
                    if (onSelectStage) onSelectStage(stageItem.key)
                  }}
                  className={`w-full flex items-center gap-2 px-2 py-1 text-left text-xs font-mono rounded hover:bg-[#0F1518] transition-colors group ${
                    isActive ? 'text-white font-bold bg-[#0F1518]/80' : isPassed ? 'text-zinc-300' : 'text-zinc-500'
                  }`}
                >
                  {/* Status Indicator */}
                  <span className="shrink-0 flex items-center justify-center w-3.5 h-3.5">
                    {isPassed ? (
                      <svg className="w-3.5 h-3.5 text-lime" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : isActive ? (
                      <span className="relative flex h-2.5 w-2.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-lime opacity-75" />
                        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-lime drop-shadow-[0_0_6px_rgba(198,255,61,0.8)]" />
                      </span>
                    ) : isFailed ? (
                      <span className="inline-flex rounded-full h-2.5 w-2.5 bg-red-500" />
                    ) : (
                      <span className="inline-flex rounded-full h-2 w-2 border border-zinc-600" />
                    )}
                  </span>

                  <span className={`text-[11px] truncate ${isActive ? 'text-lime font-bold' : ''}`}>
                    <span className="text-zinc-500 mr-1">{stageItem.id}</span>
                    {stageItem.label}
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      </div>

      {/* Bottom of Sidebar: Theme Switcher */}
      <div className="p-2.5 border-t border-white/[0.08]">
        <div className="flex items-center justify-between px-2.5 py-1.5 rounded-lg border border-white/[0.08] bg-[#0F1518] text-xs text-zinc-300">
          <div className="flex items-center gap-2">
            <svg className="h-3.5 w-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <span>Dark</span>
          </div>
          <svg className="h-3.5 w-3.5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
    </aside>
  )
}
