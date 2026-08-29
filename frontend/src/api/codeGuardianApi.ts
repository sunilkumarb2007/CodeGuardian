import { readString, asRecord } from './json'

const RAW_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
export const API_BASE_URL = RAW_BASE.replace(/\/+$/, '')

export class ApiError extends Error {
  readonly status: number
  readonly title: string
  readonly statusText: string

  constructor(message: string, status: number, title?: string, statusText?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.statusText = statusText ?? (status === 0 ? 'Backend connection unavailable' : `HTTP ${status}`)
    this.title = title ?? (
      status === 0
        ? 'Backend Unavailable'
        : status === 400 || status === 422
          ? 'Invalid Repository Request'
          : status === 401 || status === 403
            ? 'Authorization Required'
            : status === 404
              ? 'Run or Repository Not Found'
              : status >= 500
                ? 'Investigation Service Error'
                : 'Investigation Unavailable'
    )
  }
}

function safeParse(text: string): unknown {
  try {
    return JSON.parse(text) as unknown
  } catch {
    return { detail: text }
  }
}

async function request(path: string, init?: RequestInit): Promise<unknown> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    throw new ApiError(
      `Cannot reach the CodeGuardian backend at ${API_BASE_URL || window.location.origin}. Please ensure the backend server is running.`,
      0,
      'Backend Unavailable',
      'Connection refused · 0',
    )
  }

  const text = await response.text()
  const payload: unknown = text ? safeParse(text) : undefined

  if (!response.ok) {
    const detail = readString(asRecord(payload), 'detail', 'message', 'error')
    let title = 'Investigation Unavailable'
    let statusText = `HTTP ${response.status}`

    if (response.status === 400 || response.status === 422) {
      title = 'Invalid Repository Request'
      statusText = `Validation error · ${response.status}`
    } else if (response.status === 401 || response.status === 403) {
      title = 'Authorization Required'
      statusText = `Auth error · ${response.status}`
    } else if (response.status === 404) {
      title = 'Run or Repository Not Found'
      statusText = `Not found · 404`
    } else if (response.status >= 500) {
      title = 'Investigation Service Error'
      statusText = `Server error · ${response.status}`
    }

    const message = detail || (
      response.status >= 500 
        ? 'The backend encountered an error while processing the investigation.'
        : `${response.status} ${response.statusText}`
    )

    throw new ApiError(message, response.status, title, statusText)
  }

  return payload
}

export const codeGuardianApi = {
  /** 1. Create / Start investigation run */
  startRun(repositoryUrl: string, suppliedIncidentId?: string, failureInput?: Record<string, unknown>): Promise<{ run_id: string; status: string }> {
    return request('/api/orchestration/run', {
      method: 'POST',
      body: JSON.stringify({
        repository_url: repositoryUrl,
        supplied_incident_id: suppliedIncidentId,
        failure_input: failureInput,
      }),
    }) as Promise<{ run_id: string; status: string }>
  },

  /** 2. Get single run state (authoritative status and stage map) */
  getRunState(runId: string): Promise<unknown> {
    return request(`/api/runs/${encodeURIComponent(runId)}/state`)
  },

  /** 3. Get complete workspace (17 stages, artifacts, events, commands, source tree) */
  getWorkspace(runId: string): Promise<unknown> {
    return request(`/api/runs/${encodeURIComponent(runId)}/workspace`)
  },

  /** 4. Get run events */
  getAgentEvents(runId: string): Promise<unknown> {
    return request(`/api/runs/${encodeURIComponent(runId)}/agent-events`)
  },

  /** 5. Get command log */
  getCommands(runId: string): Promise<unknown> {
    return request(`/api/runs/${encodeURIComponent(runId)}/commands`)
  },

  /** 6. Approve candidate patch and initiate delivery */
  approveRun(runId: string): Promise<{ status: string; message?: string }> {
    return request(`/api/runs/${encodeURIComponent(runId)}/approve`, { method: 'POST' }) as Promise<{ status: string; message?: string }>
  },

  /** 7. Reject candidate patch */
  rejectRun(runId: string): Promise<{ status: string }> {
    return request(`/api/runs/${encodeURIComponent(runId)}/reject`, { method: 'POST' }) as Promise<{ status: string }>
  },

  /** 8. File-level review decision */
  setChangedFileDecision(runId: string, fileId: string, decision: 'accept' | 'reject'): Promise<unknown> {
    return request(
      `/api/runs/${encodeURIComponent(runId)}/changed-files/${encodeURIComponent(fileId)}/${decision}`,
      { method: 'POST' },
    )
  },

  /** 9. Failure DNA */
  getFailureDna(runId: string): Promise<unknown> {
    return request(`/api/runs/${encodeURIComponent(runId)}/failure-dna`)
  },

  /** 10. Repair Candidates */
  getRepairCandidates(runId: string): Promise<unknown> {
    return request(`/api/runs/${encodeURIComponent(runId)}/repair-candidates`)
  },

  /** 11. Blast Radius Impact */
  getImpact(runId: string): Promise<unknown> {
    return request(`/api/runs/${encodeURIComponent(runId)}/impact`)
  },

  /** 12. Failure Lab scenario execution */
  runFailureScenario(scenarioId: string): Promise<{ run_id: string }> {
    return request(`/api/failure-lab/scenarios/${encodeURIComponent(scenarioId)}/run`, {
      method: 'POST',
    }) as Promise<{ run_id: string }>
  },

  /** 13. List Failure Lab scenarios */
  listFailureScenarios(): Promise<unknown> {
    return request('/api/failure-lab/scenarios')
  },

  /** 14. System status & health check */
  getSystemStatus(): Promise<unknown> {
    return request('/api/system/status')
  },

  /** 15. Export failure capsule */
  exportCapsule(runId: string): string {
    return `${API_BASE_URL}/api/capsules/${encodeURIComponent(runId)}/export`
  },
}

// Re-export standalone helpers for compatibility
export const startRun = codeGuardianApi.startRun
export const getRun = codeGuardianApi.getRunState
export const getWorkspace = codeGuardianApi.getWorkspace
export const approveRun = codeGuardianApi.approveRun
export const rejectRun = codeGuardianApi.rejectRun
export const setChangedFileDecision = codeGuardianApi.setChangedFileDecision
export const runFailureScenario = codeGuardianApi.runFailureScenario
export const listFailureScenarios = codeGuardianApi.listFailureScenarios
