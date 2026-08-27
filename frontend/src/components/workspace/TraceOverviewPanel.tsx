import { useState } from 'react'
import type { GhostTrace, Incident } from '../../api/types'

interface ServiceNode {
  id: string
  name: string
  duration: string
  status: 'success' | 'failure' | 'timeout'
  icon: 'globe' | 'cube' | 'database'
  operation?: string
  spanId?: string
  error?: string
  tags?: Record<string, string>
}

const DEFAULT_NODES: ServiceNode[] = [
  {
    id: 'gateway',
    name: 'Gateway',
    duration: '142ms',
    status: 'success',
    icon: 'globe',
    operation: 'GET /',
    spanId: '1a9e32408bc81a21',
    tags: { env: 'development', version: '1.18.2', region: 'local', host: 'macos' },
  },
  {
    id: 'order-service',
    name: 'Order Service',
    duration: '87ms',
    status: 'success',
    icon: 'cube',
    operation: 'GET /api/orders',
    spanId: '2c8f41509cd92b32',
    tags: { env: 'development', version: '1.18.2', region: 'local', host: 'macos' },
  },
  {
    id: 'payment-service',
    name: 'Payment Service',
    duration: '17ms',
    status: 'failure',
    icon: 'cube',
    operation: 'POST /payments/charge',
    spanId: '4b4d05950bc9045a470d62',
    error: 'NullPointerException: Cannot read properties of null\nat PaymentService.charge(PaymentService.java:82)\n...',
    tags: { env: 'development', version: '1.18.2', region: 'local', host: 'macos' },
  },
  {
    id: 'postgres',
    name: 'PostgreSQL',
    duration: 'TIMEOUT',
    status: 'timeout',
    icon: 'database',
    operation: 'Query Execution: SELECT * FROM payment_records WHERE id = $1',
    spanId: '5d6e71801ef03c44',
    error: 'QueryTimeoutException: Statement cancelled due to timeout (3000ms)',
    tags: { env: 'development', version: '17.2', region: 'local', host: 'macos' },
  },
]

