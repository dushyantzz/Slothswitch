import React, { useState } from 'react'
import type { WorkflowData } from '../../types'

interface PoliciesViewProps {
  workflows: WorkflowData[]
}

export const PoliciesView: React.FC<PoliciesViewProps> = ({ workflows }) => {
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>(
    workflows.length > 0 ? workflows[0].name : 'github_pr_management'
  )

  const activeWf = workflows.find((w) => w.name === selectedWorkflow) || workflows[0]

  const securityRules = [
    {
      id: 'SEC-001',
      title: 'Prohibited Repository Administration',
      desc: 'Requests targeting repo visibility alteration, administrative ownership transfer, billing modifications, or force-deletion are intercepted and rejected with ABSTAIN.',
      enforcement: 'Deterministic Pre-Execution Regex Gate',
      outcome: 'ABSTAIN',
      badgeClass: 'tag-amber',
    },
    {
      id: 'SEC-002',
      title: 'Human-in-the-Loop Approval for State Mutations',
      desc: 'Actions that modify external state (merging PRs, closing issues, cleaning disk caches) pause execution and yield HUMAN_REVIEW awaiting manual approval.',
      enforcement: 'WorkflowPolicy Gate',
      outcome: 'HUMAN_REVIEW',
      badgeClass: 'tag-ember',
    },
    {
      id: 'SEC-003',
      title: 'Schema Parameter Validation Gate',
      desc: 'If mandatory action parameters (such as pull_number or repo) are absent from caller context, the request enters conversational clarification rather than guessing.',
      enforcement: 'Pydantic Schema Gate',
      outcome: 'CLARIFY',
      badgeClass: 'tag-iris',
    },
    {
      id: 'SEC-004',
      title: 'Generative Model Boundary',
      desc: 'Generative models are only engaged for creative drafting, natural language summarization, or synthesis. Structured factual lookups never invoke generative LLMs.',
      enforcement: 'Laya Router Classification',
      outcome: 'USE_GENERATIVE_MODEL',
      badgeClass: 'tag-iris',
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 className="font-display" style={{ fontSize: '24px', fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}>
          Workflow Schemas & Policy Inspector
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--color-ash)' }}>
          Read-only governance interface inspecting registered actions, required permissions, mutating gates, and security rules.
        </p>
      </div>

      {/* Security Policies Overview */}
      <div style={{ marginBottom: '32px' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 600, color: '#ffffff', marginBottom: '14px' }}>
          Active Deterministic Security Rules
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          {securityRules.map((rule) => (
            <div key={rule.id} className="card-charcoal" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span className="tag-chip tag-ash" style={{ fontFamily: 'var(--font-mono)' }}>
                  {rule.id}
                </span>
                <span className={`tag-chip ${rule.badgeClass}`}>{rule.outcome}</span>
              </div>
              <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '15px', fontWeight: 600, color: '#ffffff', marginBottom: '6px' }}>
                {rule.title}
              </h4>
              <p style={{ fontSize: '12px', color: 'var(--color-ash)', lineHeight: 1.5, marginBottom: '12px' }}>
                {rule.desc}
              </p>
              <div style={{ fontSize: '11px', color: 'var(--color-smoke)', fontFamily: 'var(--font-mono)' }}>
                Enforcement: {rule.enforcement}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Workflow Actions Registry */}
      <div className="card-charcoal" style={{ padding: '24px' }}>
        {/* Workflow Selector Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
          <div>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '17px', fontWeight: 600, color: '#ffffff' }}>
              Registered Workflow Actions
            </h3>
            <span style={{ fontSize: '12px', color: 'var(--color-ash)' }}>
              Inspecting active schema contracts in WorkflowRegistry
            </span>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            {workflows.map((wf) => (
              <button
                key={wf.name}
                onClick={() => setSelectedWorkflow(wf.name)}
                style={{
                  background: selectedWorkflow === wf.name ? 'var(--color-electric-iris)' : '#090a0c',
                  color: selectedWorkflow === wf.name ? '#ffffff' : 'var(--color-smoke)',
                  border: '1px solid',
                  borderColor: selectedWorkflow === wf.name ? 'transparent' : 'var(--color-slate-edge)',
                  borderRadius: '9999px',
                  padding: '6px 16px',
                  fontSize: '12px',
                  fontFamily: 'var(--font-inter)',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                {wf.name} ({wf.actions_count} actions)
              </button>
            ))}
          </div>
        </div>

        {/* Actions List */}
        {activeWf && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {activeWf.actions.map((act) => (
              <div
                key={act.action_id}
                style={{
                  background: '#090a0c',
                  border: '1px solid var(--color-slate-edge)',
                  borderRadius: '8px',
                  padding: '16px 20px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <code style={{ fontSize: '14px', color: '#79a2f2', fontWeight: 600 }}>{act.action_id}</code>
                    {act.is_mutating ? (
                      <span className="tag-chip tag-ember" style={{ fontSize: '10px' }}>Mutating</span>
                    ) : (
                      <span className="tag-chip tag-ash" style={{ fontSize: '10px' }}>Read-Only</span>
                    )}
                    {act.requires_approval && (
                      <span className="tag-chip tag-amber" style={{ fontSize: '10px' }}>Approval Required</span>
                    )}
                    {act.allows_generative && (
                      <span className="tag-chip tag-iris" style={{ fontSize: '10px' }}>Generative Model</span>
                    )}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--color-smoke)', fontFamily: 'var(--font-mono)' }}>
                    Permissions: {act.required_permissions.join(', ') || 'none'}
                  </div>
                </div>

                <p style={{ fontSize: '13px', color: 'var(--color-ash)', marginBottom: '10px', lineHeight: 1.5 }}>
                  {act.description}
                </p>

                {/* Schema properties */}
                {act.parameters_schema?.properties && (
                  <div style={{ background: '#111111', borderRadius: '6px', padding: '10px 14px', fontSize: '12px' }}>
                    <span style={{ color: 'var(--color-smoke)', textTransform: 'uppercase', fontSize: '10px', display: 'block', marginBottom: '4px' }}>
                      Accepted Parameters:
                    </span>
                    <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                      {Object.entries(act.parameters_schema.properties).map(([key, val]: [string, any]) => (
                        <div key={key}>
                          <span style={{ color: '#ffffff', fontFamily: 'var(--font-mono)' }}>{key}</span>
                          <span style={{ color: 'var(--color-smoke)' }}> ({val.type || 'any'})</span>
                          {act.parameters_schema.required?.includes(key) && (
                            <span style={{ color: '#ff8964', marginLeft: '4px' }}>*required</span>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
