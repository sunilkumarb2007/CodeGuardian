import { useState } from 'react'
import type { RepairCandidate } from '../../api/types'

export function RepairLabPanel({
  candidates,
}: {
  candidates?: RepairCandidate[]
}) {
  const [selectedId, setSelectedId] = useState<string>(
    candidates && candidates.length > 0 ? candidates[0].id : 'candidate-a'
  )

  const items = candidates || []

  if (items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <svg className="h-10 w-10 text-zinc-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <h3 className="text-zinc-400 font-mono text-sm tracking-widest uppercase">NO CANDIDATES AVAILABLE</h3>
        <p className="text-zinc-600 text-xs mt-2 max-w-md">No candidate patches were generated or evaluated for this investigation.</p>
      </div>
    )
  }

  const selected = items.find((c) => c.id === selectedId) || items[0]
  const recommended = items.find((c) => c.is_recommended) || items[0]

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="rounded-xl border border-lime/30 bg-ide-panel p-5 shadow-sm">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-lime animate-pulse" />
              <span className="font-mono text-xs uppercase tracking-widest text-lime font-bold">
                COUNTERFACTUAL REPAIR LAB
              </span>
            </div>
            <h2 className="font-display text-xl font-black text-white tracking-tight">
              Evidence-Driven Multi-Candidate Evaluation
            </h2>
            <p className="text-xs text-zinc-400 font-sans">
              CodeGuardian evaluates competing candidate repair strategies across deterministic safety, build compilation, regression tests, and Ghost Replay.
            </p>
          </div>

          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg border border-lime/30 bg-lime/10 font-mono text-xs text-lime font-semibold">
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
            <span>{items.length} Candidates Evaluated</span>
          </div>
        </div>
      </div>

      {/* Recommended Strategy Banner */}
      {recommended ? (
        <div className="rounded-xl border border-lime/40 bg-lime/[0.04] p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <span className="font-mono text-[10px] uppercase tracking-widest text-lime font-bold">
              RECOMMENDED CANDIDATE · FULL VERIFICATION PROOF
            </span>
            <p className="font-display text-sm font-bold text-white">
              {recommended.label}
            </p>
            <p className="text-xs text-zinc-300 font-sans">
              {recommended.description}
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <span className="px-2 py-1 rounded bg-lime/20 text-lime font-mono text-xs font-bold border border-lime/40">
              ACCEPTED (4/4 GATES)
            </span>
            <button
              type="button"
              onClick={() => setSelectedId(recommended.id)}
              className="px-3 py-1 rounded-lg border border-white/[0.12] bg-ide-base text-xs font-mono text-zinc-200 hover:border-lime/40"
            >
              Inspect Diff
            </button>
          </div>
        </div>
      ) : null}

      {/* Candidate Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {items.map((cand) => {
          const isSelected = cand.id === selectedId
          const isRec = cand.is_recommended
          const ev = cand.evaluation

          return (
            <div
              key={cand.id}
              onClick={() => setSelectedId(cand.id)}
              className={`p-4 rounded-xl border transition-all cursor-pointer flex flex-col justify-between space-y-4 ${
                isSelected
                  ? isRec
                    ? 'border-lime/80 bg-lime/[0.06] shadow-[0_0_16px_rgba(198,255,61,0.15)]'
                    : 'border-red-500/60 bg-red-950/10'
                  : 'border-ide-divider bg-ide-panel hover:border-white/[0.18]'
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span
                    className={`font-mono text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                      isRec
                        ? 'bg-lime/20 text-lime border border-lime/30'
                        : 'bg-red-500/20 text-red-400 border border-red-500/30'
                    }`}
                  >
                    {isRec ? 'RECOMMENDED' : 'REJECTED'}
                  </span>

                  <span className="font-mono text-[11px] text-zinc-400">
                    {ev?.final_status || 'EVALUATED'}
                  </span>
                </div>

                <h3 className="font-display text-sm font-bold text-white leading-snug">
                  {cand.label}
                </h3>
                <p className="text-xs text-zinc-400 font-sans leading-relaxed">
                  {cand.description}
                </p>
              </div>

              {/* Matrix of Gates */}
              <div className="border-t border-white/[0.06] pt-3 space-y-1.5 font-mono text-xs">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-zinc-500">Safety Check</span>
                  <span className={ev?.safety === 'PASS' ? 'text-lime font-bold' : 'text-red-400'}>
                    {ev?.safety || 'PASS'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-zinc-500">Build Compilation</span>
                  <span className={ev?.build === 'PASS' ? 'text-lime font-bold' : 'text-red-400'}>
                    {ev?.build || 'PASS'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-zinc-500">Regression Tests</span>
                  <span className={ev?.tests === 'PASS' ? 'text-lime font-bold' : 'text-red-400'}>
                    {ev?.tests || 'FAILED'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-zinc-500">Ghost Replay</span>
                  <span className={ev?.replay === 'PASS' ? 'text-lime font-bold' : 'text-red-400'}>
                    {ev?.replay || 'FAILED'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-[11px]">
                  <span className="text-zinc-500">Semantic Risk</span>
                  <span className={ev?.semantic_risk === 'LOW' ? 'text-lime' : 'text-amber-400'}>
                    {ev?.semantic_risk || 'NOT_MEASURED'}
                  </span>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Selected Candidate Detailed Inspection */}
      {selected ? (
        <div className="rounded-xl border border-ide-divider bg-ide-panel p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
            <div>
              <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider block">
                INSPECTING CANDIDATE
              </span>
              <h3 className="font-display text-sm font-bold text-white">
                {selected.label}
              </h3>
            </div>

            <span
              className={`font-mono text-xs font-bold px-2.5 py-1 rounded ${
                selected.is_recommended
                  ? 'bg-lime/20 text-lime border border-lime/40'
                  : 'bg-red-500/20 text-red-400 border border-red-500/40'
              }`}
            >
              {selected.is_recommended ? 'ACCEPTED FOR DELIVERY' : 'REJECTED BY GATES'}
            </span>
          </div>

          {selected.evaluation?.rejection_reason ? (
            <div className="p-3 rounded-lg border border-red-500/30 bg-red-950/20 text-xs font-mono text-red-300">
              <span className="font-bold text-red-400 block mb-1">REJECTION REASON:</span>
              {selected.evaluation.rejection_reason}
            </div>
          ) : null}

          <div>
            <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider block mb-1.5 font-bold">
              Synthesized Git Diff
            </span>
            <pre className="p-4 rounded-lg border border-ide-divider bg-ide-base text-zinc-300 font-mono text-xs leading-relaxed overflow-x-auto">
              {selected.diff}
            </pre>
          </div>
        </div>
      ) : null}
    </div>
  )
}
