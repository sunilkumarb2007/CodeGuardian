/**
 * Tolerant readers for JSON returned by the CodeGuardian backend.
 *
 * The frontend never fabricates values: every reader returns `undefined`
 * when the backend did not provide the field, and the UI renders an
 * explicit "not reported" state instead of inventing data.
 */

export type JsonRecord = Record<string, unknown>

export function asRecord(value: unknown): JsonRecord | undefined {
  if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
    return value as JsonRecord
  }
  return undefined
}

export function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : []
}

export function pick(record: JsonRecord | undefined, ...keys: string[]): unknown {
  if (!record) return undefined
  for (const key of keys) {
    const value = record[key]
    if (value !== undefined && value !== null) return value
  }
  return undefined
}

export function readString(record: JsonRecord | undefined, ...keys: string[]): string | undefined {
  const value = pick(record, ...keys)
  if (typeof value === 'string') return value
  if (typeof value === 'number') return String(value)
  return undefined
}

export function readNumber(record: JsonRecord | undefined, ...keys: string[]): number | undefined {
  const value = pick(record, ...keys)
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string') {
    const parsed = Number(value)
    if (Number.isFinite(parsed)) return parsed
  }
  return undefined
}

export function readBoolean(record: JsonRecord | undefined, ...keys: string[]): boolean | undefined {
  const value = pick(record, ...keys)
  if (typeof value === 'boolean') return value
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    if (['true', 'pass', 'passed', 'ok', 'yes'].includes(normalized)) return true
    if (['false', 'fail', 'failed', 'no'].includes(normalized)) return false
  }
  return undefined
}

export function readRecord(record: JsonRecord | undefined, ...keys: string[]): JsonRecord | undefined {
  return asRecord(pick(record, ...keys))
}

export function readRecordList(record: JsonRecord | undefined, ...keys: string[]): JsonRecord[] {
  return asArray(pick(record, ...keys))
    .map(asRecord)
    .filter((item): item is JsonRecord => item !== undefined)
}

export function readStringList(record: JsonRecord | undefined, ...keys: string[]): string[] {
  return asArray(pick(record, ...keys)).filter((item): item is string => typeof item === 'string')
}
