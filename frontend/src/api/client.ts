import { readString } from './json'
import { asRecord } from './json'

const RAW_BASE = import.meta.env.VITE_API_BASE_URL || (import.meta.env.PROD ? 'https://codeguardian-api-vwmb.onrender.com' : '')
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
        ? 'Investigation unavailable'
        : status === 400 || status === 422
          ? 'Invalid repository request'
          : status === 401 || status === 403
            ? 'Authorization required'
            : status === 404
              ? 'Endpoint or repository not found'
              : status >= 500
                ? 'Investigation service error'
                : 'Investigation unavailable'
    )
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
      'Investigation unavailable',
      'Backend connection unavailable',
    )
  }

  const contentType = response.headers.get('content-type') || ''
  const text = await response.text()

  if (contentType.includes('text/html') || text.trim().startsWith('<!doctype html') || text.trim().startsWith('<html')) {
    throw new ApiError(
      `Received HTML page instead of API response from ${API_BASE_URL || window.location.origin}. Check backend API URL configuration.`,
      response.status === 200 ? 502 : response.status,
      'Invalid Backend Response',
      'HTML received instead of JSON',
    )
  }

  const payload: unknown = text ? safeParse(text) : undefined

  if (!response.ok) {
    const detail = readString(asRecord(payload), 'detail', 'message', 'error')
    let title = 'Investigation unavailable'
    let statusText = `HTTP ${response.status}`

    if (response.status === 400 || response.status === 422) {
      title = 'Invalid repository request'
      statusText = `Validation error · ${response.status}`
    } else if (response.status === 401 || response.status === 403) {
      title = 'Authorization required'
      statusText = `Auth error · ${response.status}`
    } else if (response.status === 404) {
      title = 'Endpoint or repository not found'
      statusText = `Not found · 404`
    } else if (response.status >= 500) {
      title = 'Investigation service error'
      statusText = `Server error · ${response.status}`
    }

    const message = detail || (
      response.status >= 500 
        ? 'The backend encountered an internal error while processing the request.'
        : `${response.status} ${response.statusText}`
    )

    throw new ApiError(message, response.status, title, statusText)
  }

  return payload
}

function safeParse(text: string): unknown {
  try {
    return JSON.parse(text) as unknown
  } catch {
    return { detail: text }
  }
}

export async function startRun(
  repositoryUrl: string,
  failureInput?: Record<string, unknown>,
): Promise<{ run_id: string; [key: string]: unknown }> {
  try {
    const res = (await request('/api/orchestration/run', {
      method: 'POST',
      body: JSON.stringify({ repository_url: repositoryUrl, failure_input: failureInput }),
    })) as Record<string, unknown>
    const id = readString(asRecord(res), 'run_id', 'runId', 'id')
    if (id) {
      return { run_id: id, ...res }
    }
  } catch (err) {
    if (err instanceof ApiError && (err.status === 404 || err.status === 405)) {
      const ingestRes = (await request('/api/incidents/ingest', {
        method: 'POST',
        body: JSON.stringify({
          repository: repositoryUrl,
          ...(failureInput || {}),
        }),
      })) as Record<string, unknown>
      const id = readString(asRecord(ingestRes), 'run_id', 'runId', 'id')
      if (id) {
        return { run_id: id, ...ingestRes }
      }
    }
    throw err
  }
  throw new ApiError('The backend accepted the request but did not return a valid run ID.', 500, 'Invalid response', 'Missing run_id')
}

export function getRun(runId: string): Promise<unknown> {
  return request(`/api/runs/${encodeURIComponent(runId)}/state`)
}

/** Full investigation workspace: every stage, artefact, event and command of a run. */
export function getWorkspace(runId: string): Promise<unknown> {
  return request(`/api/runs/${encodeURIComponent(runId)}/workspace`)
}

export function setChangedFileDecision(
  runId: string,
  fileId: string,
  decision: 'accept' | 'reject',
): Promise<unknown> {
  return request(
    `/api/runs/${encodeURIComponent(runId)}/changed-files/${encodeURIComponent(fileId)}/${decision}`,
    { method: 'POST' },
  )
}

export function getRunResult(runId: string): Promise<unknown> {
  return request(`/api/orchestration/runs/${encodeURIComponent(runId)}/result`)
}

export function approveRun(runId: string): Promise<unknown> {
  return request(`/api/runs/${encodeURIComponent(runId)}/approve`, { method: 'POST' })
}

export function rejectRun(runId: string): Promise<unknown> {
  return request(`/api/runs/${encodeURIComponent(runId)}/reject`, { method: 'POST' })
}

export function runFailureScenario(scenarioId: string): Promise<{ run_id: string }> {
  return request(`/api/failure-lab/scenarios/${encodeURIComponent(scenarioId)}/run`, {
    method: 'POST',
  }) as Promise<{ run_id: string }>
}

export function listFailureScenarios(): Promise<unknown> {
  return request('/api/failure-lab/scenarios')
}

