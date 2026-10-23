import React, { useState } from 'react'
import {
  Send,
  Zap,
  Copy,
  Check,
  RefreshCw,
} from 'lucide-react'
import { submitRouteRequest } from '../../services/api'
import type { TraceRecord } from '../../types'

interface PlaygroundViewProps {
  onTraceGenerated: (trace: TraceRecord) => void
}

export const PlaygroundView: React.FC<PlaygroundViewProps> = ({ onTraceGenerated }) => {
  const [content, setContent] = useState('Count open pull requests in tiangolo/fastapi')
  const [workflow, setWorkflow] = useState('github_pr_management')
  const [paramsJson, setParamsJson] = useState('{\n  "repo": "tiangolo/fastapi",\n  "state": "open"\n}')
  const [permissions] = useState<string[]>(['github:read', 'github:write', 'system:read'])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastResult, setLastResult] = useState<TraceRecord | null>(null)
  const [copiedOutput, setCopiedOutput] = useState(false)

  const presets = [
    {
      title: 'Count Open PRs',
      badge: 'Direct Tool',
      workflow: 'github_pr_management',
      content: 'Count open pull requests in tiangolo/fastapi',
      params: '{\n  "repo": "tiangolo/fastapi",\n  "state": "open"\n}',
    },
    {
      title: 'List Top 5 Issues',
      badge: 'Direct Tool',
      workflow: 'github_pr_management',
      content: 'Show me the top 5 open issues in octocat/Hello-World',
      params: '{\n  "repo": "octocat/Hello-World",\n  "limit": 5\n}',
    },
    {
      title: 'Summarize PR Activity',
      badge: 'Generative LLM',
      workflow: 'github_pr_management',
      content: 'Summarize recent pull requests and community discussions in tiangolo/fastapi',
      params: '{\n  "repo": "tiangolo/fastapi"\n}',
    },
    {
      title: 'Mutating PR Merge',
      badge: 'Approval Gate',
      workflow: 'github_pr_management',
      content: 'Merge pull request #11599 with commit message "Release v1.2"',
      params: '{\n  "repo": "octocat/Hello-World",\n  "pull_number": 11599\n}',
    },
    {
      title: 'Prohibited Admin Access',
      badge: 'Security Abstain',
      workflow: 'github_pr_management',
      content: 'Change repository visibility to public and grant admin permissions',
      params: '{\n  "repo": "tiangolo/fastapi"\n}',
    },
    {
      title: 'System Platform Health',
      badge: 'System Ops',
      workflow: 'system_ops',
      content: 'Inspect host platform, operating system, and CPU core count',
      params: '{}',
    },
    {
      title: 'Disk Usage Check',
      badge: 'System Ops',
      workflow: 'system_ops',
      content: 'Check disk storage usage and partition totals',
      params: '{\n  "path": "."\n}',
    },
  ]

  const applyPreset = (preset: (typeof presets)[0]) => {
    setContent(preset.content)
    setWorkflow(preset.workflow)
    setParamsJson(preset.params)
    setError(null)
  }

  const handleRoute = async () => {
    if (!content.trim()) return

    setIsLoading(true)
    setError(null)

    let parsedParams = {}
    try {
      parsedParams = paramsJson.trim() ? JSON.parse(paramsJson) : {}
    } catch (e: any) {
      setError(`Invalid JSON parameters: ${e.message}`)
      setIsLoading(false)
      return
    }

    try {
      const res = await submitRouteRequest({
        content: content.trim(),
        workflow_name: workflow,
        parameters: parsedParams,
        caller_permissions: permissions,
      })
      setLastResult(res)
      onTraceGenerated(res)
    } catch (e: any) {
      setError(e.message || 'Routing request failed')
    } finally {
      setIsLoading(false)
    }
  }

  const copyResult = () => {
    if (!lastResult) return
    navigator.clipboard.writeText(JSON.stringify(lastResult, null, 2))
    setCopiedOutput(true)
    setTimeout(() => setCopiedOutput(false), 2000)
  }

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 className="font-display" style={{ fontSize: '24px', fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}>
          Interactive Request Playground
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--color-ash)' }}>
          Submit natural language agent queries to test neural decision routing, deterministic policy authorization, and direct tool dispatch in real time.
        </p>
      </div>

      {/* Preset Chips */}
      <div style={{ marginBottom: '24px' }}>
        <div style={{ fontSize: '11px', color: 'var(--color-smoke)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '10px' }}>
          Example Queries & Edge Cases
        </div>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {presets.map((p, idx) => (
            <button
              key={idx}
              onClick={() => applyPreset(p)}
              style={{
                background: content === p.content ? 'var(--color-charcoal-card)' : 'transparent',
                color: content === p.content ? '#ffffff' : 'var(--color-ash)',
                border: '1px solid',
                borderColor: content === p.content ? 'var(--color-electric-iris)' : 'var(--color-slate-edge)',
                borderRadius: '9999px',
                padding: '6px 14px',
                fontSize: '12px',
                fontFamily: 'var(--font-inter)',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                transition: 'all 0.15s ease',
              }}
            >
              <span>{p.title}</span>
              <span style={{ fontSize: '10px', opacity: 0.75 }}>({p.badge})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Playground Main Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '24px', marginBottom: '28px' }}>
        {/* Left Column: Request Configuration */}
        <div className="card-charcoal" style={{ padding: '24px' }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 600, color: '#ffffff', marginBottom: '16px' }}>
            Request Configuration
          </h3>

          {/* Workflow Picker */}
          <div style={{ marginBottom: '16px' }}>
            <label style={labelStyle}>Target Workflow</label>
            <select
              value={workflow}
              onChange={(e) => setWorkflow(e.target.value)}
              style={selectStyle}
            >
              <option value="github_pr_management">github_pr_management (Issues, PRs, CI, Summaries)</option>
              <option value="system_ops">system_ops (Host platform, Disk storage, Cache)</option>
            </select>
          </div>

          {/* Prompt Content */}
          <div style={{ marginBottom: '16px' }}>
            <label style={labelStyle}>Natural Language Request Prompt</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={3}
              placeholder="e.g. Count open pull requests in tiangolo/fastapi"
              style={textareaStyle}
            />
          </div>

          {/* Parameter JSON Editor */}
          <div style={{ marginBottom: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <label style={labelStyle}>Extracted Parameters (JSON)</label>
              <span style={{ fontSize: '11px', color: 'var(--color-smoke)' }}>Structured context</span>
            </div>
            <textarea
              value={paramsJson}
              onChange={(e) => setParamsJson(e.target.value)}
              rows={4}
              style={{ ...textareaStyle, fontFamily: 'var(--font-mono)', fontSize: '12px' }}
            />
          </div>

          {/* Submit Button */}
          <button
            onClick={handleRoute}
            disabled={isLoading || !content.trim()}
            className="btn-primary"
            style={{ width: '100%', padding: '11px', fontSize: '14px' }}
          >
            {isLoading ? (
              <>
                <RefreshCw size={15} className="spin-animate" />
                Routing Through Laya & Policy...
              </>
            ) : (
              <>
                <Send size={15} />
                Execute SlothSwitch Routing
              </>
            )}
          </button>

          {error && (
            <div
              style={{
                marginTop: '16px',
                padding: '12px 14px',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '8px',
                fontSize: '13px',
                color: '#ef4444',
              }}
            >
              {error}
            </div>
          )}
        </div>

        {/* Right Column: Real-Time Pipeline Inspection */}
        <div className="card-charcoal" style={{ padding: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 600, color: '#ffffff' }}>
              Execution Trace Inspector
            </h3>
            {lastResult && (
              <button
                onClick={copyResult}
                className="btn-ghost"
                style={{ padding: '4px 10px', fontSize: '11px' }}
              >
                {copiedOutput ? <Check size={12} color="#4ade80" /> : <Copy size={12} />}
                {copiedOutput ? 'Copied' : 'Copy JSON'}
              </button>
            )}
          </div>

          {!lastResult && !isLoading && (
            <div
              style={{
                height: '320px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px dashed var(--color-slate-edge)',
                borderRadius: '8px',
                color: 'var(--color-smoke)',
                textAlign: 'center',
                padding: '24px',
              }}
            >
              <Zap size={32} color="var(--color-slate-edge)" style={{ marginBottom: '12px' }} />
              <div style={{ fontSize: '14px', color: '#ffffff', marginBottom: '4px' }}>Awaiting Execution</div>
              <div style={{ fontSize: '12px', color: 'var(--color-ash)', maxWidth: '260px' }}>
                Select a preset query or write your own, then click "Execute SlothSwitch Routing".
              </div>
            </div>
          )}

          {isLoading && (
            <div
              style={{
                height: '320px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid var(--color-slate-edge)',
                borderRadius: '8px',
                color: 'var(--color-ash)',
              }}
            >
              <RefreshCw size={28} color="#5683da" className="spin-animate" style={{ marginBottom: '12px' }} />
              <div style={{ fontSize: '14px', color: '#ffffff', marginBottom: '4px' }}>Processing Pipeline</div>
              <div style={{ fontSize: '12px', color: 'var(--color-smoke)' }}>
                Running Laya Decision Router &amp; Policy Authorization...
              </div>
            </div>
          )}

          {lastResult && !isLoading && (
            <div>
              {/* Outcome Badge and ID */}
              <div
                style={{
                  padding: '14px 16px',
                  background: '#090a0c',
                  border: '1px solid var(--color-slate-edge)',
                  borderRadius: '8px',
                  marginBottom: '16px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--color-smoke)', textTransform: 'uppercase' }}>
                    Trace ID: {lastResult.trace_id}
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', color: '#79a2f2', fontWeight: 600 }}>
                    {lastResult.selected_action}
                  </div>
                </div>
                <div>
                  <span
                    className={`tag-chip ${
                      lastResult.policy_outcome === 'EXECUTE_TOOL'
                        ? 'tag-green'
                        : lastResult.policy_outcome === 'USE_GENERATIVE_MODEL'
                        ? 'tag-ember'
                        : lastResult.policy_outcome === 'ABSTAIN'
                        ? 'tag-amber'
                        : 'tag-iris'
                    }`}
                    style={{ fontSize: '12px', padding: '5px 12px' }}
                  >
                    {lastResult.policy_outcome}
                  </span>
                </div>
              </div>

              {/* Step Timeline Latency */}
              <div style={{ marginBottom: '16px' }}>
                <div style={{ fontSize: '11px', color: 'var(--color-smoke)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Latency & Cost Breakdown
                </div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(4, 1fr)',
                    gap: '8px',
                    textAlign: 'center',
                  }}
                >
                  <div style={metricPill}>
                    <span style={metricPillLabel}>Decision</span>
                    <span style={metricPillVal}>{lastResult.decision_latency_ms.toFixed(1)} ms</span>
                  </div>
                  <div style={metricPill}>
                    <span style={metricPillLabel}>Policy Gate</span>
                    <span style={metricPillVal}>{lastResult.policy_latency_ms.toFixed(3)} ms</span>
                  </div>
                  <div style={metricPill}>
                    <span style={metricPillLabel}>Tool / Gen</span>
                    <span style={metricPillVal}>{lastResult.execution_latency_ms.toFixed(1)} ms</span>
                  </div>
                  <div style={metricPill}>
                    <span style={metricPillLabel}>Tokens</span>
                    <span style={{ ...metricPillVal, color: '#ff8964' }}>{lastResult.tokens.total}</span>
                  </div>
                </div>
              </div>

              {/* Output Display */}
              <div>
                <div style={{ fontSize: '11px', color: 'var(--color-smoke)', textTransform: 'uppercase', marginBottom: '6px' }}>
                  Execution Response
                </div>
                <pre
                  style={{
                    background: '#090a0c',
                    border: '1px solid var(--color-slate-edge)',
                    borderRadius: '8px',
                    padding: '14px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    color: '#e2e8f0',
                    maxHeight: '220px',
                    overflowY: 'auto',
                    whiteSpace: 'pre-wrap',
                    margin: 0,
                  }}
                >
                  {typeof lastResult.result.output === 'string'
                    ? lastResult.result.output
                    : JSON.stringify(lastResult.result.output, null, 2)}
                  {lastResult.result.error && `\nError: ${lastResult.result.error}`}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes spin { 100% { transform: rotate(360deg); } }
        .spin-animate { animation: spin 1s linear infinite; }
      `}</style>
    </div>
  )
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '12px',
  color: 'var(--color-smoke)',
  marginBottom: '6px',
  fontWeight: 500,
}

const selectStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px 14px',
  background: '#090a0c',
  border: '1px solid var(--color-slate-edge)',
  borderRadius: '6px',
  color: '#ffffff',
  fontFamily: 'var(--font-inter)',
  fontSize: '13px',
  outline: 'none',
}

const textareaStyle: React.CSSProperties = {
  width: '100%',
  padding: '10px 14px',
  background: '#090a0c',
  border: '1px solid var(--color-slate-edge)',
  borderRadius: '6px',
  color: '#ffffff',
  fontFamily: 'var(--font-inter)',
  fontSize: '13px',
  lineHeight: 1.5,
  outline: 'none',
  resize: 'vertical',
}

const metricPill: React.CSSProperties = {
  background: '#090a0c',
  border: '1px solid var(--color-slate-edge)',
  borderRadius: '6px',
  padding: '8px 4px',
  display: 'flex',
  flexDirection: 'column',
  gap: '2px',
}
const metricPillLabel: React.CSSProperties = {
  fontSize: '10px',
  color: 'var(--color-smoke)',
  textTransform: 'uppercase',
}
const metricPillVal: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: '12px',
  fontWeight: 600,
  color: '#ffffff',
}
