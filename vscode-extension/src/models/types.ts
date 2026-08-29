export interface IncidentItem {
  id: string
  incident_number: number
  title: string
  status: string
  endpoint?: string
  http_method?: string
  observed_status_code?: number
  fingerprint?: string
}

export interface FailureDNA {
  fingerprint: string
  trigger?: string
  exception_class?: string
  failure_point?: string
  dependency_type?: string
  recurrence_count?: number
}

export interface RepairCandidate {
  id: string
  label: string
  description: string
  diff: string
  is_recommended: boolean
  final_status: string
}

export interface RegressionGuard {
  id: string
  fingerprint: string
  test_name: string
  test_path: string
  validation_status: string
  is_active: boolean
}
