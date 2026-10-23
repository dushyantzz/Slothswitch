import React from 'react'
import { Lock, Key } from 'lucide-react'

export const SettingsView: React.FC = () => {
  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h2 className="font-display" style={{ fontSize: '24px', fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}>
          System Configuration & Settings
        </h2>
        <p style={{ fontSize: '13px', color: 'var(--color-ash)' }}>
          Operational parameters and non-secret credential indicators. All credentials remain secure on the backend server.
        </p>
      </div>

      {/* Security Credentials Status Card */}
      <div className="card-charcoal" style={{ padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
          <Lock size={18} color="#4ade80" />
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 600, color: '#ffffff' }}>
            Credential Security & Isolation
          </h3>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--color-ash)', lineHeight: 1.5, marginBottom: '20px' }}>
          Per security requirements, API tokens and HuggingFace credentials are strictly stored in local environment variables or <code>.env</code> on the server. They are never rendered or transmitted to browser bundles.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          <div style={secretStatusBox}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Key size={14} color="#79a2f2" /> HF_TOKEN
              </span>
              <span className="tag-chip tag-green" style={{ fontSize: '10px' }}>Configured Server-Side</span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--color-smoke)' }}>
              Grants gated model access to <code>google/gemma-2-2b-it</code> on HuggingFace Hub.
            </div>
          </div>

          <div style={secretStatusBox}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Key size={14} color="#79a2f2" /> GITHUB_TOKEN
              </span>
              <span className="tag-chip tag-green" style={{ fontSize: '10px' }}>Configured Server-Side</span>
            </div>
            <div style={{ fontSize: '12px', color: 'var(--color-smoke)' }}>
              Enables authenticated GitHub REST API v3 tool calls without rate limiting.
            </div>
          </div>
        </div>
      </div>

      {/* Engine Parameters Card */}
      <div className="card-charcoal" style={{ padding: '24px' }}>
        <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: 600, color: '#ffffff', marginBottom: '16px' }}>
          WorkflowPolicy Engine Parameters
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={paramRow}>
            <div>
              <div style={{ fontWeight: 600, color: '#ffffff', fontSize: '13px' }}>Decision Confidence Threshold</div>
              <div style={{ fontSize: '12px', color: 'var(--color-ash)' }}>Minimum confidence score required before proposing action</div>
            </div>
            <span style={paramValBadge}>0.55</span>
          </div>

          <div style={paramRow}>
            <div>
              <div style={{ fontWeight: 600, color: '#ffffff', fontSize: '13px' }}>Approval Gate for Mutating Actions</div>
              <div style={{ fontSize: '12px', color: 'var(--color-ash)' }}>Pauses mutating state modifications for human review</div>
            </div>
            <span className="tag-chip tag-green">Enforced</span>
          </div>

          <div style={paramRow}>
            <div>
              <div style={{ fontWeight: 600, color: '#ffffff', fontSize: '13px' }}>Read-Only Mode Isolation</div>
              <div style={{ fontSize: '12px', color: 'var(--color-ash)' }}>Strictly disables all mutating tool executions</div>
            </div>
            <span className="tag-chip tag-ash">Disabled (Standard)</span>
          </div>

          <div style={paramRow}>
            <div>
              <div style={{ fontWeight: 600, color: '#ffffff', fontSize: '13px' }}>Action Execution Timeout</div>
              <div style={{ fontSize: '12px', color: 'var(--color-ash)' }}>Maximum per-action execution deadline</div>
            </div>
            <span style={paramValBadge}>30.0 seconds</span>
          </div>
        </div>
      </div>
    </div>
  )
}

const secretStatusBox: React.CSSProperties = {
  background: '#090a0c',
  border: '1px solid var(--color-slate-edge)',
  borderRadius: '8px',
  padding: '16px',
}

const paramRow: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  paddingBottom: '12px',
  borderBottom: '1px solid rgba(74, 75, 80, 0.4)',
}

const paramValBadge: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: '13px',
  fontWeight: 600,
  color: '#79a2f2',
  background: '#090a0c',
  padding: '4px 10px',
  borderRadius: '6px',
  border: '1px solid var(--color-slate-edge)',
}
