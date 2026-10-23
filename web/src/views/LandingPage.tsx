import React, { useState } from 'react'
import {
  Zap,
  Shield,
  Layers,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Lock,
  GitBranch,
  Terminal,
  Activity,
  BarChart3,
  Copy,
  Check,
  ChevronRight,
  Sparkles,
} from 'lucide-react'
import { ProofOfEfficiency } from '../components/ProofOfEfficiency'

interface LandingPageProps {
  onOpenDashboard: () => void
}

export const LandingPage: React.FC<LandingPageProps> = ({ onOpenDashboard }) => {
  const [copiedInstall, setCopiedInstall] = useState(false)
  const [activeHeroExample, setActiveHeroExample] = useState<number>(0)
  const [activeSecurityQuery, setActiveSecurityQuery] = useState<number>(0)

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedInstall(true)
    setTimeout(() => setCopiedInstall(false), 2000)
  }

  const heroExamples = [
    {
      id: 0,
      title: 'Direct Tool Execution',
      badge: 'FAST_PATH',
      badgeClass: 'tag-iris',
      query: 'Count open pull requests in tiangolo/fastapi',
      action: 'count_pull_requests',
      outcome: 'EXECUTE_TOOL',
      route: 'Direct ToolExecutor (GitHub REST API v3)',
      model: 'convaiinnovations/laya (ModernBERT)',
      tokens: '0 generative tokens',
      latency: '1.24s total (1.22s decision, 0.02ms policy, 22ms tool)',
      resultSnippet: '{"repo": "tiangolo/fastapi", "count": 48, "state": "open"}',
    },
    {
      id: 1,
      title: 'Generative Model Escalation',
      badge: 'SMALL_LLM',
      badgeClass: 'tag-ember',
      query: 'Summarize recent PR themes and community contributions',
      action: 'summarize_pull_requests',
      outcome: 'USE_GENERATIVE_MODEL',
      route: 'Local Gemma 2 2B (bfloat16 native)',
      model: 'google/gemma-2-2b-it',
      tokens: '94 tokens (24 prompt, 70 completion)',
      latency: '4.05s total (1.21s decision, 2.84s generation)',
      resultSnippet: '"Recent contributions focus on Pydantic v2 compatibility and typing fixes."',
    },
    {
      id: 2,
      title: 'Security Boundary Abstention',
      badge: 'SECURITY_GATE',
      badgeClass: 'tag-amber',
      query: 'Change repository visibility to public and grant admin access',
      action: 'none',
      outcome: 'ABSTAIN',
      route: 'Deterministic Policy Gate (Interception)',
      model: 'slothswitch_policy_gate',
      tokens: '0 tokens',
      latency: '0.015ms (Deterministic policy gate)',
      resultSnippet: '{"error": "Security gate: repository visibility and administrative modifications are strictly prohibited."}',
    },
  ]

  const securityQueries = [
    {
      query: 'Make repository public and delete production branch',
      decision: 'none',
      outcome: 'ABSTAIN',
      reason: 'Rule SEC-001: Administrative permissions, deletion, and visibility changes prohibited.',
      color: '#ef4444',
    },
    {
      query: 'Merge pull request #11599 with message "Release v1.2"',
      decision: 'merge_pull_request',
      outcome: 'HUMAN_REVIEW',
      reason: 'Rule SEC-002: Mutating action requires verified human authorization before dispatch.',
      color: '#f59e0b',
    },
    {
      query: 'Show pull request details for #16589 in tiangolo/fastapi',
      decision: 'get_pull_request_details',
      outcome: 'EXECUTE_TOOL',
      reason: 'Rule SEC-004: Read-only deterministic lookup authorized with github:read permission.',
      color: '#10b981',
    },
    {
      query: 'Draft a technical release note summarizing recent PRs',
      decision: 'summarize_pull_requests',
      outcome: 'USE_GENERATIVE_MODEL',
      reason: 'Rule SEC-003: Open-ended creative synthesis delegated to bounded local Gemma 2 2B.',
      color: '#5683da',
    },
  ]

  return (
    <div style={{ position: 'relative', overflowX: 'hidden' }}>
      {/* ------------------------------------------------------------- */}
      {/* HERO SECTION (DESIGN.md specifications)                       */}
      {/* ------------------------------------------------------------- */}
      <section
        style={{
          position: 'relative',
          paddingTop: '140px',
          paddingBottom: '96px',
          background: 'var(--color-void)',
          overflow: 'hidden',
          minHeight: '92vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Brand Vertical Aurora Beam (DESIGN.md section 251) */}
        <div className="aurora-beam aurora-animate" />
        <div className="aurora-sunburst" />

        <div
          style={{
            maxWidth: 'var(--page-max-width)',
            width: '100%',
            margin: '0 auto',
            padding: '0 24px',
            position: 'relative',
            zIndex: 1,
            textAlign: 'center',
          }}
        >
          {/* Top Pill Announcement */}
          <div style={{ display: 'inline-flex', marginBottom: '24px' }}>
            <span
              className="tag-chip tag-iris"
              style={{
                padding: '6px 14px',
                fontSize: '12px',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
              }}
              onClick={onOpenDashboard}
            >
              <Sparkles size={13} color="#ff8964" />
              <span>SlothSwitch Benchmark Verified: 87.5% Avoided Generative Calls</span>
              <ChevronRight size={13} />
            </span>
          </div>

          {/* Hero Headline */}
          <h1
            className="font-display"
            style={{
              fontSize: 'var(--text-display)',
              lineHeight: 'var(--leading-display)',
              letterSpacing: 'var(--tracking-display)',
              fontWeight: 700,
              color: '#ffffff',
              maxWidth: '960px',
              margin: '0 auto 24px auto',
            }}
          >
            Make AI agents more efficient.{' '}
            <span
              style={{
                background: 'linear-gradient(135deg, #ffffff 40%, #ff8964 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Keep execution under control.
            </span>
          </h1>

          {/* Supporting Subtitle */}
          <p
            style={{
              fontFamily: 'var(--font-inter)',
              fontSize: 'clamp(16px, 2vw, 19px)',
              lineHeight: 1.6,
              color: 'var(--color-ash)',
              maxWidth: '720px',
              margin: '0 auto 36px auto',
            }}
          >
            SlothSwitch routes agent requests to the right tools, applies runtime policies, and uses generative models when they are actually needed.
          </p>

          {/* Action Buttons */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '16px',
              flexWrap: 'wrap',
              marginBottom: '64px',
            }}
          >
            <button
              onClick={onOpenDashboard}
              className="btn-primary"
              style={{ padding: '12px 28px', fontSize: '15px' }}
            >
              <Zap size={16} />
              Explore the Dashboard
            </button>
            <a
              href="https://github.com/dushyantzz/Slothswitch"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ghost"
              style={{ padding: '12px 26px', fontSize: '15px' }}
            >
              <Terminal size={16} />
              View on GitHub
            </a>
          </div>

          {/* Floating Realistic Product Execution Interface Frame (DESIGN.md section 138) */}
          <div
            className="screenshot-frame"
            style={{
              maxWidth: '880px',
              margin: '0 auto',
              textAlign: 'left',
              border: '1px solid var(--color-slate-edge)',
              boxShadow: '0 20px 50px rgba(0, 0, 0, 0.75), 0 0 30px rgba(86, 131, 218, 0.15)',
            }}
          >
            {/* Window Title Bar */}
            <div
              style={{
                background: '#090a0c',
                padding: '12px 20px',
                borderBottom: '1px solid var(--color-slate-edge)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ff5f56' }} />
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#ffbd2e' }} />
                <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#27c93f' }} />
                <span
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    color: 'var(--color-smoke)',
                    marginLeft: '8px',
                  }}
                >
                  slothswitch-pipeline :: live-trace-inspector
                </span>
              </div>
              <div style={{ display: 'flex', gap: '6px' }}>
                {heroExamples.map((ex) => (
                  <button
                    key={ex.id}
                    onClick={() => setActiveHeroExample(ex.id)}
                    style={{
                      background: activeHeroExample === ex.id ? 'var(--color-electric-iris)' : 'transparent',
                      color: activeHeroExample === ex.id ? '#ffffff' : 'var(--color-smoke)',
                      border: '1px solid',
                      borderColor: activeHeroExample === ex.id ? 'transparent' : 'var(--color-slate-edge)',
                      borderRadius: '9999px',
                      padding: '3px 10px',
                      fontSize: '11px',
                      fontFamily: 'var(--font-inter)',
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    {ex.title}
                  </button>
                ))}
              </div>
            </div>

            {/* Execution Inspector Body */}
            <div style={{ padding: '24px', background: 'var(--color-charcoal-card)' }}>
              {/* Step 1: Input Query */}
              <div style={{ marginBottom: '18px' }}>
                <div style={{ fontSize: '11px', color: 'var(--color-smoke)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Incoming Agent Request
                </div>
                <div
                  style={{
                    background: '#090a0c',
                    border: '1px solid var(--color-slate-edge)',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '14px',
                    color: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <span>"{heroExamples[activeHeroExample].query}"</span>
                  <span className={`tag-chip ${heroExamples[activeHeroExample].badgeClass}`}>
                    {heroExamples[activeHeroExample].badge}
                  </span>
                </div>
              </div>

              {/* Step 2: Routing & Policy Evaluation Grid */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '12px',
                  marginBottom: '18px',
                }}
              >
                <div style={statBoxStyle}>
                  <span style={statBoxLabel}>Selected Action</span>
                  <span style={{ ...statBoxValue, color: '#79a2f2' }}>
                    {heroExamples[activeHeroExample].action}
                  </span>
                </div>

                <div style={statBoxStyle}>
                  <span style={statBoxLabel}>Policy Outcome</span>
                  <span style={{ ...statBoxValue, color: heroExamples[activeHeroExample].outcome === 'ABSTAIN' ? '#ff8964' : '#4ade80' }}>
                    {heroExamples[activeHeroExample].outcome}
                  </span>
                </div>

                <div style={statBoxStyle}>
                  <span style={statBoxLabel}>Execution Route</span>
                  <span style={{ ...statBoxValue, fontSize: '12px' }}>
                    {heroExamples[activeHeroExample].route}
                  </span>
                </div>

                <div style={statBoxStyle}>
                  <span style={statBoxLabel}>Model & Token Cost</span>
                  <span style={{ ...statBoxValue, color: '#ffda9f', fontSize: '12px' }}>
                    {heroExamples[activeHeroExample].tokens}
                  </span>
                </div>
              </div>

              {/* Step 3: Result Output Box */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--color-smoke)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    Execution Result
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--color-ash)', fontFamily: 'var(--font-mono)' }}>
                    ⏱ {heroExamples[activeHeroExample].latency}
                  </span>
                </div>
                <pre
                  style={{
                    background: '#090a0c',
                    border: '1px solid var(--color-slate-edge)',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '12px',
                    color: '#e2e8f0',
                    overflowX: 'auto',
                    margin: 0,
                  }}
                >
                  <code>{heroExamples[activeHeroExample].resultSnippet}</code>
                </pre>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION C: PROBLEM AND SOLUTION (Alternating Light Band)      */}
      {/* ------------------------------------------------------------- */}
      <section id="product" className="section-light-band">
        <div style={{ maxWidth: 'var(--page-max-width)', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 64px auto' }}>
            <span
              className="tag-chip tag-ash"
              style={{ marginBottom: '12px', background: '#e5e5e7', color: '#303236', border: '1px solid #d1d1d1' }}
            >
              The Agent Dilemma
            </span>
            <h2
              className="font-display"
              style={{
                fontSize: 'clamp(30px, 4vw, 44px)',
                lineHeight: 1.15,
                fontWeight: 700,
                color: '#050506',
                marginBottom: '16px',
              }}
            >
              Why generative models should not control every tool invocation.
            </h2>
            <p style={{ fontFamily: 'var(--font-inter)', fontSize: '16px', lineHeight: 1.6 }}>
              Most modern agent architectures force every query through expensive frontier LLMs, causing runaway API costs, unpredictable tool calls, and complete lack of security oversight.
            </p>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
              gap: '24px',
            }}
          >
            {/* Problem 1 */}
            <div className="card-light">
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '10px',
                  background: 'rgba(239, 68, 68, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '20px',
                }}
              >
                <Activity size={22} color="#dc2626" />
              </div>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '20px', fontWeight: 600, marginBottom: '10px' }}>
                1. Unnecessary Generative Inference
              </h3>
              <p style={{ fontSize: '14px', lineHeight: 1.6, marginBottom: '16px' }}>
                Routing simple lookups (e.g. <em>"count open PRs"</em>) to large generative models wastes up to 3,000+ tokens and seconds of latency per call when deterministic APIs return the exact answer in 20 milliseconds.
              </p>
              <div style={{ padding: '12px', background: '#f0f0f2', borderRadius: '8px', fontSize: '12px', color: '#303236', fontWeight: 500 }}>
                💡 <strong>SlothSwitch fix:</strong> Specialized Laya ModernBERT router identifies structured tasks and routes them directly to tools.
              </div>
            </div>

            {/* Problem 2 */}
            <div className="card-light">
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '10px',
                  background: 'rgba(245, 158, 11, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '20px',
                }}
              >
                <AlertTriangle size={22} color="#d97706" />
              </div>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '20px', fontWeight: 600, marginBottom: '10px' }}>
                2. Uncontrolled Tool Execution
              </h3>
              <p style={{ fontSize: '14px', lineHeight: 1.6, marginBottom: '16px' }}>
                Autonomous agents often execute irreversible, mutating actions (closing PRs, modifying permissions, deleting databases) without approval gates or schema validation.
              </p>
              <div style={{ padding: '12px', background: '#f0f0f2', borderRadius: '8px', fontSize: '12px', color: '#303236', fontWeight: 500 }}>
                🛡️ <strong>SlothSwitch fix:</strong> Strict runtime WorkflowPolicy enforces human approval for all stateful actions and hard-abstains on dangerous operations.
              </div>
            </div>

            {/* Problem 3 */}
            <div className="card-light">
              <div
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '10px',
                  background: 'rgba(99, 102, 241, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginBottom: '20px',
                }}
              >
                <Layers size={22} color="#4f46e5" />
              </div>
              <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '20px', fontWeight: 600, marginBottom: '10px' }}>
                3. Black-Box Execution Tracing
              </h3>
              <p style={{ fontSize: '14px', lineHeight: 1.6, marginBottom: '16px' }}>
                Engineering teams struggle to debug agent failures because prompt chains conflate reasoning, authorization, and tool execution into an opaque text blob.
              </p>
              <div style={{ padding: '12px', background: '#f0f0f2', borderRadius: '8px', fontSize: '12px', color: '#303236', fontWeight: 500 }}>
                🔍 <strong>SlothSwitch fix:</strong> Disaggregated telemetry breaks down decision time, policy validation, tool runtime, and token consumption per request.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION D: HOW IT WORKS (Animated Architecture Diagram)       */}
      {/* ------------------------------------------------------------- */}
      <section
        id="how-it-works"
        style={{
          background: 'var(--color-obsidian-canvas)',
          padding: 'var(--spacing-96) 24px',
          borderTop: '1px solid var(--color-slate-edge)',
          borderBottom: '1px solid var(--color-slate-edge)',
        }}
      >
        <div style={{ maxWidth: 'var(--page-max-width)', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 64px auto' }}>
            <span className="tag-chip tag-iris" style={{ marginBottom: '12px' }}>
              Execution Lifecycle
            </span>
            <h2
              className="font-display"
              style={{
                fontSize: 'clamp(30px, 4vw, 44px)',
                lineHeight: 1.15,
                fontWeight: 700,
                color: '#ffffff',
                marginBottom: '16px',
              }}
            >
              How SlothSwitch routes every incoming request.
            </h2>
            <p style={{ fontFamily: 'var(--font-inter)', fontSize: '16px', color: 'var(--color-ash)', lineHeight: 1.6 }}>
              A clean separation of concerns: small neural decision routing, deterministic security authorization, and specialized execution engines.
            </p>
          </div>

          {/* Interactive Flow Diagram */}
          <div
            className="card-charcoal card-glow-amber"
            style={{
              padding: '36px',
              position: 'relative',
              maxWidth: '1080px',
              margin: '0 auto',
            }}
          >
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                gap: '24px',
                position: 'relative',
                zIndex: 1,
              }}
            >
              {/* Step 1 */}
              <div style={flowStepCardStyle}>
                <div style={flowStepNumber}>01</div>
                <h4 style={flowStepTitle}>Incoming Request</h4>
                <p style={flowStepDesc}>
                  Natural language prompt ingested from agent framework, user chat, or webhook. Content is normalized and parameters extracted.
                </p>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#a5b4fc', marginTop: '12px' }}>
                  Input tokens bounded to 256
                </div>
              </div>

              {/* Step 2 */}
              <div style={flowStepCardStyle}>
                <div style={{ ...flowStepNumber, background: 'rgba(86, 131, 218, 0.2)', color: '#79a2f2' }}>02</div>
                <h4 style={flowStepTitle}>Laya Decision Router</h4>
                <p style={flowStepDesc}>
                  ModernBERT router performs fast, non-generative semantic classification across workflow actions. Predicts target action and confidence score.
                </p>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#79a2f2', marginTop: '12px' }}>
                  ~1.22s on CPU (0 generative tokens)
                </div>
              </div>

              {/* Step 3 */}
              <div style={flowStepCardStyle}>
                <div style={{ ...flowStepNumber, background: 'rgba(255, 137, 100, 0.2)', color: '#ffa185' }}>03</div>
                <h4 style={flowStepTitle}>Workflow Policy Gate</h4>
                <p style={flowStepDesc}>
                  Deterministic security engine checks caller permissions, required schema parameters, mutating operation approval gates, and prohibited actions.
                </p>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#ffa185', marginTop: '12px' }}>
                  &lt; 0.05ms deterministic check
                </div>
              </div>
            </div>

            {/* Step 4: Outcomes Terminal */}
            <div style={{ marginTop: '36px', paddingTop: '28px', borderTop: '1px solid var(--color-slate-edge)' }}>
              <div style={{ fontSize: '12px', color: 'var(--color-smoke)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
                Five Deterministic Outcome Terminals
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: '12px',
                }}
              >
                <div style={terminalCardStyle}>
                  <div style={{ color: '#4ade80', fontWeight: 600, fontSize: '13px', marginBottom: '4px' }}>EXECUTE_TOOL</div>
                  <div style={{ fontSize: '12px', color: 'var(--color-ash)' }}>Dispatches directly to registered ToolExecutor</div>
                </div>
                <div style={terminalCardStyle}>
                  <div style={{ color: '#5683da', fontWeight: 600, fontSize: '13px', marginBottom: '4px' }}>USE_GENERATIVE</div>
                  <div style={{ fontSize: '12px', color: 'var(--color-ash)' }}>Escalates to local Gemma 2 2B for summarization</div>
                </div>
                <div style={terminalCardStyle}>
                  <div style={{ color: '#fbbf24', fontWeight: 600, fontSize: '13px', marginBottom: '4px' }}>HUMAN_REVIEW</div>
                  <div style={{ fontSize: '12px', color: 'var(--color-ash)' }}>Pauses mutating action for explicit approval</div>
                </div>
                <div style={terminalCardStyle}>
                  <div style={{ color: '#f97316', fontWeight: 600, fontSize: '13px', marginBottom: '4px' }}>CLARIFY</div>
                  <div style={{ fontSize: '12px', color: 'var(--color-ash)' }}>Prompts caller for missing required parameters</div>
                </div>
                <div style={terminalCardStyle}>
                  <div style={{ color: '#ef4444', fontWeight: 600, fontSize: '13px', marginBottom: '4px' }}>ABSTAIN</div>
                  <div style={{ fontSize: '12px', color: 'var(--color-ash)' }}>Hard rejection of prohibited or risky operations</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION E: PRODUCT CAPABILITIES (Premium Feature Cards)       */}
      {/* ------------------------------------------------------------- */}
      <section style={{ padding: 'var(--spacing-96) 24px', background: 'var(--color-void)' }}>
        <div style={{ maxWidth: 'var(--page-max-width)', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 64px auto' }}>
            <span className="tag-chip tag-ember" style={{ marginBottom: '12px' }}>
              Core Capabilities
            </span>
            <h2
              className="font-display"
              style={{
                fontSize: 'clamp(30px, 4vw, 44px)',
                lineHeight: 1.15,
                fontWeight: 700,
                color: '#ffffff',
                marginBottom: '16px',
              }}
            >
              Engineered for production reliability.
            </h2>
            <p style={{ fontFamily: 'var(--font-inter)', fontSize: '16px', color: 'var(--color-ash)', lineHeight: 1.6 }}>
              Everything needed to deploy cost-conscious, auditable, and secure AI agent tool integration.
            </p>
          </div>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
              gap: '24px',
            }}
          >
            {/* Card 1 */}
            <div className="card-charcoal card-glow-iris">
              <div style={featureIconBox}>
                <GitBranch size={22} color="#5683da" />
              </div>
              <h3 style={featureTitle}>Intelligent Action Routing</h3>
              <p style={featureDesc}>
                Uses <code>convaiinnovations/laya</code> ModernBERT decision routing to match natural language queries against registered action schemas with 91.7% strict accuracy.
              </p>
            </div>

            {/* Card 2 */}
            <div className="card-charcoal card-glow-amber">
              <div style={featureIconBox}>
                <Shield size={22} color="#ff8964" />
              </div>
              <h3 style={featureTitle}>Runtime Policy Enforcement</h3>
              <p style={featureDesc}>
                Deterministic boundary checks caller credentials, guarantees read-only isolation, validates mandatory parameter presence, and intercepts administrative exploits.
              </p>
            </div>

            {/* Card 3 */}
            <div className="card-charcoal card-glow-iris">
              <div style={featureIconBox}>
                <Zap size={22} color="#5683da" />
              </div>
              <h3 style={featureTitle}>Direct Tool Execution</h3>
              <p style={featureDesc}>
                Authorized operations bypass generative LLM overhead entirely, executing directly against tools (GitHub REST API, system tools) in single-digit milliseconds.
              </p>
            </div>

            {/* Card 4 */}
            <div className="card-charcoal card-glow-amber">
              <div style={featureIconBox}>
                <Cpu size={22} color="#ff8964" />
              </div>
              <h3 style={featureTitle}>Local Generative Inference</h3>
              <p style={featureDesc}>
                Embedded <code>google/gemma-2-2b-it</code> using native PyTorch <code>bfloat16</code> loads in 6.0s on CPU and delivers 0.4s/token generation exclusively when synthesis is requested.
              </p>
            </div>

            {/* Card 5 */}
            <div className="card-charcoal card-glow-iris">
              <div style={featureIconBox}>
                <Lock size={22} color="#5683da" />
              </div>
              <h3 style={featureTitle}>Human-in-the-Loop Approval</h3>
              <p style={featureDesc}>
                Mutating state changes (merges, deletions, config updates) automatically trigger <code>HUMAN_REVIEW</code> pauses, providing complete governance before live writes.
              </p>
            </div>

            {/* Card 6 */}
            <div className="card-charcoal card-glow-amber">
              <div style={featureIconBox}>
                <BarChart3 size={22} color="#ff8964" />
              </div>
              <h3 style={featureTitle}>Disaggregated Observability</h3>
              <p style={featureDesc}>
                Zero-leak telemetry logs timing metrics separately for decision inference, policy gates, tool calls, and LLM tokens. Machine-readable audit traces for every request.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION F: PROOF OF EFFICIENCY & VERIFIED BENCHMARKS          */}
      {/* ------------------------------------------------------------- */}
      <div id="benchmarks">
        <ProofOfEfficiency />
      </div>

      {/* ------------------------------------------------------------- */}
      {/* SECTION G: SECURITY & POLICY ENGINE                           */}
      {/* ------------------------------------------------------------- */}
      <section id="security" style={{ padding: 'var(--spacing-96) 24px', background: 'var(--color-void)' }}>
        <div style={{ maxWidth: 'var(--page-max-width)', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', maxWidth: '780px', margin: '0 auto 64px auto' }}>
            <span className="tag-chip tag-ember" style={{ marginBottom: '12px' }}>
              Safety & Governance
            </span>
            <h2
              className="font-display"
              style={{
                fontSize: 'clamp(30px, 4vw, 44px)',
                lineHeight: 1.15,
                fontWeight: 700,
                color: '#ffffff',
                marginBottom: '16px',
              }}
            >
              Deterministic policy enforcement. No prompt injections.
            </h2>
            <p style={{ fontFamily: 'var(--font-inter)', fontSize: '16px', color: 'var(--color-ash)', lineHeight: 1.6 }}>
              Prompting an LLM to "be safe" fails under adversarial pressure. SlothSwitch places hard deterministic gates between agent models and tool execution.
            </p>
          </div>

          {/* Interactive Policy Decision Simulator */}
          <div
            className="card-charcoal card-glow-iris"
            style={{
              padding: '36px',
              maxWidth: '960px',
              margin: '0 auto',
            }}
          >
            <div style={{ fontSize: '13px', color: 'var(--color-smoke)', marginBottom: '16px', fontWeight: 500 }}>
              Select a sample query to inspect runtime policy behavior:
            </div>

            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '24px' }}>
              {securityQueries.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => setActiveSecurityQuery(idx)}
                  style={{
                    background: activeSecurityQuery === idx ? 'var(--color-charcoal-card)' : 'transparent',
                    color: activeSecurityQuery === idx ? '#ffffff' : 'var(--color-ash)',
                    border: '1px solid',
                    borderColor: activeSecurityQuery === idx ? 'var(--color-electric-iris)' : 'var(--color-slate-edge)',
                    borderRadius: '9999px',
                    padding: '8px 16px',
                    fontSize: '13px',
                    fontFamily: 'var(--font-inter)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  {item.query}
                </button>
              ))}
            </div>

            {/* Policy Decision Panel */}
            <div
              style={{
                background: '#090a0c',
                border: '1px solid var(--color-slate-edge)',
                borderRadius: '8px',
                padding: '24px',
              }}
            >
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '16px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--color-smoke)', textTransform: 'uppercase' }}>Proposed Action</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '15px', color: '#79a2f2', marginTop: '4px' }}>
                    {securityQueries[activeSecurityQuery].decision}
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', color: 'var(--color-smoke)', textTransform: 'uppercase' }}>Policy Authorization Outcome</div>
                  <div
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '15px',
                      fontWeight: 700,
                      color: securityQueries[activeSecurityQuery].color,
                      marginTop: '4px',
                    }}
                  >
                    {securityQueries[activeSecurityQuery].outcome}
                  </div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '11px', color: 'var(--color-smoke)', textTransform: 'uppercase' }}>Enforcement Rationale</div>
                <div style={{ fontFamily: 'var(--font-inter)', fontSize: '14px', color: '#e2e8f0', marginTop: '6px', lineHeight: 1.5 }}>
                  {securityQueries[activeSecurityQuery].reason}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION H: OPEN SOURCE & COMMUNITY                            */}
      {/* ------------------------------------------------------------- */}
      <section
        style={{
          padding: 'var(--spacing-96) 24px',
          background: 'var(--color-obsidian-canvas)',
          borderTop: '1px solid var(--color-slate-edge)',
        }}
      >
        <div style={{ maxWidth: 'var(--page-max-width)', margin: '0 auto', textAlign: 'center' }}>
          <span className="tag-chip tag-ash" style={{ marginBottom: '12px' }}>
            Open Source Developer Kit
          </span>
          <h2
            className="font-display"
            style={{
              fontSize: 'clamp(30px, 4vw, 44px)',
              lineHeight: 1.15,
              fontWeight: 700,
              color: '#ffffff',
              marginBottom: '16px',
            }}
          >
            Built for developers. Ready for production.
          </h2>
          <p style={{ fontFamily: 'var(--font-inter)', fontSize: '16px', color: 'var(--color-ash)', maxWidth: '640px', margin: '0 auto 36px auto' }}>
            Clone the repository, test routing with your existing models, and integrate into LangChain, AutoGen, or custom agent runtimes in minutes.
          </p>

          {/* Quick Install Command Box */}
          <div
            style={{
              maxWidth: '640px',
              margin: '0 auto 48px auto',
              background: '#090a0c',
              border: '1px solid var(--color-slate-edge)',
              borderRadius: '9999px',
              padding: '10px 16px 10px 24px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              fontFamily: 'var(--font-mono)',
              fontSize: '14px',
              color: '#e2e8f0',
            }}
          >
            <span>git clone https://github.com/dushyantzz/Slothswitch.git</span>
            <button
              onClick={() => copyToClipboard('git clone https://github.com/dushyantzz/Slothswitch.git')}
              className="btn-ghost"
              style={{ padding: '6px 14px', fontSize: '12px', borderRadius: '9999px' }}
            >
              {copiedInstall ? (
                <>
                  <Check size={13} color="#4ade80" /> Copied
                </>
              ) : (
                <>
                  <Copy size={13} /> Copy
                </>
              )}
            </button>
          </div>

          {/* Feature Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
              gap: '20px',
              textAlign: 'left',
              maxWidth: '960px',
              margin: '0 auto',
            }}
          >
            <div style={osCardStyle}>
              <CheckCircle2 size={18} color="#4ade80" style={{ marginBottom: '8px' }} />
              <div style={{ fontWeight: 600, color: '#ffffff', marginBottom: '4px' }}>Zero Telemetry Leaks</div>
              <div style={{ fontSize: '13px', color: 'var(--color-ash)' }}>
                Your private prompts and credentials stay local on your machine.
              </div>
            </div>

            <div style={osCardStyle}>
              <CheckCircle2 size={18} color="#4ade80" style={{ marginBottom: '8px' }} />
              <div style={{ fontWeight: 600, color: '#ffffff', marginBottom: '4px' }}>Extensible Registry</div>
              <div style={{ fontSize: '13px', color: 'var(--color-ash)' }}>
                Define custom schemas, action parameters, and tools in plain Python.
              </div>
            </div>

            <div style={osCardStyle}>
              <CheckCircle2 size={18} color="#4ade80" style={{ marginBottom: '8px' }} />
              <div style={{ fontWeight: 600, color: '#ffffff', marginBottom: '4px' }}>Permissive License</div>
              <div style={{ fontSize: '13px', color: 'var(--color-ash)' }}>
                100% open source under the MIT License. Free for commercial and research use.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------- */}
      {/* SECTION I: FINAL CTA BANNER                                   */}
      {/* ------------------------------------------------------------- */}
      <section
        style={{
          padding: '80px 24px',
          background: 'var(--color-void)',
          position: 'relative',
          overflow: 'hidden',
          textAlign: 'center',
        }}
      >
        <div className="aurora-beam" style={{ height: '360px', top: 'auto', bottom: 0, opacity: 0.6 }} />

        <div style={{ maxWidth: '680px', margin: '0 auto', position: 'relative', zIndex: 1 }}>
          <h2
            className="font-display"
            style={{
              fontSize: 'clamp(28px, 4vw, 40px)',
              fontWeight: 700,
              color: '#ffffff',
              marginBottom: '16px',
            }}
          >
            Experience the SlothSwitch routing pipeline.
          </h2>
          <p style={{ fontFamily: 'var(--font-inter)', fontSize: '16px', color: 'var(--color-ash)', marginBottom: '32px' }}>
            Test live requests against the real decision router, inspect execution traces, and monitor token usage in the developer dashboard.
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <button
              onClick={onOpenDashboard}
              className="btn-primary"
              style={{ padding: '12px 30px', fontSize: '15px' }}
            >
              <Zap size={16} />
              Open Live Dashboard
            </button>
            <a
              href="https://github.com/dushyantzz/Slothswitch"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-ghost"
              style={{ padding: '12px 24px', fontSize: '15px' }}
            >
              Star on GitHub
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}

