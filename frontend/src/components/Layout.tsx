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
    <header className="sticky top-4 z-50 px-4 sm:px-8 pointer-events-none">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-4 rounded-2xl border-2 border-ink-700 bg-ink-900/85 px-5 py-3 shadow-[0_8px_32px_rgba(0,0,0,0.5)] backdrop-blur-md pointer-events-auto">
        <div className="flex items-center gap-2">
          <Logo />
        </div>

        <nav className="hidden flex-1 items-center justify-center gap-2 lg:flex">
          {NAV.map((item) => (
            <a
              key={item.label}
              href={item.to}
              className="rounded-lg px-4 py-2 text-sm font-medium text-ink-300 transition-colors hover:bg-ink-800 hover:text-white"
            >
              {item.label}
            </a>
          ))}
          <NavLink
            to="/"
            className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              pathname === '/' ? 'bg-ink-800 text-white' : 'text-ink-300 hover:bg-ink-800 hover:text-white'
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
    <footer className="border-t border-ink-800 bg-ink-950 text-ink-400">
      <div className="mx-auto max-w-[1400px] px-6 py-16 sm:px-10">
        <div className="flex flex-wrap items-center justify-between gap-6 border-b border-ink-800 pb-10">
          <div className="flex items-center gap-3">
            <LogoMark className="h-8 w-8" />
            <span className="font-display text-lg font-bold tracking-tight text-white">
              Code<span className="text-lime">Guardian</span>
            </span>
          </div>
          <p className="font-mono text-xs uppercase tracking-widest text-zinc-500">
            Autonomous Failure Investigation &amp; Verified Repair
          </p>
        </div>
        <div className="mt-10 grid gap-8 md:grid-cols-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-widest text-lime font-bold">Platform</p>
            <ul className="mt-4 space-y-2 text-xs font-medium text-zinc-400">
              <li>GhostTrace causal flow</li>
              <li>Failure DNA &amp; fingerprinting</li>
              <li>Counterfactual Repair Lab</li>
              <li>Deterministic replay proof</li>
            </ul>
          </div>
          <div>
            <p className="font-mono text-xs uppercase tracking-widest text-lime font-bold">17-Stage Pipeline</p>
            <ul className="mt-4 space-y-2 text-xs font-medium text-zinc-400">
              <li>Inspect &amp; Detect (01–04)</li>
              <li>Evidence &amp; Trace (05–08)</li>
              <li>Patch &amp; Replay (09–11)</li>
              <li>Build, Test &amp; Deliver (12–17)</li>
            </ul>
          </div>
          <div>
            <p className="font-mono text-xs uppercase tracking-widest text-lime font-bold">Safety &amp; Verification</p>
            <ul className="mt-4 space-y-2 text-xs font-medium text-zinc-400">
              <li>6/6 Deterministic safety gates</li>
              <li>Sandboxed container execution</li>
              <li>Human-in-the-loop approval gate</li>
              <li>Zero unverified deliveries</li>
            </ul>
          </div>
          <div>
            <p className="font-mono text-xs uppercase tracking-widest text-lime font-bold">Ecosystem</p>
            <ul className="mt-4 space-y-2 text-xs font-medium text-zinc-400">
              <li>
                <a
                  className="hover:text-white transition-colors underline underline-offset-4"
                  href="https://github.com/sunilkumarb2007/CodeGuardian"
                  target="_blank"
                  rel="noreferrer"
                >
                  GitHub Repository →
                </a>
              </li>
              <li>FastAPI · PostgreSQL · Sarvam AI</li>
              <li>VS Code Extension (.vsix)</li>
            </ul>
          </div>
        </div>
        <div className="mt-12 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-ink-800/80 pt-6 text-xs text-zinc-500 font-mono">
          <p>© 2026 CodeGuardian. Evidence-driven autonomous software repair.</p>
          <p className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-lime animate-pulse" />
            Engine: Sarvam 105B · PostgreSQL 17
          </p>
        </div>
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
