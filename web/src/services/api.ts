/* API Service client connecting to SlothSwitch backend */

import type {
  BenchmarkData,
  DashboardStats,
  InteractiveScenario,
  ModelsInfo,
  TraceRecord,
  WorkflowData,
} from '../types'

const API_BASE = '/api/v1'

export async function fetchHealth(): Promise<any> {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`)
  return res.json()
}

export async function fetchOverview(): Promise<{
  stats: DashboardStats
  recent_traces: TraceRecord[]
  workflows: string[]
  models: { decision: string; generative: string }
}> {
  const res = await fetch(`${API_BASE}/overview`)
  if (!res.ok) throw new Error(`Failed to fetch overview: ${res.statusText}`)
  return res.json()
}

export async function fetchWorkflows(): Promise<{ workflows: WorkflowData[] }> {
  const res = await fetch(`${API_BASE}/workflows`)
  if (!res.ok) throw new Error(`Failed to fetch workflows: ${res.statusText}`)
  return res.json()
}

export async function fetchPolicies(): Promise<any> {
  const res = await fetch(`${API_BASE}/policies`)
  if (!res.ok) throw new Error(`Failed to fetch policies: ${res.statusText}`)
  return res.json()
}

export async function fetchTraces(filters?: {
  outcome?: string
  workflow?: string
}): Promise<{ traces: TraceRecord[]; total_traces: number }> {
  const params = new URLSearchParams()
  if (filters?.outcome) params.set('outcome', filters.outcome)
  if (filters?.workflow) params.set('workflow', filters.workflow)

  const url = `${API_BASE}/traces${params.toString() ? `?${params.toString()}` : ''}`
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Failed to fetch traces: ${res.statusText}`)
  return res.json()
}

export async function fetchBenchmarks(): Promise<BenchmarkData> {
  const res = await fetch(`${API_BASE}/benchmarks`)
  if (!res.ok) throw new Error(`Failed to fetch benchmarks: ${res.statusText}`)
  return res.json()
}

export async function fetchScenarios(): Promise<{ scenarios: InteractiveScenario[] }> {
  const res = await fetch(`${API_BASE}/benchmarks/scenarios`)
  if (!res.ok) throw new Error(`Failed to fetch scenarios: ${res.statusText}`)
  return res.json()
}

export async function fetchModels(): Promise<ModelsInfo> {
  const res = await fetch(`${API_BASE}/models`)
  if (!res.ok) throw new Error(`Failed to fetch models: ${res.statusText}`)
  return res.json()
}

export async function submitRouteRequest(payload: {
  content: string
  workflow_name: string
  parameters?: Record<string, any>
  caller_permissions?: string[]
}): Promise<TraceRecord> {
  const res = await fetch(`${API_BASE}/route`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }))
    throw new Error(err.error || `Routing failed with status ${res.status}`)
  }
  return res.json()
}
