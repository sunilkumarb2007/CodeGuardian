import { motion } from 'framer-motion'
import type { Stage, TimelineEvent } from '../../api/types'
import { Card, EmptyState, PanelHeading, StatusBadge, StatusDot } from '../primitives'

function pad(index: number): string {
  return String(index + 1).padStart(2, '0')
}

export function StageRail({ stages, currentStage }: { stages: Stage[]; currentStage?: string }) {
  if (stages.length === 0) {
    return (
      <Card>
        <PanelHeading title="Pipeline" caption="Stages are rendered exactly as the backend reports them." />
        <EmptyState message="Backend has not reported any stages yet" />
      </Card>
    )
  }

  return (
    <Card>
      <PanelHeading
        index="01"
        title="Investigation pipeline"
        caption="Every stage below is driven by the backend run state — nothing is simulated in the browser."
        right={
          <span className="pill border-ink-600 text-ink-300">
            {stages.filter((stage) => stage.status === 'passed' || stage.status === 'completed').length} /{' '}
            {stages.length} complete
          </span>
        }
      />
      <div className="grid grid-cols-2 gap-px bg-ink-700 sm:grid-cols-3 xl:grid-cols-4">
        {stages.map((stage, index) => {
          const active = stage.status === 'running' || stage.key === currentStage
          return (
            <motion.div
              key={stage.key}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: Math.min(index * 0.03, 0.4) }}
              className={`relative min-h-[122px] p-5 transition-colors ${
                active ? 'bg-lime text-ink-900' : 'bg-ink-850'
              }`}
            >
              <div className="flex items-center justify-between">
                <span
                  className={`font-mono text-[11px] tracking-[0.2em] ${
                    active ? 'text-ink-900/70' : 'text-ink-400'
                  }`}
                >
                  {pad(index)}
                </span>
                {active ? (
                  <span className="h-2.5 w-2.5 rounded-pill bg-ink-900" />
                ) : (
                  <StatusDot status={stage.status} />
                )}
              </div>
              <p className="mt-4 font-display text-sm font-bold leading-tight tracking-tight">{stage.name}</p>
              <p
                className={`mt-2 line-clamp-2 text-xs ${active ? 'text-ink-900/70' : 'text-ink-400'}`}
              >
                {stage.description ?? stage.status.replace(/_/g, ' ')}
              </p>
            </motion.div>
          )
        })}
      </div>
    </Card>
  )
}

export function StageList({ stages }: { stages: Stage[] }) {
  if (stages.length === 0) return null
  return (
    <Card>
      <PanelHeading index="02" title="Stage detail" caption="Status, timing and output reported per stage." />
      <ul>
        {stages.map((stage) => (
          <li
            key={stage.key}
            className="flex flex-wrap items-center justify-between gap-4 border-b border-ink-700 px-7 py-4 last:border-b-0"
          >
            <div className="flex items-center gap-4">
              <StatusDot status={stage.status} />
              <div>
                <p className="font-display text-sm font-bold tracking-tight">{stage.name}</p>
                {stage.description ? <p className="text-xs text-ink-400">{stage.description}</p> : null}
              </div>
            </div>
            <div className="flex items-center gap-4">
              {stage.durationMs !== undefined ? (
                <span className="font-mono text-[11px] text-ink-400">{stage.durationMs} ms</span>
              ) : null}
              <StatusBadge status={stage.status} />
            </div>
          </li>
        ))}
      </ul>
    </Card>
  )
}

export function EventFeed({ events }: { events: TimelineEvent[] }) {
  return (
    <Card className="h-full">
      <PanelHeading
        title="Live event feed"
        caption="Engineering events streamed from the run record."
        right={<span className="pill border-ink-600 text-ink-300">{events.length} events</span>}
      />
      {events.length === 0 ? (
        <EmptyState message="No events reported yet" />
      ) : (
        <ol className="max-h-[520px] overflow-y-auto px-7 py-4">
          {events.map((event) => (
            <li key={event.id} className="relative border-l-2 border-ink-700 py-3 pl-6">
              <span className="absolute -left-[7px] top-5 h-3 w-3 rounded-pill border-2 border-ink-900 bg-lime" />
              <div className="flex flex-wrap items-center gap-3">
                {event.timestamp ? (
                  <span className="font-mono text-[11px] text-ink-400">{event.timestamp}</span>
                ) : null}
                {event.channel ? (
                  <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-lime">
                    {event.channel}
                  </span>
                ) : null}
              </div>
              <p className="mt-1 text-sm text-white">{event.message}</p>
            </li>
          ))}
        </ol>
      )}
    </Card>
  )
}
