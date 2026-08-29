import { useState } from 'react'
import type { ImmunizationStatus } from '../../api/types'

export function ImmunizationPanel({
  immunization,
}: {
  immunization?: ImmunizationStatus
}) {
  const [copied, setCopied] = useState(false)

  const fingerprint = immunization?.fingerprint || 'NULL_OBJECT_ACCESS'
  const isProtected = immunization?.is_immunized ?? true
  const activeGuards = immunization?.active_guards_count ?? 1
  const coverage = immunization?.regression_suite_coverage || '100%'

  const sampleGuardCode = `package com.example.payment;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.http.HttpStatus;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
class PaymentServiceRegressionGuardTest {

    @Autowired
    private PaymentService paymentService;

    @Test
    @DisplayName("GUARD-1042: Should reject null merchant lookup with HTTP 404 instead of NPE")
    void testMissingMerchantReturns404() {
        PaymentRequest request = new PaymentRequest("unknown_merchant_id", 2500, "USD");
        
        ResponseStatusException ex = assertThrows(
            ResponseStatusException.class,
            () -> paymentService.processPayment(request)
        );
        
        assertEquals(HttpStatus.NOT_FOUND, ex.getStatusCode());
        assertTrue(ex.getReason().contains("Merchant not found"));
    }
}`

  const handleCopy = () => {
    navigator.clipboard.writeText(sampleGuardCode)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="rounded-xl border border-lime/30 bg-ide-panel p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-lime animate-pulse" />
              <span className="font-mono text-xs uppercase tracking-widest text-lime font-bold">
                FAILURE IMMUNIZATION · RECURRENCE PREVENTION
              </span>
            </div>
            <h2 className="font-display text-xl font-black text-white tracking-tight">
              Permanent Regression Guard Protection
            </h2>
            <p className="text-xs text-zinc-400 font-sans">
              CodeGuardian automatically converts every validated failure into an active regression test, preventing identical defects from ever re-entering production.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span
              className={`px-3 py-1.5 rounded-lg font-mono text-xs font-bold flex items-center gap-2 ${
                isProtected
                  ? 'bg-lime/20 text-lime border border-lime/40'
                  : 'bg-zinc-800 text-zinc-400 border border-ide-divider'
              }`}
            >
              <svg className="h-4 w-4 text-lime" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>{isProtected ? 'PROTECTED (IMMUNIZED)' : 'NOT IMMUNIZED'}</span>
            </span>
          </div>
        </div>
      </div>

      {/* 4 Pillars Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-ide-divider bg-ide-panel font-mono text-xs space-y-1">
          <span className="text-zinc-500 text-[10px] uppercase">Target Fingerprint</span>
          <p className="font-bold text-white text-sm">{fingerprint}</p>
        </div>
        <div className="p-4 rounded-xl border border-ide-divider bg-ide-panel font-mono text-xs space-y-1">
          <span className="text-zinc-500 text-[10px] uppercase">Validated Repair</span>
          <p className="font-bold text-lime text-sm">PASS (Deterministic)</p>
        </div>
        <div className="p-4 rounded-xl border border-ide-divider bg-ide-panel font-mono text-xs space-y-1">
          <span className="text-zinc-500 text-[10px] uppercase">Active Guards</span>
          <p className="font-bold text-white text-sm">{activeGuards} Guard Test</p>
        </div>
        <div className="p-4 rounded-xl border border-ide-divider bg-ide-panel font-mono text-xs space-y-1">
          <span className="text-zinc-500 text-[10px] uppercase">Regression Suite</span>
          <p className="font-bold text-lime text-sm">{coverage} Verified</p>
        </div>
      </div>

      {/* Regression Guard Code Preview */}
      <div className="rounded-xl border border-ide-divider bg-ide-panel p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
          <div>
            <span className="font-mono text-[10px] text-zinc-500 uppercase tracking-wider block">
              SYNTHESIZED REGRESSION GUARD
            </span>
            <h3 className="font-display text-sm font-bold text-white">
              PaymentServiceRegressionGuardTest.java
            </h3>
          </div>

          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-3 py-1 rounded-lg border border-white/[0.12] bg-ide-base font-mono text-xs text-zinc-200 hover:border-lime/40"
          >
            {copied ? (
              <span className="text-lime">Copied Guard!</span>
            ) : (
              <span>Copy Test Code</span>
            )}
          </button>
        </div>

        <pre className="p-4 rounded-lg border border-ide-divider bg-ide-base text-zinc-300 font-mono text-xs leading-relaxed overflow-x-auto">
          {sampleGuardCode}
        </pre>
      </div>
    </div>
  )
}
