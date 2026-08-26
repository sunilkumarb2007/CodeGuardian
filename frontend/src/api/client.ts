import { readString } from './json'
import { asRecord } from './json'

const RAW_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
export const API_BASE_URL = RAW_BASE.replace(/\/+$/, '')

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
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
      `Cannot reach the CodeGuardian backend at ${API_BASE_URL || window.location.origin}.`,
      0,
    )
  }

  const text = await response.text()
  const payload: unknown = text ? safeParse(text) : undefined

  if (!response.ok) {
    const detail = readString(asRecord(payload), 'detail', 'message', 'error')
    throw new ApiError(detail ?? `${response.status} ${response.statusText}`, response.status)
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
  return request('/api/demo/run', {
    method: 'POST',
    body: JSON.stringify({ repository_url: repositoryUrl }),
  })
}

export function getRun(runId: string): Promise<unknown> {
  return request(`/api/demo/runs/${encodeURIComponent(runId)}`)
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
  return request(`/api/demo/runs/${encodeURIComponent(runId)}/result`)
}

export function approveRun(runId: string): Promise<unknown> {
  return request(`/api/runs/${encodeURIComponent(runId)}/approve`, { method: 'POST' })
}

export function rejectRun(runId: string): Promise<unknown> {
  return request(`/api/runs/${encodeURIComponent(runId)}/reject`, { method: 'POST' })
}
