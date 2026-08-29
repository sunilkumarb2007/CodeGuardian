import { useState } from 'react'
import type { GhostTrace, Incident } from '../../api/types'

export function TraceOverviewPanel({
  trace,
  incident: _incident,
}: {
  trace?: GhostTrace
  incident?: Incident
}) {
  const nodes = trace?.nodes || []
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(nodes.length > 0 ? nodes[0].id : null)

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || nodes[0]

  if (!nodes || nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <svg className="h-10 w-10 text-zinc-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
        <h2 className="text-zinc-300 font-mono text-sm tracking-widest uppercase">NO CAUSAL CHAIN AVAILABLE</h2>
        <p className="text-zinc-500 text-xs mt-2 max-w-md">The GhostTrace engine has not yet established a confident causality chain for this failure, or the run has not progressed far enough.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        <div className="lg:col-span-5 rounded-xl border border-ide-divider bg-ide-panel p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-zinc-300">
                Causal Chain
              </h3>
            </div>

            <div className="space-y-2 relative">
              {nodes.map((node, index) => {
                const isSelected = selectedNodeId === node.id
                return (
                  <div key={node.id} className="relative group">
                    {index !== 0 && (
                      <div className="absolute left-4 -top-3 h-3 w-px bg-zinc-800" />
                    )}
                    <button
                      onClick={() => setSelectedNodeId(node.id)}
                      className={`w-full flex items-center justify-between p-2.5 rounded-lg border transition-all text-left ${
                        isSelected
                          ? 'bg-[#151D21] border-zinc-700 shadow-sm'
                          : 'bg-ide-base border-transparent hover:border-zinc-800 hover:bg-[#0A0D0F]'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {node.isRootCause ? (
                           <svg className="h-4 w-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                          </svg>
                        ) : node.isSymptom ? (
                          <svg className="h-4 w-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        ) : (
                          <svg className="h-4 w-4 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        )}
                        <span className="text-xs font-semibold text-white">{node.label}</span>
                      </div>
                    </button>
                  </div>
                )
              })}
            </div>
          </div>

          {trace?.rootCause && (
            <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between text-xs">
              <span className="text-zinc-400 text-[11px]">
                Root cause candidate: <span className="text-zinc-200">{trace.rootCause}</span>
              </span>
            </div>
          )}
        </div>

        <div className="lg:col-span-7 rounded-xl border border-ide-divider bg-ide-panel p-5 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
              <h3 className="font-display text-sm font-bold text-white tracking-wide">
                {selectedNode?.label || 'Node Details'}
              </h3>
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                selectedNode?.isRootCause ? 'bg-red-500/20 text-red-400 border border-red-500/40' :
                selectedNode?.isSymptom ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' :
                'bg-zinc-800 text-zinc-300'
              }`}>
                {selectedNode?.isRootCause ? 'ROOT CAUSE' : selectedNode?.isSymptom ? 'SYMPTOM' : 'TRACE NODE'}
              </span>
            </div>

            <div>
              <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider block mb-1.5 font-bold">
                Detail
              </span>
              <pre className="p-3 rounded-lg border border-ide-divider bg-ide-base text-zinc-300 font-mono text-[11px] leading-relaxed overflow-x-auto">
                {selectedNode?.detail || 'No detail provided.'}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
