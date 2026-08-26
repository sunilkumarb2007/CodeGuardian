import { Link, NavLink, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { CursorFX } from './CursorFX'

const NAV = [
  { label: 'Platform', to: '/#platform' },
  { label: 'How it works', to: '/#pipeline' },
  { label: 'Investigation', to: '/#investigation' },
  { label: 'Docs', to: '/#faq' },
]

export const LOGO_SRC = '/brand/codeguardian-logo.png'

export function LogoMark({ className = 'h-9 w-9' }: { className?: string }) {
  return (
    <img
      src={LOGO_SRC}
      alt=""
      aria-hidden="true"
      className={`${className} select-none object-contain drop-shadow-[0_0_14px_rgba(198,255,61,0.35)]`}
      draggable={false}
    />
  )
}

export function Logo() {
  return (
    <Link to="/" className="group flex items-center gap-3" aria-label="CodeGuardian home">
      <LogoMark className="h-9 w-9 transition-transform duration-300 group-hover:scale-110" />
      <span className="font-display text-lg font-bold tracking-tight">
        Code<span className="text-lime">Guardian</span>
      </span>
    </Link>
  )
}

export function TopNav({ cta }: { cta?: ReactNode }) {
  const { pathname } = useLocation()
  return (
    <header className="sticky top-0 z-50 px-4 pt-4 sm:px-8">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4">
        <div className="flex items-center gap-2 rounded-pill border-2 border-ink-700 bg-ink-900/85 px-5 py-3 backdrop-blur">
          <Logo />
        </div>

        <nav className="hidden items-center gap-1 rounded-pill border-2 border-ink-700 bg-ink-900/85 px-3 py-2 backdrop-blur lg:flex">
          {NAV.map((item) => (
            <a
              key={item.label}
              href={item.to}
              className="rounded-pill px-4 py-2 text-sm font-medium text-ink-300 transition-colors hover:bg-white hover:text-ink-900"
            >
              {item.label}
            </a>
          ))}
          <NavLink
            to="/"
            className={`rounded-pill px-4 py-2 text-sm font-medium transition-colors ${
              pathname === '/' ? 'bg-white text-ink-900' : 'text-ink-300 hover:text-white'
            }`}
          >
            Home
          </NavLink>
        </nav>

        <div className="flex items-center gap-3">{cta}</div>
      </div>
    </header>
  )
}

export function Footer() {
  return (
    <footer className="mt-32 border-t-2 border-ink-700 bg-lime text-ink-900">
      <div className="mx-auto max-w-[1400px] px-6 py-16 sm:px-10">
        <div className="flex flex-wrap items-center gap-6">
          <LogoMark className="h-16 w-16 shrink-0 drop-shadow-none" />
          <p className="display-lg max-w-4xl">Symptom is where you look. Root cause is where it broke.</p>
        </div>
        <div className="mt-14 grid gap-10 border-t-2 border-ink-900/20 pt-10 md:grid-cols-4">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-ink-900/60">Platform</p>
            <ul className="mt-4 space-y-2 text-sm font-medium">
              <li>GhostTrace reconstruction</li>
              <li>Failure memory</li>
              <li>Patch &amp; replay</li>
              <li>Validation gates</li>
            </ul>
          </div>
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-ink-900/60">Pipeline</p>
            <ul className="mt-4 space-y-2 text-sm font-medium">
              <li>Inspect → Triage</li>
              <li>Evidence → GhostTrace</li>
              <li>Investigate → Patch</li>
              <li>Replay → Deliver</li>
            </ul>
          </div>
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-ink-900/60">Safety</p>
            <ul className="mt-4 space-y-2 text-sm font-medium">
              <li>Human approval gate</li>
              <li>No unvalidated delivery</li>
              <li>Backend-sourced state only</li>
              <li>Explicit failure reporting</li>
            </ul>
          </div>
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-ink-900/60">Project</p>
            <ul className="mt-4 space-y-2 text-sm font-medium">
              <li>
                <a className="underline underline-offset-4" href="https://github.com/sunilkumarb2007/CodeGuardian">
                  GitHub repository
                </a>
              </li>
              <li>FastAPI · PostgreSQL · SQLAlchemy</li>
            </ul>
          </div>
        </div>
        <p className="mt-12 flex items-center gap-3 font-mono text-[11px] uppercase tracking-[0.22em] text-ink-900/60">
          <LogoMark className="h-5 w-5 drop-shadow-none" />
          CodeGuardian — autonomous engineering failure investigation
        </p>
      </div>
    </footer>
  )
}

export function Shell({ children, cta }: { children: ReactNode; cta?: ReactNode }) {
  return (
    <div className="min-h-screen bg-ink-900">
      <CursorFX />
      <TopNav cta={cta} />
      {children}
    </div>
  )
}

export function BrandLoader({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-4">
      <span className="relative flex h-12 w-12 items-center justify-center">
        <span className="absolute inset-0 animate-pulseRing rounded-pill border-2 border-lime/50" />
        <LogoMark className="h-9 w-9" />
      </span>
      <span className="eyebrow">{label}</span>
    </div>
  )
}