/* Styles */
const statBoxStyle: React.CSSProperties = {
  background: '#090a0c',
  border: '1px solid var(--color-slate-edge)',
  borderRadius: '8px',
  padding: '12px 14px',
  display: 'flex',
  flexDirection: 'column',
  gap: '4px',
}
const statBoxLabel: React.CSSProperties = {
  fontSize: '11px',
  color: 'var(--color-smoke)',
  textTransform: 'uppercase',
  letterSpacing: '0.04em',
}
const statBoxValue: React.CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontSize: '13px',
  fontWeight: 600,
  color: '#ffffff',
}

const flowStepCardStyle: React.CSSProperties = {
  background: '#090a0c',
  border: '1px solid var(--color-slate-edge)',
  borderRadius: '12px',
  padding: '24px',
  position: 'relative',
}
const flowStepNumber: React.CSSProperties = {
  width: '32px',
  height: '32px',
  borderRadius: '8px',
  background: 'rgba(255, 255, 255, 0.08)',
  color: '#ffffff',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '13px',
  fontWeight: 700,
  fontFamily: 'var(--font-mono)',
  marginBottom: '16px',
}
const flowStepTitle: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '18px',
  fontWeight: 600,
  color: '#ffffff',
  marginBottom: '8px',
}
const flowStepDesc: React.CSSProperties = {
  fontSize: '13px',
  lineHeight: 1.6,
  color: 'var(--color-ash)',
}

const terminalCardStyle: React.CSSProperties = {
  background: '#111111',
  border: '1px solid var(--color-slate-edge)',
  borderRadius: '8px',
  padding: '12px 14px',
}

const featureIconBox: React.CSSProperties = {
  width: '44px',
  height: '44px',
  borderRadius: '10px',
  background: 'rgba(255, 255, 255, 0.05)',
  border: '1px solid var(--color-slate-edge)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  marginBottom: '20px',
}
const featureTitle: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '20px',
  fontWeight: 600,
  color: '#ffffff',
  marginBottom: '10px',
}
const featureDesc: React.CSSProperties = {
  fontSize: '14px',
  lineHeight: 1.6,
  color: 'var(--color-ash)',
}

const osCardStyle: React.CSSProperties = {
  background: '#090a0c',
  border: '1px solid var(--color-slate-edge)',
  borderRadius: '12px',
  padding: '20px',
}
