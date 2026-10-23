import React from 'react'
import { ArrowUpRight } from 'lucide-react'

export const Footer: React.FC<{ onOpenDashboard: () => void }> = ({ onOpenDashboard }) => {
  return (
    <footer
      style={{
        background: 'var(--color-void)',
        borderTop: '1px solid var(--color-slate-edge)',
        position: 'relative',
        overflow: 'hidden',
        paddingTop: '64px',
        paddingBottom: '48px',
      }}
    >
      {/* Restrained Aurora Accent at the bottom */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: '50%',
          transform: 'translateX(-50%)',
          width: '500px',
          height: '160px',
          background: 'radial-gradient(ellipse at bottom, rgba(86, 131, 218, 0.2) 0%, rgba(255, 137, 100, 0.1) 40%, transparent 70%)',
          filter: 'blur(40px)',
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          maxWidth: 'var(--page-max-width)',
          margin: '0 auto',
          padding: '0 24px',
          position: 'relative',
          zIndex: 1,
        }}
      >
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '40px',
            marginBottom: '48px',
          }}
        >
          {/* Brand Info */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '16px' }}>
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '6px',
                  background: '#090a0c',
                  border: '1px solid #4a4b50',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                <svg width="18" height="18" viewBox="0 0 32 32" fill="none">
                  <path d="M7 16C7 11.0294 11.0294 7 16 7H18C21.3137 7 24 9.68629 24 13C24 16.3137 21.3137 19 18 19H12" stroke="#5683da" strokeWidth="2.8" strokeLinecap="round" />
                  <path d="M25 16C25 20.9706 20.9706 25 16 25H14C10.6863 25 8 22.3137 8 19C8 15.6863 10.6863 13 14 13H20" stroke="#ff8964" strokeWidth="2.8" strokeLinecap="round" />
                  <circle cx="12" cy="19" r="2.2" fill="#5683da" />
                  <circle cx="20" cy="13" r="2.2" fill="#ff8964" />
                </svg>
              </div>
              <span
                style={{
                  fontFamily: 'var(--font-display)',
                  fontWeight: 700,
                  fontSize: '18px',
                  color: '#ffffff',
                }}
              >
                SlothSwitch
              </span>
            </div>
            <p
              style={{
                fontFamily: 'var(--font-inter)',
                fontSize: '13px',
                color: 'var(--color-ash)',
                lineHeight: 1.6,
                maxWidth: '280px',
              }}
            >
              Open-source decision and execution layer for AI agent workflows. Avoid unnecessary generative model calls and keep tool execution under deterministic control.
            </p>
          </div>

          {/* Product links */}
          <div>
            <h4 style={footerHeadingStyle}>Product</h4>
            <ul style={footerListStyle}>
              <li>
                <button onClick={onOpenDashboard} style={footerLinkBtnStyle}>
                  Live Dashboard
                </button>
              </li>
              <li>
                <a href="#how-it-works" style={footerLinkStyle}>
                  Architecture & Routing
                </a>
              </li>
              <li>
                <a href="#benchmarks" style={footerLinkStyle}>
                  Verified Benchmarks
                </a>
              </li>
              <li>
                <a href="#security" style={footerLinkStyle}>
                  Security & Policy Engine
                </a>
              </li>
            </ul>
          </div>

          {/* Developers */}
          <div>
            <h4 style={footerHeadingStyle}>Developers</h4>
            <ul style={footerListStyle}>
              <li>
                <a
                  href="https://github.com/dushyantzz/Slothswitch"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={footerLinkStyle}
                >
                  GitHub Repository <ArrowUpRight size={13} />
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/dushyantzz/Slothswitch#quickstart"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={footerLinkStyle}
                >
                  CLI Quickstart <ArrowUpRight size={13} />
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/dushyantzz/Slothswitch/blob/main/decision.md"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={footerLinkStyle}
                >
                  Benchmark Audit Report <ArrowUpRight size={13} />
                </a>
              </li>
            </ul>
          </div>

          {/* Open Source / License */}
          <div>
            <h4 style={footerHeadingStyle}>Community & License</h4>
            <p
              style={{
                fontFamily: 'var(--font-inter)',
                fontSize: '13px',
                color: 'var(--color-ash)',
                lineHeight: 1.6,
                marginBottom: '12px',
              }}
            >
              Released under the permissive MIT Open Source License. Built with Laya ModernBERT & Google Gemma 2 2B.
            </p>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
              <span className="tag-chip tag-ash">MIT License</span>
              <span className="tag-chip tag-iris">Python 3.10+</span>
              <span className="tag-chip tag-ember">Zero Telemetry Leaks</span>
            </div>
          </div>
        </div>

        {/* Bottom copyright */}
        <div
          style={{
            borderTop: '1px solid var(--color-slate-edge)',
            paddingTop: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '12px',
            fontFamily: 'var(--font-inter)',
            fontSize: '12px',
            color: 'var(--color-iron-veil)',
          }}
        >
          <span>© 2024 SlothSwitch Contributors. Open source software.</span>
          <span>Designed with high-density aurora tokens. No artificial metrics or synthetic claims.</span>
        </div>
      </div>
    </footer>
  )
}

const footerHeadingStyle: React.CSSProperties = {
  fontFamily: 'var(--font-display)',
  fontSize: '14px',
  fontWeight: 600,
  color: '#ffffff',
  marginBottom: '16px',
}

const footerListStyle: React.CSSProperties = {
  listStyle: 'none',
  display: 'flex',
  flexDirection: 'column',
  gap: '10px',
}

const footerLinkStyle: React.CSSProperties = {
  fontFamily: 'var(--font-inter)',
  fontSize: '13px',
  color: 'var(--color-ash)',
  textDecoration: 'none',
  display: 'inline-flex',
  alignItems: 'center',
  gap: '4px',
  transition: 'color 0.15s ease',
}

const footerLinkBtnStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  padding: 0,
  fontFamily: 'var(--font-inter)',
  fontSize: '13px',
  color: 'var(--color-ash)',
  cursor: 'pointer',
  textAlign: 'left',
}
