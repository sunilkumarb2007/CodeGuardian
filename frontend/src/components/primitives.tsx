import { motion } from 'framer-motion'
import type { ReactNode } from 'react'
import type { StageStatus } from '../api/types'

export function Reveal({
  children,
  delay = 0,
  className,
}: {
  children: ReactNode
  delay?: number
  className?: string
}) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 28 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ duration: 0.55, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  )
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return <p className="eyebrow">{children}</p>
}

export function Card({
  children,
  className = '',
  accent,
}: {
  children: ReactNode
  className?: string
  accent?: 'lime' | 'blue' | 'orange' | 'pink' | 'purple'
}) {
  const accentBorder =
    accent === 'lime'
      ? 'border-lime/50'
      : accent === 'blue'
        ? 'border-signal-blue/50'
        : accent === 'orange'
          ? 'border-signal-orange/50'
          : accent === 'pink'
            ? 'border-signal-pink/50'
            : accent === 'purple'
              ? 'border-signal-purple/50'
              : ''
  return <div className={`card ${accentBorder} ${className}`}>{children}</div>
}

export function PanelHeading({
  index,
  title,
  caption,
  right,
}: {
  index?: string
  title: string
  caption?: string
  right?: ReactNode
}) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4 border-b-2 border-ink-700 px-7 py-6">
      <div className="flex items-start gap-4">
        {index ? (
          <span className="mt-1 inline-flex h-9 w-9 items-center justify-center rounded-pill border-2 border-ink-600 font-mono text-xs text-ink-300">
            {index}
          </span>
        ) : null}
        <div>
          <h3 className="font-display text-xl font-bold tracking-tight sm:text-2xl">{title}</h3>
          {caption ? <p className="mt-1 max-w-xl text-sm text-ink-300">{caption}</p> : null}
        </div>
      </div>
      {right}
    </div>
  )
}

const STATUS_STYLES: Record<StageStatus, { dot: string; label: string; text: string }> = {
  pending: { dot: 'bg-ink-500', label: 'PENDING', text: 'text-ink-400' },
  running: { dot: 'bg-lime animate-pulseRing', label: 'RUNNING', text: 'text-lime' },
  passed: { dot: 'bg-lime', label: 'PASSED', text: 'text-lime' },
  completed: { dot: 'bg-lime', label: 'COMPLETED', text: 'text-lime' },
  failed: { dot: 'bg-signal-pink', label: 'FAILED', text: 'text-signal-pink' },
  waiting_for_approval: { dot: 'bg-signal-orange', label: 'AWAITING APPROVAL', text: 'text-signal-orange' },
  rejected: { dot: 'bg-signal-pink', label: 'REJECTED', text: 'text-signal-pink' },
  skipped: { dot: 'bg-ink-500', label: 'SKIPPED', text: 'text-ink-400' },
}

export function StatusBadge({ status, label }: { status: StageStatus; label?: string }) {
  const style = STATUS_STYLES[status]
  return (
    <span className={`pill border-ink-600 ${style.text}`}>
      <span className={`h-2 w-2 rounded-pill ${style.dot}`} />
      {label ?? style.label}
    </span>
  )
}

export function StatusDot({ status }: { status: StageStatus }) {
  return <span className={`h-2.5 w-2.5 shrink-0 rounded-pill ${STATUS_STYLES[status].dot}`} />
}

export function Metric({
  label,
  value,
  accent = false,
}: {
  label: string
  value?: string | number
  accent?: boolean
}) {
  return (
    <div className="border-t-2 border-ink-700 pt-4">
      <p className="eyebrow">{label}</p>
      <p
        className={`mt-2 font-display text-lg font-bold tracking-tight ${
          accent ? 'text-lime' : value === undefined ? 'text-ink-500' : 'text-white'
        }`}
      >
        {value ?? 'NOT REPORTED'}
      </p>
    </div>
  )
}

export function KeyValue({ label, value }: { label: string; value?: string | number }) {
  return (
    <div className="flex items-baseline justify-between gap-6 border-b border-ink-700 py-3 last:border-b-0">
      <span className="eyebrow">{label}</span>
      <span
        className={`text-right font-mono text-[13px] ${value === undefined ? 'text-ink-500' : 'text-white'}`}
      >
        {value ?? 'not reported'}
      </span>
    </div>
  )
}

export function CheckIcon({ passed }: { passed?: boolean }) {
  if (passed === undefined) {
    return <span className="font-mono text-sm text-ink-500">○</span>
  }
  return (
    <span className={`font-mono text-sm ${passed ? 'text-lime' : 'text-signal-pink'}`}>
      {passed ? '✓' : '×'}
    </span>
  )
}

export function EmptyState({ message }: { message: string }) {
  return (
    <div className="px-7 py-10 text-center">
      <p className="font-mono text-xs uppercase tracking-[0.2em] text-ink-500">{message}</p>
    </div>
  )
}

export function ProgressBar({ value, label }: { value: number; label?: string }) {
  const clamped = Math.max(0, Math.min(100, value))
  return (
    <div>
      <div className="h-3 w-full overflow-hidden rounded-pill border-2 border-ink-600 bg-ink-900">
        <motion.div
          className="h-full rounded-pill bg-lime"
          initial={{ width: 0 }}
          animate={{ width: `${clamped}%` }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>
      {label ? <p className="mt-2 font-mono text-xs text-ink-300">{label}</p> : null}
    </div>
  )
}

export function Marquee({ items }: { items: string[] }) {
  const loop = [...items, ...items]
  return (
    <div className="overflow-hidden border-y-2 border-ink-700 bg-lime py-4">
      <div className="flex w-max animate-marquee items-center gap-10 whitespace-nowrap">
        {loop.map((item, index) => (
          <span
            key={`${item}-${index}`}
            className="font-display text-2xl font-bold tracking-tight text-ink-900 sm:text-3xl"
          >
            {item}
            <span className="px-6 text-ink-900/50">✳</span>
          </span>
        ))}
      </div>
    </div>
  )
}
