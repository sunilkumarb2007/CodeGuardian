import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { codeGuardianApi } from '../api/codeGuardianApi'

export function SearchPalette() {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault()
        setIsOpen((open) => !open)
      }
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50)
      if (query.trim()) {
        performSearch(query)
      }
    } else {
      setQuery('')
      setResults([])
    }
  }, [isOpen])

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (query.trim() && isOpen) {
        performSearch(query)
      } else {
        setResults([])
      }
    }, 300)

    return () => clearTimeout(delayDebounceFn)
  }, [query, isOpen])

  const performSearch = async (q: string) => {
    setLoading(true)
    try {
      const res = await codeGuardianApi.search(q, 'all')
      setResults(res)
      setSelectedIndex(0)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const handleAction = (item: any) => {
    setIsOpen(false)
    if (item.type === 'incident' || item.type === 'memory') {
      // For now navigate to runs page or specific run if known (we don't have runId here yet, so link to /)
      navigate('/')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : prev))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : prev))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      if (results[selectedIndex]) {
        handleAction(results[selectedIndex])
      }
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] px-4 sm:px-0">
      <div className="fixed inset-0 bg-ink-950/80 backdrop-blur-sm" onClick={() => setIsOpen(false)} />
      <div className="relative w-full max-w-2xl overflow-hidden rounded-xl border border-ink-800 bg-ink-900 shadow-2xl">
        <div className="flex items-center border-b border-ink-800 px-4 py-3">
          <svg className="h-5 w-5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            className="flex-1 bg-transparent px-4 py-1 text-white placeholder:text-zinc-500 focus:outline-none font-mono text-sm"
            placeholder="Search repository, service, symbol, failure... (Ctrl+K)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          {loading && <span className="h-4 w-4 animate-spin rounded-full border-2 border-lime border-r-transparent" />}
          <div className="rounded border border-ink-800 bg-ink-950 px-1.5 py-0.5 text-[10px] font-medium text-zinc-400">ESC</div>
        </div>

        <div className="max-h-[60vh] overflow-y-auto p-2">
          {results.length === 0 && query.trim() && !loading && (
            <div className="p-8 text-center text-sm text-zinc-500 font-mono">No results found for "{query}"</div>
          )}
          {results.length === 0 && !query.trim() && (
            <div className="p-8 text-center text-sm text-zinc-500 font-mono">Start typing to search CodeGuardian...</div>
          )}
          {results.length > 0 && (
            <div className="flex flex-col gap-1">
              {results.map((r, i) => (
                <div
                  key={r.id}
                  onClick={() => handleAction(r)}
                  className={`flex cursor-pointer items-center justify-between rounded-lg px-4 py-3 text-sm transition-colors ${
                    i === selectedIndex ? 'bg-ink-800' : 'hover:bg-ink-800/50'
                  }`}
                  onMouseEnter={() => setSelectedIndex(i)}
                >
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-lime uppercase text-[10px] tracking-widest">{r.type}</span>
                      <span className="font-medium text-white">{r.title}</span>
                    </div>
                    <span className="font-mono text-xs text-zinc-400">{r.subtitle}</span>
                  </div>
                  {r.service && (
                    <span className="rounded border border-ink-700 bg-ink-950 px-2 py-1 font-mono text-[10px] text-zinc-300">
                      {r.service}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
