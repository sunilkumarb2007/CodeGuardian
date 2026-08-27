import { readString } from './json'
import { asRecord } from './json'

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

  const text = await response.text()
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

export function startRun(repositoryUrl: string): Promise<unknown> {
  return request('/api/orchestration/run', {
    method: 'POST',
    body: JSON.stringify({ repository_url: repositoryUrl }),
  })
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
