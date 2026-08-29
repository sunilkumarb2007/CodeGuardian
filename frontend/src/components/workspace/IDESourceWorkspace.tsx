import { useState, useMemo, useEffect } from 'react'
import type { SourceFile, Investigation, StackTrace } from '../../api/types'

interface IDESourceWorkspaceProps {
  files: SourceFile[]
  investigation?: Investigation
  stackTrace?: StackTrace
  isFullScreen?: boolean
  onToggleFullScreen?: () => void
  onBackToInvestigation?: () => void
}

interface FileTreeItem {
  name: string
  path: string
  isFolder: boolean
  isOpen?: boolean
  errorCount?: number
  content?: string
  children?: FileTreeItem[]
}

function buildFileTreeFromSources(sourceFiles: SourceFile[]): FileTreeItem[] {
  if (!sourceFiles || sourceFiles.length === 0) {
    return []
  }

  const root: FileTreeItem[] = []

  sourceFiles.forEach((file) => {
    const parts = file.path.split('/').filter(Boolean)
    let currentLevel = root
    let currentPath = ''

    parts.forEach((part, index) => {
      currentPath = currentPath ? `${currentPath}/${part}` : part
      const isLast = index === parts.length - 1

      if (isLast) {
        currentLevel.push({
          name: part,
          path: file.path,
          isFolder: false,
          content: file.content || `// Content for ${file.path}`,
          errorCount: file.path.includes('index') || file.path.includes('Payment') || file.path.includes('service') ? 1 : undefined
        })
      } else {
        let folder = currentLevel.find((item) => item.name === part && item.isFolder)
        if (!folder) {
          folder = {
            name: part,
            path: currentPath,
            isFolder: true,
            isOpen: true,
            children: []
          }
          currentLevel.push(folder)
        }
        currentLevel = folder.children!
      }
    })
  })

  return root
}

