import { useCallback, useEffect, useRef, useState } from 'react'
import { approveRun, getWorkspace, rejectRun, setChangedFileDecision } from '../api/client'
import { normalizeWorkspace } from '../api/normalize'
import type { Run } from '../api/types'

const POLL_INTERVAL_MS = 1200
const MAX_POLLS = 600

function isTerminal(run: Run | undefined): boolean {
  if (!run) return false
  const terminalStates = [
    'completed',
    'failed',
    'rejected',
    'baseline_failure_not_reproduced',
    'investigation_failed',
    'investigation_timeout',
    'patch_apply_failed',
    'replay_failed',
    'validation_failed',
    'delivery_failed',
    'delivery_cancelled',
    'cancelled',
    'blocked',
    'repair_exhausted',
    'repository_not_found',
  ]
  return terminalStates.includes(run.status || '')
}

function isPaused(run: Run | undefined): boolean {
  return run?.status === 'waiting_for_approval'
}

interface UseRunResult {
  run?: Run
  error?: string
  loading: boolean
  deciding: boolean
  approve: () => Promise<void>
  reject: () => Promise<void>
  decideFile: (fileId: string, decision: 'accept' | 'reject') => Promise<void>
  refresh: () => Promise<void>
}

export function useRun(runId: string | undefined): UseRunResult {
  const [run, setRun] = useState<Run | undefined>(undefined)
  const [error, setError] = useState<string | undefined>(undefined)
  const [loading, setLoading] = useState(Boolean(runId))
  const [deciding, setDeciding] = useState(false)
  const pollCount = useRef(0)

  const load = useCallback(async (): Promise<Run | undefined> => {
    if (!runId) return undefined
    try {
      const next = normalizeWorkspace(await getWorkspace(runId))
      setRun(next)
      setError(undefined)
      return next
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : 'Unknown error')
      return undefined
    } finally {
      setLoading(false)
    }
  }, [runId])

  // Polling stops as soon as the run reaches a terminal state or the approval
  // gate, so an idle workspace never keeps hitting the backend.
  useEffect(() => {
    if (!runId) {
      setRun(undefined)
      setLoading(false)
      return
    }
    
    // Clear stale run state when switching IDs
    setRun(undefined)
    setLoading(true)
    
    let cancelled = false
    let timer: number | undefined
    pollCount.current = 0

    const tick = async () => {
      const next = await load()
      if (cancelled) return
      pollCount.current += 1
      if (isTerminal(next) || isPaused(next) || pollCount.current >= MAX_POLLS) return
      timer = window.setTimeout(() => void tick(), POLL_INTERVAL_MS)
    }

    void tick()

    return () => {
      cancelled = true
      if (timer !== undefined) window.clearTimeout(timer)
    }
  }, [load, runId])

  const decide = useCallback(
    async (action: 'approve' | 'reject') => {
      if (!runId) return
      setDeciding(true)
      try {
        await (action === 'approve' ? approveRun(runId) : rejectRun(runId))
        setError(undefined)
        let polls = 0
        const resume = async () => {
          const next = await load()
          polls += 1
          if (isTerminal(next) || polls >= MAX_POLLS) return
          await new Promise((resolve) => window.setTimeout(resolve, POLL_INTERVAL_MS))
          await resume()
        }
        await resume()
      } catch (decisionError) {
        setError(decisionError instanceof Error ? decisionError.message : 'Unknown error')
      } finally {
        setDeciding(false)
      }
    },
    [load, runId],
  )

  const decideFile = useCallback(
    async (fileId: string, decision: 'accept' | 'reject') => {
      if (!runId) return
      try {
        await setChangedFileDecision(runId, fileId, decision)
        await load()
      } catch (fileError) {
        setError(fileError instanceof Error ? fileError.message : 'Unknown error')
      }
    },
    [load, runId],
  )

  return {
    run,
    error,
    loading,
    deciding,
    approve: () => decide('approve'),
    reject: () => decide('reject'),
    decideFile,
    refresh: async () => {
      await load()
    },
  }
}
