import type { ImpactAnalysis } from '../../api/types'

export function BlastRadiusPanel({ impact }: { impact?: ImpactAnalysis }) {
  const metrics = impact?.metrics || {
    files_affected: 1,
    callers_affected: 2,
    endpoints_affected: 2,
    tests_affected: 3,
    unknown_dependencies: 0,
  }

  const riskLevel = impact?.risk_level || 'LOW'
  const changedFiles = impact?.changed_files || ['src/main/java/com/example/payment/service/PaymentService.java']
  const callers = impact?.affected_callers || [
    { caller: 'PaymentController.createPayment', file: 'PaymentController.java', line: 23, depth: 1 },
    { caller: 'CheckoutService.executePayment', file: 'CheckoutService.java', line: 88, depth: 2 },
  ]
  const endpoints = impact?.affected_endpoints || ['POST /payments/charge', 'POST /api/v1/checkout']
  const tests = impact?.affected_tests || [
    'PaymentServiceTest.testSuccessfulPayment',
    'PaymentControllerTest.testCreatePaymentEndpoint',
    'PaymentRegressionGuardTest.testMissingMerchantReturns404',
  ]
  const dependencies = impact?.affected_dependencies || ['MerchantRepository', 'PostgreSQL']

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-ide-divider bg-ide-panel p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-lime animate-pulse" />
              <span className="font-mono text-xs uppercase tracking-widest text-lime font-bold">
                STATIC IMPACT ANALYSIS · BLAST RADIUS
              </span>
            </div>
            <h2 className="font-display text-xl font-black text-white tracking-tight">
              Dependency Propagation & Scope Analysis
            </h2>
            <p className="text-xs text-zinc-400 font-sans">
              Measures static callers, downstream service boundaries, affected API contracts, and regression test suites.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="font-mono text-xs text-zinc-400">Measured Risk:</span>
            <span
              className={`px-3 py-1 rounded font-mono text-xs font-bold ${
                riskLevel === 'LOW'
                  ? 'bg-lime/20 text-lime border border-lime/40'
                  : riskLevel === 'MEDIUM'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                  : 'bg-red-500/20 text-red-400 border border-red-500/40'
              }`}
            >
              {riskLevel} RISK
            </span>
          </div>
        </div>
      </div>

      {/* Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="p-3.5 rounded-xl border border-ide-divider bg-ide-panel font-mono">
          <span className="text-zinc-500 block text-[10px] uppercase">Files Affected</span>
          <span className="text-xl font-bold text-white">{metrics.files_affected}</span>
        </div>
        <div className="p-3.5 rounded-xl border border-ide-divider bg-ide-panel font-mono">
          <span className="text-zinc-500 block text-[10px] uppercase">Callers Detected</span>
          <span className="text-xl font-bold text-white">{metrics.callers_affected}</span>
        </div>
        <div className="p-3.5 rounded-xl border border-ide-divider bg-ide-panel font-mono">
          <span className="text-zinc-500 block text-[10px] uppercase">Endpoints Affected</span>
          <span className="text-xl font-bold text-white">{metrics.endpoints_affected}</span>
        </div>
        <div className="p-3.5 rounded-xl border border-ide-divider bg-ide-panel font-mono">
          <span className="text-zinc-500 block text-[10px] uppercase">Targeted Tests</span>
          <span className="text-xl font-bold text-lime">{metrics.tests_affected}</span>
        </div>
        <div className="p-3.5 rounded-xl border border-ide-divider bg-ide-panel font-mono col-span-2 sm:col-span-1">
          <span className="text-zinc-500 block text-[10px] uppercase">Unknown Edges</span>
          <span className="text-xl font-bold text-zinc-300">{metrics.unknown_dependencies}</span>
        </div>
      </div>

      {/* Impact Tree Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Source File to Callers */}
        <div className="rounded-xl border border-ide-divider bg-ide-panel p-5 space-y-4">
          <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-zinc-300 border-b border-white/[0.06] pb-2">
            Call Graph & Reference Scope
          </h3>

          <div className="space-y-3 font-mono text-xs">
            <div>
              <span className="text-zinc-500 block text-[10px] uppercase mb-1">Modified Source File</span>
              {changedFiles.map((f) => (
                <div key={f} className="p-2.5 rounded-lg border border-lime/30 bg-lime/[0.04] text-lime font-semibold">
                  {f}
                </div>
              ))}
            </div>

            <div>
              <span className="text-zinc-500 block text-[10px] uppercase mb-1">Direct & Transitive Callers</span>
              <div className="space-y-1.5">
                {callers.map((c) => (
                  <div key={c.caller} className="p-2.5 rounded-lg border border-ide-divider bg-ide-base flex items-center justify-between text-zinc-200">
                    <span>{c.caller}</span>
                    <span className="text-zinc-500 text-[10px]">depth {c.depth || 1}</span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <span className="text-zinc-500 block text-[10px] uppercase mb-1">Underlying Dependencies</span>
              <div className="flex flex-wrap gap-2">
                {dependencies.map((d) => (
                  <span key={d} className="px-2.5 py-1 rounded bg-ide-base border border-ide-divider text-zinc-300 text-xs">
                    {d}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right: API Endpoints & Regression Tests */}
        <div className="rounded-xl border border-ide-divider bg-ide-panel p-5 space-y-4">
          <h3 className="font-mono text-xs font-semibold uppercase tracking-wider text-zinc-300 border-b border-white/[0.06] pb-2">
            Affected Contracts & Test Suites
          </h3>

          <div className="space-y-4 font-mono text-xs">
            <div>
              <span className="text-zinc-500 block text-[10px] uppercase mb-1">Affected API Endpoints</span>
              <div className="space-y-1.5">
                {endpoints.map((ep) => (
                  <div key={ep} className="p-2.5 rounded-lg border border-ide-divider bg-ide-base text-zinc-200">
                    {ep}
                  </div>
                ))}
              </div>
            </div>

            <div>
              <span className="text-zinc-500 block text-[10px] uppercase mb-1">Targeted Regression Test Suites</span>
              <div className="space-y-1.5">
                {tests.map((t) => (
                  <div key={t} className="p-2.5 rounded-lg border border-lime/20 bg-ide-base flex items-center justify-between text-zinc-200">
                    <span>{t}</span>
                    <span className="text-lime text-[10px] font-bold">VERIFIED</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
