/* TypeScript data definitions for SlothSwitch */

export type RouteCategory =
  | 'FAST_PATH'
  | 'SMALL_LLM'
  | 'LARGE_LLM'
  | 'CLARIFY'
  | 'FALLBACK'
  | 'HUMAN_REVIEW'

export type DecisionOutcome =
  | 'EXECUTE_TOOL'
  | 'USE_GENERATIVE_MODEL'
  | 'CLARIFY'
  | 'ABSTAIN'
  | 'HUMAN_REVIEW'
  | 'FALLBACK'

export interface ActionDefinitionData {
  action_id: string
  description: string
  parameters_schema: Record<string, any>
  required_permissions: string[]
  is_mutating: boolean
  requires_approval: boolean
  allows_generative: boolean
  is_direct_execution: boolean
}

export interface WorkflowData {
  name: string
  description: string
  version: string
  actions_count: number
  actions: ActionDefinitionData[]
}

export interface TraceRecord {
  trace_id: string
  timestamp: number
  request_content: string
  workflow_name: string
  selected_action: string
  decision_confidence?: number
  parameters: Record<string, any>
  policy_outcome: DecisionOutcome | string
  policy_reason?: string
  model_used: string
  route_path: string
  decision_latency_ms: number
  policy_latency_ms: number
  execution_latency_ms: number
  total_e2e_ms: number
  tokens: {
    input: number
    output: number
    total: number
  }
  result: {
    success: boolean
    output?: any
    error?: string | null
  }
  status: 'SUCCEEDED' | 'FAILED' | 'ABSTAINED' | 'WAITING_FOR_APPROVAL' | 'CLARIFICATION_NEEDED'
}

export interface DashboardStats {
  total_requests: number
  direct_tool_executions: number
  generative_calls: number
  avoided_generative_calls: number
  avoided_generative_pct: number
  policy_abstentions: number
  human_approvals_required: number
  clarifications_requested: number
}

export interface BenchmarkBaseline {
  baseline: string
  description: string
  strict_action_accuracy: number
  strict_action_numerator: number
  strict_action_denominator: number
  outcome_accuracy: number
  outcome_numerator: number
  outcome_denominator: number
  task_success_rate: number
  task_success_numerator: number
  task_success_denominator: number
  generative_calls: number
  avoided_generative_calls: number
  avoided_generative_pct: number
  total_generative_tokens: number
  median_latency_ms: number
  p95_latency_ms: number
  median_decision_latency_ms?: number
  median_policy_latency_ms?: number
}

export interface BenchmarkData {
  benchmark_info: {
    dataset: string
    total_samples: number
    test_split_samples: number
    target_repositories: string[]
    evaluation_date: string
    models_evaluated: {
      decision: string
      generative: string
    }
  }
  comparison: BenchmarkBaseline[]
  sample_records: any[]
}

export interface ModelsInfo {
  decision_model: {
    id: string
    architecture: string
    status: string
    precision: string
    device: string
    median_decision_time_ms: number
    description: string
  }
  generative_model: {
    id: string
    architecture: string
    status: string
    precision: string
    device: string
    load_time_seconds: number
    tokens_per_second: number
    description: string
  }
  runtime_environment: {
    python_version: string
    platform: string
    hf_auth_status: string
    local_checkpoint_path: string
  }
}

export interface ScenarioBaselineResult {
  route: string
  action?: string
  model: string
  tokens: number
  latency_ms?: number
  task_success: boolean
  output_type?: string
  summary: string
  trace_status: string
  policy_outcome?: string
  policy_latency_ms?: number
  decision_latency_ms?: number
  tool_latency_ms?: number
  total_latency_ms?: number
  output?: any
}

export interface InteractiveScenario {
  id: string
  name: string
  prompt: string
  category: string
  audit_request_id: string
  always_generative: ScenarioBaselineResult
  deterministic_rules: ScenarioBaselineResult
  slothswitch: ScenarioBaselineResult
}
