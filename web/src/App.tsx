import { useState, useEffect } from 'react'
import { Navbar } from './components/Navbar'
import { LandingPage } from './views/LandingPage'
import { Dashboard } from './views/Dashboard'
import { Footer } from './components/Footer'

export function App() {
  const [view, setView] = useState<'landing' | 'dashboard'>('landing')

  useEffect(() => {
    // Check initial hash route
    if (window.location.hash === '#dashboard') {
      setView('dashboard')
    }

    const handleHashChange = () => {
      if (window.location.hash === '#dashboard') {
        setView('dashboard')
      } else {
        setView('landing')
      }
    }

    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  const handleNavigate = (newView: 'landing' | 'dashboard', sectionId?: string) => {
    setView(newView)
    if (newView === 'dashboard') {
      window.location.hash = '#dashboard'
      window.scrollTo({ top: 0, behavior: 'smooth' })
    } else {
      window.location.hash = sectionId ? `#${sectionId}` : ''
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {view === 'landing' ? (
        <>
          <Navbar
            currentView="landing"
            onNavigate={(v, s) => handleNavigate(v, s)}
          />
          <main style={{ flex: 1 }}>
            <LandingPage onOpenDashboard={() => handleNavigate('dashboard')} />
          </main>
          <Footer onOpenDashboard={() => handleNavigate('dashboard')} />
        </>
      ) : (
        <Dashboard onBackToLanding={() => handleNavigate('landing')} />
      )}
    </div>
  )
}

export default App