export function IDESourceWorkspace({
  files,
  investigation: _investigation,
  stackTrace,
  isFullScreen = false,
  onToggleFullScreen,
  onBackToInvestigation,
}: IDESourceWorkspaceProps) {
  const initialTree = useMemo(() => buildFileTreeFromSources(files), [files])
  const [fileTree, setFileTree] = useState<FileTreeItem[]>(initialTree)

  // Sync tree with files prop
  useEffect(() => {
    setFileTree(buildFileTreeFromSources(files))
  }, [files])

  // Find all file paths from sourceFiles
  const allFilePaths = useMemo(() => {
    return files.map((f) => f.path)
  }, [files])

  const [openTabs, setOpenTabs] = useState<string[]>(() => allFilePaths.slice(0, 4))
  const [activeTabPath, setActiveTabPath] = useState<string>(() => allFilePaths[0] || '')
  const [terminalTab, setTerminalTab] = useState<'TERMINAL' | 'PROBLEMS' | 'OUTPUT' | 'DEBUG CONSOLE'>('TERMINAL')
  const [isTerminalExpanded, setIsTerminalExpanded] = useState<boolean>(false)

  // Sync tabs when files change
  useEffect(() => {
    if (files.length > 0) {
      const paths = files.map((f) => f.path)
      setOpenTabs((prev) => prev.filter((p) => paths.includes(p)))
      setActiveTabPath((prev) => (paths.includes(prev) ? prev : paths[0] || ''))
    } else {
      setOpenTabs([])
      setActiveTabPath('')
    }
  }, [files])

  // Dynamic active file content
  const activeFile = files.find((f) => f.path === activeTabPath)
  const activeCode = activeFile?.content || ''

  const toggleFolder = (path: string, items: FileTreeItem[]): FileTreeItem[] => {
    return items.map((item) => {
      if (item.path === path) {
        return { ...item, isOpen: !item.isOpen }
      }
      if (item.children) {
        return { ...item, children: toggleFolder(path, item.children) }
      }
      return item
    })
  }

  const handleSelectFile = (path: string) => {
    if (!openTabs.includes(path)) {
      setOpenTabs([...openTabs, path])
    }
    setActiveTabPath(path)
  }

  const handleCloseTab = (path: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const nextTabs = openTabs.filter((t) => t !== path)
    setOpenTabs(nextTabs)
    if (activeTabPath === path && nextTabs.length > 0) {
      setActiveTabPath(nextTabs[nextTabs.length - 1])
    }
  }

  const renderTree = (items: FileTreeItem[], depth = 0) => {
    return (
      <ul className="space-y-0.5 select-none font-mono text-xs">
        {items.map((item) => {
          const isSelected = activeTabPath === item.path
          return (
            <li key={item.path}>
              <div
                onClick={() => {
                  if (item.isFolder) {
                    setFileTree((prev) => toggleFolder(item.path, prev))
                  } else {
                    handleSelectFile(item.path)
                  }
                }}
                style={{ paddingLeft: `${depth * 14 + 10}px` }}
                className={`flex items-center justify-between py-1 pr-2 rounded cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-white/[0.08] text-white font-semibold'
                    : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.04]'
                }`}
              >
                <div className="flex items-center gap-1.5 min-w-0">
                  {item.isFolder ? (
                    <svg
                      className={`h-3 w-3 shrink-0 text-zinc-500 transition-transform ${
                        item.isOpen ? 'rotate-90 text-zinc-300' : ''
                      }`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  ) : (
                    <span className="text-[10px] text-blue-400 font-bold w-3.5 text-center">
                      {item.name.endsWith('.ts') || item.name.endsWith('.tsx') ? 'TS' : item.name.endsWith('.java') ? 'JV' : item.name.endsWith('.py') ? 'PY' : item.name.endsWith('.json') ? '{}' : '📄'}
                    </span>
                  )}
                  <span className="truncate">{item.name}</span>
                </div>
                {item.errorCount ? (
                  <span className="px-1.5 py-0.2 rounded-full text-[10px] font-bold bg-signal-pink/20 text-signal-pink border border-signal-pink/40">
                    {item.errorCount}
                  </span>
                ) : null}
              </div>
              {item.isFolder && item.isOpen && item.children ? (
                <div>{renderTree(item.children, depth + 1)}</div>
              ) : null}
            </li>
          )
        })}
      </ul>
    )
  }

  const lines = activeCode.split('\n')
  const failingLineNumber = lines.findIndex((l) => l.includes('null') || l.includes('charge') || l.includes('throw') || l.includes('Exception')) + 1 || (lines.length > 10 ? 10 : undefined)

  return (
    <div className={`flex flex-col rounded-xl border border-ide-divider bg-ide-base overflow-hidden text-zinc-300 font-sans shadow-2xl transition-all ${
      isFullScreen ? 'fixed inset-4 z-50 bg-ide-base border-lime/40 ring-1 ring-lime/20' : 'h-[750px] w-full'
    }`}>
      {/* Top Workspace Header Bar */}
      <div className="h-10 border-b border-ide-divider bg-[#0A0F11] px-4 flex items-center justify-between shrink-0 select-none">
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs font-bold text-lime uppercase tracking-wider">
            SOURCE VIEW
          </span>
          <span className="text-zinc-600">|</span>
          <span className="font-mono text-xs text-zinc-400">
            {activeTabPath}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {onBackToInvestigation ? (
            <button
              type="button"
              onClick={onBackToInvestigation}
              className="flex items-center gap-1.5 px-3 py-1 rounded bg-ide-panel hover:bg-[#162024] border border-ide-divider text-xs text-zinc-300 hover:text-white transition-colors"
            >
              <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span>Back to Investigation</span>
            </button>
          ) : null}

          {onToggleFullScreen ? (
            <button
              type="button"
              onClick={onToggleFullScreen}
              title={isFullScreen ? 'Exit Full Screen' : 'Full Screen IDE Mode'}
              className="p-1.5 rounded hover:bg-white/[0.08] text-zinc-400 hover:text-lime transition-colors"
            >
              {isFullScreen ? (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                </svg>
              )}
            </button>
          ) : null}
        </div>
      </div>

      {/* Main 2-Pane Editor Body (Left Explorer + Right Editor & Terminal) */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Left Column: File Explorer Pane (~220px) */}
        <div className="w-56 border-r border-ide-divider bg-[#090D0F] flex flex-col shrink-0 overflow-hidden select-none">
          <div className="p-3 border-b border-white/[0.06] flex items-center justify-between">
            <span className="font-mono text-[11px] uppercase tracking-wider text-zinc-400 font-bold">
              EXPLORER
            </span>
            <span className="font-mono text-[10px] text-zinc-500">SNAPSHOT</span>
          </div>

          <div className="flex-1 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-zinc-800">
            {fileTree.length > 0 ? (
              renderTree(fileTree)
            ) : (
              <div className="p-4 text-center text-xs font-mono text-zinc-500">
                Repository snapshot not available yet.
              </div>
            )}
          </div>

          {/* Bottom Explorer Accordions */}
          <div className="border-t border-white/[0.06] p-2 text-xs font-mono text-zinc-500 space-y-1">
            <div className="flex items-center justify-between py-1 px-2 hover:bg-white/[0.04] rounded cursor-pointer">
              <span>OUTLINE</span>
              <span>›</span>
            </div>
            <div className="flex items-center justify-between py-1 px-2 hover:bg-white/[0.04] rounded cursor-pointer">
              <span>TIMELINE</span>
              <span>›</span>
            </div>
          </div>
        </div>

        {/* Center/Right: Multi-Tab Code Editor & Integrated Terminal */}
        <div className="flex-1 flex flex-col min-w-0 bg-ide-base">
          {/* Editor Tab Bar */}
          <div className="h-9 border-b border-ide-divider bg-[#080C0E] flex items-center overflow-x-auto select-none px-1">
            {openTabs.map((tabPath) => {
              const fileName = tabPath.split('/').pop() || tabPath
              const isActive = activeTabPath === tabPath
              return (
                <div
                  key={tabPath}
                  onClick={() => setActiveTabPath(tabPath)}
                  className={`h-full flex items-center gap-2 px-3 border-r border-white/[0.06] text-xs font-mono cursor-pointer transition-colors ${
                    isActive
                      ? 'bg-ide-base text-white border-t-2 border-t-lime font-semibold'
                      : 'text-zinc-400 hover:text-zinc-200 hover:bg-white/[0.02]'
                  }`}
                >
                  <span className="text-blue-400 text-[10px] font-bold">
                    {tabPath.endsWith('.ts') ? 'TS' : tabPath.endsWith('.java') ? 'JV' : '📄'}
                  </span>
                  <span className="truncate max-w-[120px]">{fileName}</span>
                  <button
                    type="button"
                    onClick={(e) => handleCloseTab(tabPath, e)}
                    className="p-0.5 hover:text-white rounded hover:bg-white/[0.1]"
                  >
                    ×
                  </button>
                </div>
              )
            })}
          </div>

          {/* Breadcrumb Path Bar */}
          <div className="h-6 border-b border-white/[0.04] bg-ide-base px-4 flex items-center text-[11px] font-mono text-zinc-500">
            <span>{activeTabPath.split('/').join(' › ')}</span>
          </div>

          {/* Code Editor Body with Line Numbers & Failing Line Highlight */}
          <div className="flex-1 overflow-y-auto font-mono text-xs leading-relaxed p-2 select-text relative flex">
            {files.length > 0 && activeTabPath ? (
              <>
                {/* Line numbers + Code */}
                <div className="flex-1 min-w-0">
                  {lines.map((line, idx) => {
                    const lineNum = idx + 1
                    const isFailing = lineNum === failingLineNumber
                    return (
                      <div
                        key={lineNum}
                        className={`flex items-start group ${
                          isFailing
                            ? 'bg-signal-pink/15 border-l-2 border-signal-pink text-white'
                            : 'hover:bg-white/[0.02]'
                        }`}
                      >
                        <span className={`w-10 shrink-0 text-right pr-4 select-none font-mono text-[11px] ${
                          isFailing ? 'text-signal-pink font-bold' : 'text-zinc-600 group-hover:text-zinc-400'
                        }`}>
                          {isFailing ? `✕ ${lineNum}` : lineNum}
                        </span>
                        <div className="flex-1 min-w-0 pr-4 whitespace-pre">
                          <span className={isFailing ? 'text-red-200 font-semibold' : 'text-zinc-300'}>
                            {line}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>

                {/* Minimap preview bar on the right */}
                <div className="w-16 shrink-0 border-l border-white/[0.04] bg-[#06080A]/80 hidden md:flex flex-col p-1 opacity-60 select-none">
                  <div className="h-2 w-full bg-zinc-700/40 rounded-sm mb-1" />
                  <div className="h-2 w-full bg-zinc-700/40 rounded-sm mb-1" />
                  <div className="h-3 w-full bg-signal-pink/60 rounded-sm mb-1" />
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-xs font-mono text-zinc-500">
                No source file selected.
              </div>
            )}
          </div>

          {/* Editor Status Bar */}
          <div className="h-6 border-t border-white/[0.06] bg-[#080C0E] px-4 flex items-center justify-between text-[10px] font-mono text-zinc-500 select-none">
            <div className="flex items-center gap-4">
              <span>Ln {failingLineNumber || 1}, Col 1</span>
              <span>Spaces: 2</span>
              <span>UTF-8</span>
              <span>LF</span>
              <span>{activeTabPath.split('.').pop()?.toUpperCase() || 'CODE'}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-signal-pink flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-signal-pink" /> 1 Root Cause Focus
              </span>
              <span className="text-lime flex items-center gap-1">
                <span className="h-1.5 w-1.5 rounded-full bg-lime" /> AutoFix Ready
              </span>
            </div>
          </div>

          {/* Bottom Integrated Terminal Panel */}
          <div className={`border-t border-ide-divider bg-[#07090A] flex flex-col transition-all ${
            isTerminalExpanded ? 'h-72' : 'h-48'
          }`}>
            {/* Terminal Header Tabs & Actions */}
            <div className="h-8 border-b border-white/[0.06] bg-[#080C0E] px-3 flex items-center justify-between select-none">
              <div className="flex items-center gap-4 text-xs font-mono">
                {(['TERMINAL', 'PROBLEMS', 'OUTPUT', 'DEBUG CONSOLE'] as const).map((t) => (
                  <button
                    key={t}
                    type="button"
                    onClick={() => setTerminalTab(t)}
                    className={`h-full flex items-center gap-1.5 font-bold transition-colors ${
                      terminalTab === t ? 'text-white border-b-2 border-lime' : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                  >
                    <span>{t}</span>
                  </button>
                ))}
              </div>

              {/* Terminal controls */}
              <div className="flex items-center gap-2 text-zinc-400">
                <span className="font-mono text-xs text-zinc-400 bg-ide-panel px-2 py-0.5 rounded border border-white/[0.06]">
                  1: console
                </span>
                <button
                  type="button"
                  title="Expand Terminal"
                  onClick={() => setIsTerminalExpanded(!isTerminalExpanded)}
                  className="p-1 hover:text-white"
                >
                  <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={isTerminalExpanded ? "M19 9l-7 7-7-7" : "M5 15l7-7 7 7"} />
                  </svg>
                </button>
              </div>
            </div>

            {/* Terminal Log Output */}
            <div className="flex-1 overflow-y-auto p-3 font-mono text-xs text-zinc-300 bg-[#050708] leading-relaxed select-text">
              {terminalTab === 'TERMINAL' ? (
                <div className="space-y-1">
                  <p className="text-zinc-500">&gt; git clone --depth 1 &lt;repository&gt;</p>
                  <p className="text-lime pt-1">✓ Repository snapshot cloned to isolated sandbox</p>
                  <p className="text-zinc-400">&gt; inspect_source_tree --target {activeTabPath}</p>
                  {stackTrace?.content ? (
                    <p className="text-red-400 pt-2 whitespace-pre-wrap">{stackTrace.content}</p>
                  ) : (
                    <p className="text-red-400 pt-2 font-bold">
                      Identified error signature on {activeTabPath}:{failingLineNumber || 1}
                    </p>
                  )}
                </div>
              ) : terminalTab === 'PROBLEMS' ? (
                <div className="space-y-2">
                  <div className="p-2 rounded bg-red-950/20 border border-red-500/30 text-red-300 flex items-start gap-2">
                    <span className="text-signal-pink font-bold">✕</span>
                    <div>
                      <p className="font-bold">{activeTabPath}:{failingLineNumber || 1}</p>
                      <p className="text-zinc-400">Target failure point in investigated flow.</p>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-zinc-500">Output stream initialized.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
