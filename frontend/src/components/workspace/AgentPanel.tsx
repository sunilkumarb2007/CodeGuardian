import type { Run, TimelineEvent } from '../../api/types'
import { StatusDot } from '../primitives'

function latestEvent(events: TimelineEvent[]): TimelineEvent | undefined {
  return events.length > 0 ? events[events.length - 1] : undefined
}

function nextStageLabel(run: Run): string | undefined {
  const next = run.stages.find((stage) => stage.status === 'pending')
  return next?.name
}

function Block({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="border-b-2 border-ink-700 px-5 py-5 last:border-b-0">
      <p className="eyebrow">{label}</p>
      <div className="mt-3 text-sm text-white">{children}</div>
    </div>
  )
}

function Missing() {
  return <span className="font-mono text-xs text-ink-500">not reported</span>
}

export function AgentPanel({ run }: { run: Run }) {
  const event = latestEvent(run.events)
  const finding = run.investigation?.rootCause
  const next =
    run.status === 'waiting_for_approval'
      ? 'Waiting for human approval before delivery.'
      : run.status === 'rejected'
        ? 'Patch rejected. Delivery blocked.'
        : run.status === 'completed'
          ? 'Run complete.'
          : (nextStageLabel(run) ?? undefined)

  return (
    <aside className="flex h-full flex-col overflow-y-auto border-l-2 border-ink-700 bg-ink-850">
      <div className="flex items-center gap-3 border-b-2 border-ink-700 px-5 py-4">
        <StatusDot status={event?.status ?? 'pending'} />
        <p className="font-display text-sm font-bold uppercase tracking-[0.18em]">Agent</p>
      </div>
      <Block label="Current action">{event?.stage ?? <Missing />}</Block>
      <Block label="Command">
        {event?.command ? (
          <p className="break-all font-mono text-xs text-lime">$ {event.command}</p>
        ) : (
          <Missing />
        )}
      </Block>
      <Block label="Output">
        {event?.output ? (
          <p className="font-mono text-xs text-ink-300">{event.output}</p>
        ) : (
          <Missing />
        )}
      </Block>
      <Block label="Finding">{finding ?? <Missing />}</Block>
      <Block label="Next action">{next ?? <Missing />}</Block>
    </aside>
  )
}
