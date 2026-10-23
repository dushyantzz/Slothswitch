import React from 'react'
import {
  Activity,
  Zap,
  Cpu,
  ShieldAlert,
  UserCheck,
} from 'lucide-react'
import type { DashboardStats, TraceRecord } from '../../types'

interface OverviewViewProps {
  stats: DashboardStats
  recentTraces: TraceRecord[]
  onSelectTrace: (trace: TraceRecord) => void
  onNavigateToPlayground: () => void
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  stats,
  recentTraces,
  onSelectTrace,
  onNavigateToPlayground,
}) => {
  return (
    <div>
      {/* Top Welcome & Quick Action */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
          marginBottom: '28px',
        }}
      >
        <div>
          <h2
            className="font-display"
            style={{ fontSize: '24px', fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}
          >
            System Overview & Metrics
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--color-ash)' }}>
            Real-time telemetry across registered workflows, policy authorization gates, and model inference paths.
          </p>
        </div>

        <button
          onClick={onNavigateToPlayground}
          className="btn-primary"
          style={{ padding: '9px 18px', fontSize: '13px' }}
        >
          <Zap size={14} /> New Request Routing
        </button>
      </div>

      {/* KPI Metric Cards Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          marginBottom: '28px',
        }}
      >
        {/* Total Requests */}
        <div className="card-charcoal" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={kpiLabelStyle}>Total Evaluated</span>
            <Activity size={16} color="var(--color-smoke)" />
          </div>
          <div style={kpiValueStyle}>{stats.total_requests}</div>
          <div style={{ fontSize: '12px', color: 'var(--color-ash)', marginTop: '4px' }}>
            Requests processed through pipeline
          </div>
        </div>

        {/* Avoided Generative Calls */}
        <div className="card-charcoal card-glow-iris" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={kpiLabelStyle}>Avoided Gen Calls</span>
            <span className="tag-chip tag-green" style={{ fontSize: '10px' }}>
              +{stats.avoided_generative_pct}%
            </span>
          </div>
          <div style={{ ...kpiValueStyle, color: '#4ade80' }}>
            {stats.avoided_generative_calls}{' '}
            <span style={{ fontSize: '14px', color: 'var(--color-ash)', fontWeight: 400 }}>
              / {stats.total_requests}
            </span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--color-ash)', marginTop: '4px' }}>
            Bypassed generative LLM expenditure
          </div>
        </div>

        {/* Direct Tool Executions */}
        <div className="card-charcoal" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={kpiLabelStyle}>Direct Tool Executions</span>
            <Zap size={16} color="#79a2f2" />
          </div>
          <div style={kpiValueStyle}>{stats.direct_tool_executions}</div>
          <div style={{ fontSize: '12px', color: 'var(--color-ash)', marginTop: '4px' }}>
            Deterministic REST & system calls
          </div>
        </div>

        {/* Generative LLM Calls */}
        <div className="card-charcoal" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={kpiLabelStyle}>Generative LLM Calls</span>
            <Cpu size={16} color="#ffa185" />
          </div>
          <div style={kpiValueStyle}>{stats.generative_calls}</div>
          <div style={{ fontSize: '12px', color: 'var(--color-ash)', marginTop: '4px' }}>
            Gemma 2 2B synthesis requests
          </div>
        </div>

        {/* Policy Abstentions */}
        <div className="card-charcoal" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={kpiLabelStyle}>Policy Interceptions</span>
            <ShieldAlert size={16} color="#ff8964" />
          </div>
          <div style={{ ...kpiValueStyle, color: '#ffa185' }}>{stats.policy_abstentions}</div>
          <div style={{ fontSize: '12px', color: 'var(--color-ash)', marginTop: '4px' }}>
            Security boundaries enforced
          </div>
        </div>

        {/* Human Approvals Required */}
        <div className="card-charcoal" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span style={kpiLabelStyle}>Approval Pauses</span>
            <UserCheck size={16} color="#fbbf24" />
          </div>
          <div style={{ ...kpiValueStyle, color: '#fbbf24' }}>{stats.human_approvals_required}</div>
          <div style={{ fontSize: '12px', color: 'var(--color-ash)', marginTop: '4px' }}>
            Mutating operations gated
          </div>
        </div>
      </div>

      {/* Model Health Status Cards */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '16px',
          marginBottom: '28px',
        }}
      >
        {/* Laya Model Status */}
        <div className="card-charcoal" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#4ade80' }} />
              <strong style={{ fontSize: '14px', color: '#ffffff' }}>convaiinnovations/laya</strong>
            </div>
            <span className="tag-chip tag-iris">Decision Router</span>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--color-ash)', lineHeight: 1.5, marginBottom: '12px' }}>
            ModernBERT checkpoint loaded in PyTorch. Maps unstructured user queries to structured workflow actions with 91.7% strict accuracy.
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--color-smoke)', fontFamily: 'var(--font-mono)' }}>
            <span>Precision: float32</span>
            <span>Median Latency: 1,226 ms (CPU)</span>
          </div>
        </div>

        {/* Gemma 2 2B Status */}
        <div className="card-charcoal" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#4ade80' }} />
              <strong style={{ fontSize: '14px', color: '#ffffff' }}>google/gemma-2-2b-it</strong>
            </div>
            <span className="tag-chip tag-ember">Generative Model</span>
          </div>
          <div style={{ fontSize: '13px', color: 'var(--color-ash)', lineHeight: 1.5, marginBottom: '12px' }}>
            Native PyTorch <code>bfloat16</code> causal language model. Generates summaries, drafts, and responses only when direct tools cannot satisfy request.
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--color-smoke)', fontFamily: 'var(--font-mono)' }}>
            <span>Precision: bfloat16 native</span>
            <span>Load Time: 6.0s (30.5× speedup)</span>
          </div>
        </div>
      </div>

      {/* Recent Execution Traces Table */}
      <div className="card-charcoal" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
          <div>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '17px', fontWeight: 600, color: '#ffffff' }}>
              Recent Execution Traces
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--color-ash)' }}>
              Click any execution trace to inspect step-by-step pipeline resolution
            </span>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-slate-edge)', color: 'var(--color-smoke)' }}>
                <th style={{ padding: '10px 14px', fontWeight: 500 }}>ID</th>
                <th style={{ padding: '10px 14px', fontWeight: 500 }}>Request Query</th>
                <th style={{ padding: '10px 14px', fontWeight: 500 }}>Workflow</th>
                <th style={{ padding: '10px 14px', fontWeight: 500 }}>Selected Action</th>
                <th style={{ padding: '10px 14px', fontWeight: 500 }}>Outcome</th>
                <th style={{ padding: '10px 14px', fontWeight: 500 }}>Route Path</th>
                <th style={{ padding: '10px 14px', fontWeight: 500 }}>Total Latency</th>
              </tr>
            </thead>
            <tbody>
              {recentTraces.map((trace) => {
                const outcomeClass =
                  trace.policy_outcome === 'EXECUTE_TOOL'
                    ? 'tag-green'
                    : trace.policy_outcome === 'USE_GENERATIVE_MODEL'
                    ? 'tag-ember'
                    : trace.policy_outcome === 'ABSTAIN'
                    ? 'tag-amber'
                    : 'tag-iris'

                return (
                  <tr
                    key={trace.trace_id}
                    onClick={() => onSelectTrace(trace)}
                    style={{
                      borderBottom: '1px solid rgba(74, 75, 80, 0.4)',
                      cursor: 'pointer',
                      transition: 'background 0.15s ease',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)')}
                    onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                  >
                    <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', color: '#79a2f2' }}>
                      {trace.trace_id}
                    </td>
                    <td style={{ padding: '12px 14px', maxWidth: '280px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#ffffff' }}>
                      {trace.request_content}
                    </td>
                    <td style={{ padding: '12px 14px', color: 'var(--color-ash)' }}>
                      {trace.workflow_name}
                    </td>
                    <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', color: '#ffffff' }}>
                      {trace.selected_action}
                    </td>
                    <td style={{ padding: '12px 14px' }}>
                      <span className={`tag-chip ${outcomeClass}`}>{trace.policy_outcome}</span>
                    </td>
                    <td style={{ padding: '12px 14px', fontSize: '12px', color: 'var(--color-ash)' }}>
                      {trace.route_path}
                    </td>
                    <td style={{ padding: '12px 14px', fontFamily: 'var(--font-mono)', color: 'var(--color-smoke)' }}>
                      {trace.total_e2e_ms ? `${trace.total_e2e_ms.toFixed(1)} ms` : '< 1 ms'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

const kpiLabelStyle: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--color-smoke)',
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
  fontWeight: 600,
}
const kpiValueStyle: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '28px',
  fontWeight: 700,
  color: '#ffffff',
}