export function TraceOverviewPanel({
  trace: _trace,
  incident,
}: {
  trace?: GhostTrace
  incident?: Incident
}) {
  const [selectedNodeId, setSelectedNodeId] = useState<string>('payment-service')

  // Merge dynamic trace nodes from backend if available
  const nodes = DEFAULT_NODES.map((n) => {
    if (n.id === 'payment-service' && incident?.service) {
      return {
        ...n,
        name: incident.service === 'payment-service' ? 'Payment Service' : incident.service,
        error: incident.summary || n.error,
      }
    }
    return n
  })

  const selectedNode = nodes.find((n) => n.id === selectedNodeId) || nodes[2]

  return (
    <div className="space-y-4">
      {/* Upper Grid: Service Map (Left) + Detail (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left: Service Map Card */}
        <div className="lg:col-span-5 rounded-xl border border-white/[0.08] bg-[#0F1518] p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-zinc-300">
                Service map
              </h3>
            </div>

            {/* Vertical Connected Service Nodes */}
            <div className="space-y-2 relative">
              {nodes.map((node, index) => {
                const isSelected = selectedNodeId === node.id
                const isFailure = node.status === 'failure' || node.status === 'timeout'

                return (
                  <div key={node.id} className="flex flex-col items-center">
                    <button
                      type="button"
                      onClick={() => setSelectedNodeId(node.id)}
                      className={`w-full flex items-center justify-between px-3.5 py-2 rounded-lg border transition-all text-left ${
                        isSelected
                          ? isFailure
                            ? 'border-red-500/80 bg-red-950/20 shadow-[0_0_12px_rgba(239,68,68,0.2)]'
                            : 'border-lime/80 bg-lime/10 shadow-[0_0_12px_rgba(198,255,61,0.2)]'
                          : isFailure
                            ? 'border-red-500/40 bg-[#0B1012] hover:border-red-500/60'
                            : 'border-white/[0.08] bg-[#0B1012] hover:border-white/[0.18]'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        {/* Icon */}
                        {node.icon === 'globe' ? (
                          <svg className="h-4 w-4 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
                          </svg>
                        ) : node.icon === 'cube' ? (
                          <svg className={`h-4 w-4 ${isFailure ? 'text-red-400' : 'text-zinc-400'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                          </svg>
                        ) : (
                          <svg className="h-4 w-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                          </svg>
                        )}
                        <span className="text-xs font-semibold text-white">{node.name}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <span
                          className={`font-mono text-[11px] ${
                            node.status === 'timeout'
                              ? 'text-red-400 font-bold tracking-wider'
                              : 'text-zinc-400'
                          }`}
                        >
                          {node.duration}
                        </span>

                        {node.status === 'success' ? (
                          <svg className="h-3.5 w-3.5 text-lime" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <span className="flex h-4 w-4 items-center justify-center rounded-full bg-red-500/20 text-red-400 font-mono text-[10px] font-bold">
                            !
                          </span>
                        )}
                      </div>
                    </button>

                    {/* Connecting Arrow */}
                    {index < nodes.length - 1 && (
                      <div className="py-1 text-zinc-600 text-xs select-none">↓</div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Root Cause Candidate Footer */}
          <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between text-xs">
            <span className="text-zinc-400 text-[11px]">
              Root cause candidate: <span className="text-zinc-200">PostgreSQL timeout / null repository result</span>
            </span>
            <span className="font-mono text-lime font-bold text-xs shrink-0 pl-2">
              Confidence 93%
            </span>
          </div>
        </div>

        {/* Right: Trace Detail Panel */}
        <div className="lg:col-span-7 rounded-xl border border-white/[0.08] bg-[#0F1518] p-5 flex flex-col justify-between">
          <div className="space-y-4">
            {/* Detail Header */}
            <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
              <h3 className="font-display text-sm font-bold text-white tracking-wide">
                {selectedNode.name}
              </h3>
              <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded ${
                selectedNode.status === 'success'
                  ? 'bg-lime/20 text-lime border border-lime/30'
                  : 'bg-red-500/20 text-red-400 border border-red-500/40'
              }`}>
                {selectedNode.status === 'success' ? 'HEALTHY' : 'FAILURE'}
              </span>
            </div>

            {/* Key-Value Details */}
            <div className="grid grid-cols-2 gap-y-2 text-xs font-mono">
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Duration</span>
                <span className="text-zinc-200">{selectedNode.duration}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Timestamp</span>
                <span className="text-zinc-200">2026-08-26 13:34:20.699105+05:30</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Span ID</span>
                <span className="text-zinc-300">{selectedNode.spanId || '4b4d05950bc9045a470d62'}</span>
              </div>
              <div>
                <span className="text-zinc-500 block text-[10px] uppercase">Service</span>
                <span className="text-zinc-200">{selectedNode.id}</span>
              </div>
              <div className="col-span-2">
                <span className="text-zinc-500 block text-[10px] uppercase">Operation</span>
                <span className="text-zinc-200">{selectedNode.operation || 'POST /payments/charge'}</span>
              </div>
            </div>

            {/* Error Sub-box */}
            <div>
              <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider block mb-1.5 font-bold">
                Error
              </span>
              <pre className="p-3 rounded-lg border border-red-500/20 bg-[#070A0B] text-red-400 font-mono text-[11px] leading-relaxed overflow-x-auto">
                {selectedNode.error || 'No runtime exception recorded on this node.'}
              </pre>
            </div>

            {/* Tags */}
            <div>
              <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider block mb-1.5 font-bold">
                Tags
              </span>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(selectedNode.tags || {}).map(([key, val]) => (
                  <span
                    key={key}
                    className="px-2 py-0.5 rounded border border-white/[0.08] bg-[#070A0B] font-mono text-[10px] text-zinc-300"
                  >
                    <span className="text-zinc-500">{key}:</span> {val}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Lower Grid: Timeline (Left) + Top Errors (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left: Timeline */}
        <div className="lg:col-span-8 rounded-xl border border-white/[0.08] bg-[#0F1518] p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-zinc-300">
                Timeline
              </h3>
              <div className="flex items-center gap-1 rounded bg-[#070A0B] border border-white/[0.08] px-2 py-0.5 text-[10px] font-mono text-zinc-400 cursor-pointer">
                <span>Events</span>
                <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>
          </div>

          {/* Time axis header */}
          <div className="grid grid-cols-5 text-[10px] font-mono text-zinc-500 border-b border-white/[0.06] pb-1.5 mb-2.5 text-right">
            <span>13:34:20.640</span>
            <span>13:34:20.660</span>
            <span>13:34:20.680</span>
            <span>13:34:20.700</span>
            <span>13:34:20.720</span>
          </div>

          {/* Timeline rows */}
          <div className="space-y-2 text-xs font-mono">
            {/* Gateway */}
            <div className="flex items-center gap-3">
              <div className="w-28 flex items-center gap-1.5 shrink-0 text-zinc-300 text-[11px]">
                <svg className="h-3 w-3 text-lime shrink-0" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="truncate">Gateway</span>
              </div>
              <span className="w-28 text-[10px] text-zinc-500 truncate">GET /</span>
              <div className="flex-1 bg-[#070A0B] h-4 rounded overflow-hidden relative flex items-center">
                <div className="h-full bg-lime rounded flex items-center justify-end px-1 text-[10px] font-bold text-black" style={{ width: '85%' }}>
                  142ms
                </div>
              </div>
            </div>

            {/* Order Service */}
            <div className="flex items-center gap-3">
              <div className="w-28 flex items-center gap-1.5 shrink-0 text-zinc-300 text-[11px]">
                <svg className="h-3 w-3 text-lime shrink-0" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="truncate">Order Service</span>
              </div>
              <span className="w-28 text-[10px] text-zinc-500 truncate">GET /api/orders</span>
              <div className="flex-1 bg-[#070A0B] h-4 rounded overflow-hidden relative flex items-center">
                <div className="h-full bg-lime/90 rounded flex items-center justify-end px-1 text-[10px] font-bold text-black" style={{ width: '58%' }}>
                  87ms
                </div>
              </div>
            </div>

            {/* Payment Service */}
            <div className="flex items-center gap-3">
              <div className="w-28 flex items-center gap-1.5 shrink-0 text-red-400 text-[11px]">
                <span className="flex h-3 w-3 items-center justify-center rounded-full bg-red-500/20 text-[9px] font-bold">
                  !
                </span>
                <span className="truncate">Payment Service</span>
              </div>
              <span className="w-28 text-[10px] text-zinc-500 truncate">POST /payments/charge</span>
              <div className="flex-1 bg-[#070A0B] h-4 rounded overflow-hidden relative flex items-center">
                <div className="h-full bg-red-500 rounded flex items-center justify-end px-1 text-[10px] font-bold text-white" style={{ width: '22%' }}>
                  17ms
                </div>
              </div>
            </div>

            {/* PostgreSQL */}
            <div className="flex items-center gap-3">
              <div className="w-28 flex items-center gap-1.5 shrink-0 text-red-400 text-[11px]">
                <span className="flex h-3 w-3 items-center justify-center rounded-full bg-red-500/20 text-[9px] font-bold">
                  !
                </span>
                <span className="truncate">PostgreSQL</span>
              </div>
              <span className="w-28 text-[10px] text-zinc-500 truncate">Query Execution</span>
              <div className="flex-1 bg-[#070A0B] h-4 rounded overflow-hidden relative flex items-center">
                <div
                  className="h-full bg-red-950 border border-red-500/60 rounded flex items-center justify-center text-[10px] font-bold text-red-400"
                  style={{
                    width: '65%',
                    backgroundImage: 'repeating-linear-gradient(45deg, rgba(239,68,68,0.2), rgba(239,68,68,0.2) 6px, transparent 6px, transparent 12px)',
                  }}
                >
                  TIMEOUT
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right: Error Summary */}
        <div className="lg:col-span-4 rounded-xl border border-white/[0.08] bg-[#0F1518] p-4 flex flex-col justify-between">
          <div>
            <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-zinc-300 mb-3">
              Top Errors
            </h3>
            <div className="space-y-2 font-mono text-xs">
              <div className="flex items-center justify-between">
                <span className="text-red-400">NullPointerException</span>
                <span className="font-bold text-red-400">1</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-zinc-500">TimeoutException</span>
                <span className="text-zinc-500">0</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-zinc-500">SQLException</span>
                <span className="text-zinc-500">0</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/[0.06]">
            <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider block mb-1">
              Most Affected Endpoint
            </span>
            <p className="font-mono text-xs text-red-400 font-semibold">POST /payments/charge</p>
            <p className="font-mono text-[10px] text-zinc-500">1 occurrence</p>
          </div>
        </div>
      </div>
    </div>
  )
}
