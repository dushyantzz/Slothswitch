import React, { useState } from 'react'
import {
  Search,
  X,
  Copy,
  Check,
} from 'lucide-react'
import type { TraceRecord } from '../../types'

interface TracesViewProps {
  traces: TraceRecord[]
  selectedTrace: TraceRecord | null
  onSelectTrace: (trace: TraceRecord | null) => void
}

export const TracesView: React.FC<TracesViewProps> = ({
  traces,
  selectedTrace,
  onSelectTrace,
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [outcomeFilter, setOutcomeFilter] = useState('ALL')
  const [copiedTrace, setCopiedTrace] = useState(false)

  const outcomes = ['ALL', 'EXECUTE_TOOL', 'USE_GENERATIVE_MODEL', 'ABSTAIN', 'HUMAN_REVIEW', 'CLARIFY']

  const filteredTraces = traces.filter((t) => {
    const matchesSearch =
      t.request_content.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.selected_action.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.trace_id.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesOutcome = outcomeFilter === 'ALL' || t.policy_outcome === outcomeFilter
    return matchesSearch && matchesOutcome
  })

  const copyTraceJson = (t: TraceRecord) => {
    navigator.clipboard.writeText(JSON.stringify(t, null, 2))
    setCopiedTrace(true)
    setTimeout(() => setCopiedTrace(false), 2000)
  }

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 className="font-display" style={{ fontSize: '24px', fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}>
          Execution Traces Explorer
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--color-ash)' }}>
          Detailed audit logs and step-by-step resolution timelines for every agent request routed by SlothSwitch.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div
        className="card-charcoal"
        style={{
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
        }}
      >
        {/* Search */}
        <div style={{ position: 'relative', minWidth: '260px', flex: 1 }}>
          <Search
            size={16}
            color="var(--color-smoke)"
            style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }}
          />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by query, action ID, or trace..."
            style={{
              width: '100%',
              padding: '9px 12px 9px 36px',
              background: '#090a0c',
              border: '1px solid var(--color-slate-edge)',
              borderRadius: '9999px',
              color: '#ffffff',
              fontSize: '13px',
              fontFamily: 'var(--font-inter)',
              outline: 'none',
            }}
          />
        </div>

        {/* Outcome Filter Pills */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {outcomes.map((opt) => (
            <button
              key={opt}
              onClick={() => setOutcomeFilter(opt)}
              style={{
                background: outcomeFilter === opt ? 'var(--color-electric-iris)' : '#090a0c',
                color: outcomeFilter === opt ? '#ffffff' : 'var(--color-smoke)',
                border: '1px solid',
                borderColor: outcomeFilter === opt ? 'transparent' : 'var(--color-slate-edge)',
                borderRadius: '9999px',
                padding: '5px 12px',
                fontSize: '11px',
                fontFamily: 'var(--font-inter)',
                fontWeight: outcomeFilter === opt ? 600 : 400,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {opt}
            </button>
          ))}
        </div>
      </div>

      {/* Traces List Table */}
      <div className="card-charcoal" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-slate-edge)', background: 'rgba(255, 255, 255, 0.02)', color: 'var(--color-smoke)' }}>
                <th style={{ padding: '12px 18px', fontWeight: 500 }}>ID</th>
                <th style={{ padding: '12px 18px', fontWeight: 500 }}>Request Query</th>
                <th style={{ padding: '12px 18px', fontWeight: 500 }}>Workflow</th>
                <th style={{ padding: '12px 18px', fontWeight: 500 }}>Action</th>
                <th style={{ padding: '12px 18px', fontWeight: 500 }}>Outcome</th>
                <th style={{ padding: '12px 18px', fontWeight: 500 }}>Latency</th>
                <th style={{ padding: '12px 18px', fontWeight: 500 }}>Tokens</th>
              </tr>
            </thead>
            <tbody>
              {filteredTraces.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ padding: '40px', textAlign: 'center', color: 'var(--color-ash)' }}>
                    No execution traces match your search filter.
                  </td>
                </tr>
              ) : (
                filteredTraces.map((trace) => {
                  const outcomeBadge =
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
                      <td style={{ padding: '14px 18px', fontFamily: 'var(--font-mono)', color: '#79a2f2' }}>
                        {trace.trace_id}
                      </td>
                      <td style={{ padding: '14px 18px', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: '#ffffff' }}>
                        {trace.request_content}
                      </td>
                      <td style={{ padding: '14px 18px', color: 'var(--color-ash)' }}>
                        {trace.workflow_name}
                      </td>
                      <td style={{ padding: '14px 18px', fontFamily: 'var(--font-mono)', color: '#ffffff' }}>
                        {trace.selected_action}
                      </td>
                      <td style={{ padding: '14px 18px' }}>
                        <span className={`tag-chip ${outcomeBadge}`}>{trace.policy_outcome}</span>
                      </td>
                      <td style={{ padding: '14px 18px', fontFamily: 'var(--font-mono)', color: 'var(--color-smoke)' }}>
                        {trace.total_e2e_ms ? `${trace.total_e2e_ms.toFixed(1)} ms` : '< 1 ms'}
                      </td>
                      <td style={{ padding: '14px 18px', fontFamily: 'var(--font-mono)', color: '#ffda9f' }}>
                        {trace.tokens?.total || 0}
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Trace Timeline Modal */}
      {selectedTrace && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(9, 10, 12, 0.8)',
            backdropFilter: 'blur(8px)',
            zIndex: 200,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
          }}
          onClick={() => onSelectTrace(null)}
        >
          <div
            className="card-charcoal"
            style={{
              maxWidth: '720px',
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '28px',
              position: 'relative',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
              <div>
                <span className="tag-chip tag-iris" style={{ marginBottom: '6px' }}>
                  Trace {selectedTrace.trace_id}
                </span>
                <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 600, color: '#ffffff' }}>
                  Execution Timeline & Resolution
                </h3>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  onClick={() => copyTraceJson(selectedTrace)}
                  className="btn-ghost"
                  style={{ padding: '6px 12px', fontSize: '12px' }}
                >
                  {copiedTrace ? <Check size={13} color="#4ade80" /> : <Copy size={13} />}
                  {copiedTrace ? 'Copied' : 'Copy'}
                </button>
                <button
                  onClick={() => onSelectTrace(null)}
                  style={{ background: 'none', border: 'none', color: 'var(--color-smoke)', cursor: 'pointer', padding: '4px' }}
                >
                  <X size={20} />
                </button>
              </div>
            </div>

            {/* Timeline Steps */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '24px' }}>
              {/* Step 1 */}
              <div style={timelineCardStyle}>
                <div style={timelineStepHeader}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: '#5683da', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>1</div>
                    <strong style={{ color: '#ffffff', fontSize: '13px' }}>Request Received</strong>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--color-smoke)' }}>Workflow: {selectedTrace.workflow_name}</span>
                </div>
                <div style={{ padding: '10px 14px', background: '#090a0c', borderRadius: '6px', fontSize: '13px', color: '#e2e8f0', marginTop: '8px' }}>
                  "{selectedTrace.request_content}"
                </div>
              </div>

              {/* Step 2 */}
              <div style={timelineCardStyle}>
                <div style={timelineStepHeader}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: '#ff8964', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>2</div>
                    <strong style={{ color: '#ffffff', fontSize: '13px' }}>Laya Decision Router</strong>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--color-smoke)', fontFamily: 'var(--font-mono)' }}>
                    ⏱ {selectedTrace.decision_latency_ms?.toFixed(1) || 0} ms
                  </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '8px', fontSize: '12px' }}>
                  <div>Proposed Action: <code style={{ color: '#79a2f2' }}>{selectedTrace.selected_action}</code></div>
                  <div>Model: <span style={{ color: 'var(--color-ash)' }}>{selectedTrace.model_used}</span></div>
                </div>
              </div>

              {/* Step 3 */}
              <div style={timelineCardStyle}>
                <div style={timelineStepHeader}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: '#4ade80', color: '#090a0c', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>3</div>
                    <strong style={{ color: '#ffffff', fontSize: '13px' }}>Workflow Policy Gate</strong>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--color-smoke)', fontFamily: 'var(--font-mono)' }}>
                    ⏱ {selectedTrace.policy_latency_ms?.toFixed(3) || 0} ms
                  </span>
                </div>
                <div style={{ marginTop: '8px', fontSize: '12px' }}>
                  Outcome Authorized:{' '}
                  <span style={{ fontWeight: 600, color: '#4ade80' }}>{selectedTrace.policy_outcome}</span>
                  {selectedTrace.policy_reason && (
                    <div style={{ color: 'var(--color-ash)', marginTop: '4px' }}>
                      Reason: {selectedTrace.policy_reason}
                    </div>
                  )}
                </div>
              </div>

              {/* Step 4 */}
              <div style={timelineCardStyle}>
                <div style={timelineStepHeader}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ width: '22px', height: '22px', borderRadius: '50%', background: '#a5b4fc', color: '#090a0c', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700 }}>4</div>
                    <strong style={{ color: '#ffffff', fontSize: '13px' }}>Execution Result</strong>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--color-smoke)', fontFamily: 'var(--font-mono)' }}>
                    ⏱ {selectedTrace.execution_latency_ms?.toFixed(1) || 0} ms
                  </span>
                </div>
                <pre
                  style={{
                    background: '#090a0c',
                    border: '1px solid var(--color-slate-edge)',
                    borderRadius: '6px',
                    padding: '12px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    color: '#e2e8f0',
                    marginTop: '8px',
                    maxHeight: '160px',
                    overflowY: 'auto',
                    whiteSpace: 'pre-wrap',
                  }}
                >
                  {typeof selectedTrace.result.output === 'string'
                    ? selectedTrace.result.output
                    : JSON.stringify(selectedTrace.result.output, null, 2)}
                  {selectedTrace.result.error && `\nError: ${selectedTrace.result.error}`}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const timelineCardStyle: React.CSSProperties = {
  background: '#111111',
  border: '1px solid var(--color-slate-edge)',
  borderRadius: '8px',
  padding: '14px',
}

const timelineStepHeader: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
}
