import { useCallback, useEffect, useState } from 'react'
import { approveRun, getWorkspace, rejectRun, setChangedFileDecision, API_BASE_URL } from '../api/client'
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

  useEffect(() => {
    if (!runId) {
      setRun(undefined)
      setLoading(false)
      return
    }

    setRun(undefined)
    setLoading(true)

    const base = API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : '')
    const wsProtocol = base.startsWith('https') ? 'wss:' : 'ws:'
    const wsHost = base.replace(/^https?:\/\//, '')
    const wsUrl = `${wsProtocol}//${wsHost}/api/orchestration/runs/${runId}/ws`
    let ws: WebSocket | null = null

    try {
      ws = new WebSocket(wsUrl)

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          const next = normalizeWorkspace(data)
          setRun(next)
          setError(undefined)
          setLoading(false)
          if (isTerminal(next)) {
            ws?.close()
          }
        } catch (err) {
          console.error("Failed to parse websocket message", err)
        }
      }

      ws.onerror = () => {
        void load()
      }
      
      ws.onclose = () => {
        setLoading(false)
      }
    } catch {
      void load()
    }

    // Always run an active HTTP poll interval so UI receives updates even if WS is dropped
    void load()
    let active = true
    const interval = setInterval(async () => {
      if (!active) return
      const next = await load()
      if (next && isTerminal(next)) {
        clearInterval(interval)
      }
    }, 2500)

    return () => {
      active = false
      clearInterval(interval)
      ws?.close()
    }
  }, [runId, load])

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
