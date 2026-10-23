import React, { useState, useEffect } from 'react'
import {
  Menu,
  X,
  ExternalLink,
  Zap,
} from 'lucide-react'

interface NavbarProps {
  currentView: 'landing' | 'dashboard'
  onNavigate: (view: 'landing' | 'dashboard', sectionId?: string) => void
  backendConnected?: boolean
}

export const Navbar: React.FC<NavbarProps> = ({
  currentView,
  onNavigate,
}) => {
  const [isScrolled, setIsScrolled] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const handleNavClick = (sectionId?: string) => {
    setMobileMenuOpen(false)
    if (sectionId) {
      if (currentView !== 'landing') {
        onNavigate('landing')
        setTimeout(() => {
          const el = document.getElementById(sectionId)
          if (el) el.scrollIntoView({ behavior: 'smooth' })
        }, 100)
      } else {
        const el = document.getElementById(sectionId)
        if (el) el.scrollIntoView({ behavior: 'smooth' })
      }
    } else {
      onNavigate('landing')
    }
  }

  return (
    <nav
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 100,
        transition: 'all 0.25s ease',
        background: isScrolled
          ? 'rgba(9, 10, 12, 0.85)'
          : 'rgba(9, 10, 12, 0.4)',
        backdropFilter: 'blur(16px)',
        borderBottom: isScrolled
          ? '1px solid rgba(74, 75, 80, 0.6)'
          : '1px solid transparent',
      }}
    >
      <div
        style={{
          maxWidth: 'var(--page-max-width)',
          margin: '0 auto',
          padding: '14px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {/* Brand Logo & Name */}
        <div
          onClick={() => handleNavClick()}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            cursor: 'pointer',
          }}
        >
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: '#090a0c',
              border: '1px solid #4a4b50',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              position: 'relative',
              boxShadow: '0 0 12px rgba(86, 131, 218, 0.25)',
            }}
          >
            <svg width="22" height="22" viewBox="0 0 32 32" fill="none">
              <path
                d="M7 16C7 11.0294 11.0294 7 16 7H18C21.3137 7 24 9.68629 24 13C24 16.3137 21.3137 19 18 19H12"
                stroke="#5683da"
                strokeWidth="2.8"
                strokeLinecap="round"
              />
              <path
                d="M25 16C25 20.9706 20.9706 25 16 25H14C10.6863 25 8 22.3137 8 19C8 15.6863 10.6863 13 14 13H20"
                stroke="#ff8964"
                strokeWidth="2.8"
                strokeLinecap="round"
              />
              <circle cx="12" cy="19" r="2.2" fill="#5683da" />
              <circle cx="20" cy="13" r="2.2" fill="#ff8964" />
            </svg>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontFamily: 'var(--font-display)',
                fontWeight: 700,
                fontSize: '18px',
                letterSpacing: '-0.03em',
                color: '#ffffff',
              }}
            >
              SlothSwitch
            </span>
            <span
              className="tag-chip tag-iris"
              style={{ fontSize: '10px', padding: '2px 8px' }}
            >
              v0.1
            </span>
          </div>
        </div>

        {/* Center Desktop Navigation */}
        <div
          className="desktop-nav"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '28px',
          }}
        >
          <button
            onClick={() => handleNavClick('product')}
            style={navItemStyle}
          >
            Product
          </button>
          <button
            onClick={() => handleNavClick('how-it-works')}
            style={navItemStyle}
          >
            How It Works
          </button>
          <button
            onClick={() => handleNavClick('benchmarks')}
            style={navItemStyle}
          >
            Benchmarks
          </button>
          <button
            onClick={() => handleNavClick('security')}
            style={navItemStyle}
          >
            Security
          </button>
          <a
            href="https://github.com/dushyantzz/Slothswitch#readme"
            target="_blank"
            rel="noopener noreferrer"
            style={{ ...navItemStyle, display: 'inline-flex', alignItems: 'center', gap: '4px' }}
          >
            Docs <ExternalLink size={12} color="#a9a9aa" />
          </a>
        </div>

        {/* Right CTA Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <a
            href="https://github.com/dushyantzz/Slothswitch"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-ghost"
            style={{ padding: '8px 16px', fontSize: '13px' }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
            </svg>
            <span className="hide-on-mobile">GitHub</span>
          </a>

          {currentView === 'landing' ? (
            <button
              onClick={() => onNavigate('dashboard')}
              className="btn-primary"
              style={{ padding: '8px 20px', fontSize: '13px' }}
            >
              <Zap size={14} />
              Open Dashboard
            </button>
          ) : (
            <button
              onClick={() => onNavigate('landing')}
              className="btn-ghost"
              style={{ padding: '8px 18px', fontSize: '13px' }}
            >
              Back to Website
            </button>
          )}

          {/* Mobile hamburger button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="mobile-toggle"
            aria-label="Toggle navigation menu"
            style={{
              background: 'none',
              border: 'none',
              color: '#ffffff',
              cursor: 'pointer',
              display: 'none',
              padding: '6px',
            }}
          >
            {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div
          style={{
            background: 'var(--color-charcoal-card)',
            borderBottom: '1px solid var(--color-slate-edge)',
            padding: '20px 24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <button
            onClick={() => handleNavClick('product')}
            style={{ ...navItemStyle, textAlign: 'left', fontSize: '16px' }}
          >
            Product
          </button>
          <button
            onClick={() => handleNavClick('how-it-works')}
            style={{ ...navItemStyle, textAlign: 'left', fontSize: '16px' }}
          >
            How It Works
          </button>
          <button
            onClick={() => handleNavClick('benchmarks')}
            style={{ ...navItemStyle, textAlign: 'left', fontSize: '16px' }}
          >
            Benchmarks
          </button>
          <button
            onClick={() => handleNavClick('security')}
            style={{ ...navItemStyle, textAlign: 'left', fontSize: '16px' }}
          >
            Security
          </button>
          <button
            onClick={() => {
              setMobileMenuOpen(false)
              onNavigate('dashboard')
            }}
            className="btn-primary"
            style={{ width: '100%', marginTop: '8px' }}
          >
            Open Dashboard
          </button>
        </div>
      )}

      <style>{`
        @media (max-width: 768px) {
          .desktop-nav { display: none !important; }
          .mobile-toggle { display: block !important; }
          .hide-on-mobile { display: none; }
        }
      `}</style>
    </nav>
  )
}

const navItemStyle: React.CSSProperties = {
  background: 'none',
  border: 'none',
  color: '#a9a9aa',
  fontFamily: 'var(--font-inter)',
  fontSize: '14px',
  fontWeight: 400,
  letterSpacing: '-0.01em',
  cursor: 'pointer',
  textDecoration: 'none',
  transition: 'color 0.15s ease',
}
