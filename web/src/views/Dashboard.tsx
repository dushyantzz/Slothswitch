import React, { useState, useEffect } from 'react'
import {
  LayoutDashboard,
  PlayCircle,
  ListFilter,
  Cpu,
  ShieldCheck,
  BarChart3,
  Settings,
  ArrowLeft,
  RefreshCw,
} from 'lucide-react'
import { OverviewView } from './dashboard/OverviewView'
import { PlaygroundView } from './dashboard/PlaygroundView'
import { TracesView } from './dashboard/TracesView'
import { ModelsView } from './dashboard/ModelsView'
import { PoliciesView } from './dashboard/PoliciesView'
import { BenchmarksView } from './dashboard/BenchmarksView'
import { SettingsView } from './dashboard/SettingsView'
import {
  fetchOverview,
  fetchWorkflows,
  fetchBenchmarks,
  fetchModels,
  fetchTraces,
} from '../services/api'
import type {
  BenchmarkData,
  DashboardStats,
  ModelsInfo,
  TraceRecord,
  WorkflowData,
} from '../types'

interface DashboardProps {
  onBackToLanding: () => void
}

type TabType =
  | 'overview'
  | 'playground'
  | 'traces'
  | 'models'
  | 'policies'
  | 'benchmarks'
  | 'settings'

export const Dashboard: React.FC<DashboardProps> = ({ onBackToLanding }) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [stats, setStats] = useState<DashboardStats>({
    total_requests: 5,
    direct_tool_executions: 2,
    generative_calls: 1,
    avoided_generative_calls: 4,
    avoided_generative_pct: 80.0,
    policy_abstentions: 1,
    human_approvals_required: 1,
    clarifications_requested: 0,
  })
  const [traces, setTraces] = useState<TraceRecord[]>([])
  const [workflows, setWorkflows] = useState<WorkflowData[]>([])
  const [benchmarks, setBenchmarks] = useState<BenchmarkData | null>(null)
  const [modelsInfo, setModelsInfo] = useState<ModelsInfo | null>(null)
  const [selectedTrace, setSelectedTrace] = useState<TraceRecord | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isConnected, setIsConnected] = useState(true)

  const loadAllData = async () => {
    setIsLoading(true)
    try {
      const [overviewData, wfData, benchData, modelsData, tracesData] = await Promise.all([
        fetchOverview().catch(() => null),
        fetchWorkflows().catch(() => ({ workflows: [] })),
        fetchBenchmarks().catch(() => null),
        fetchModels().catch(() => null),
        fetchTraces().catch(() => ({ traces: [], total_traces: 0 })),
      ])

      if (overviewData) {
        setStats(overviewData.stats)
        if (overviewData.recent_traces?.length > 0) {
          setTraces(overviewData.recent_traces)
        }
      }
      if (tracesData?.traces?.length > 0) {
        setTraces(tracesData.traces)
      }
      if (wfData?.workflows) {
        setWorkflows(wfData.workflows)
      }
      if (benchData) {
        setBenchmarks(benchData)
      }
      if (modelsData) {
        setModelsInfo(modelsData)
      }
      setIsConnected(true)
    } catch {
      setIsConnected(false)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    loadAllData()
  }, [])

  const handleTraceGenerated = (newTrace: TraceRecord) => {
    setTraces((prev) => [newTrace, ...prev])
    setStats((prev) => {
      const isGen = newTrace.policy_outcome === 'USE_GENERATIVE_MODEL'
      const isTool = newTrace.policy_outcome === 'EXECUTE_TOOL'
      const isAbstain = newTrace.policy_outcome === 'ABSTAIN'
      const isReview = newTrace.policy_outcome === 'HUMAN_REVIEW'
      const newTotal = prev.total_requests + 1
      const newGen = prev.generative_calls + (isGen ? 1 : 0)
      const newAvoided = newTotal - newGen
      return {
        ...prev,
        total_requests: newTotal,
        direct_tool_executions: prev.direct_tool_executions + (isTool ? 1 : 0),
        generative_calls: newGen,
        avoided_generative_calls: newAvoided,
        avoided_generative_pct: roundPct((newAvoided / newTotal) * 100),
        policy_abstentions: prev.policy_abstentions + (isAbstain ? 1 : 0),
        human_approvals_required: prev.human_approvals_required + (isReview ? 1 : 0),
      }
    })
  }

  const roundPct = (num: number) => Math.round(num * 10) / 10

  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'playground', label: 'Request Playground', icon: PlayCircle },
    { id: 'traces', label: 'Execution Traces', icon: ListFilter },
    { id: 'models', label: 'Models & Usage', icon: Cpu },
    { id: 'policies', label: 'Policies', icon: ShieldCheck },
    { id: 'benchmarks', label: 'Benchmarks', icon: BarChart3 },
    { id: 'settings', label: 'Settings', icon: Settings },
  ]

  return (
    <div
      style={{
        display: 'flex',
        minHeight: '100vh',
        background: 'var(--color-void)',
        color: '#ffffff',
        fontFamily: 'var(--font-inter)',
      }}
    >
      {/* ------------------------------------------------------------- */}
      {/* SIDEBAR NAVIGATION                                            */}
      {/* ------------------------------------------------------------- */}
      <aside
        style={{
          width: '240px',
          background: 'var(--color-charcoal-card)',
          borderRight: '1px solid var(--color-slate-edge)',
          display: 'flex',
          flexDirection: 'column',
          position: 'fixed',
          top: 0,
          bottom: 0,
          left: 0,
          zIndex: 50,
        }}
      >
        {/* Brand Header */}
        <div
          style={{
            padding: '20px',
            borderBottom: '1px solid var(--color-slate-edge)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
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
            <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: '16px' }}>
              SlothSwitch
            </span>
          </div>
          <span className="tag-chip tag-iris" style={{ fontSize: '9px', padding: '2px 6px' }}>
            v0.1
          </span>
        </div>

        {/* Navigation Items */}
        <nav style={{ padding: '16px 12px', flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = activeTab === item.id

            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id as TabType)
                  setSelectedTrace(null)
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  width: '100%',
                  padding: '9px 12px',
                  borderRadius: 'var(--radius-buttons)',
                  background: isActive ? 'var(--color-electric-iris)' : 'transparent',
                  color: isActive ? '#ffffff' : 'var(--color-ash)',
                  border: 'none',
                  fontFamily: 'var(--font-inter)',
                  fontSize: '13px',
                  fontWeight: isActive ? 600 : 400,
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.15s ease',
                }}
              >
                <Icon size={16} color={isActive ? '#ffffff' : 'var(--color-smoke)'} />
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>

        {/* Bottom Back Button */}
        <div style={{ padding: '16px 14px', borderTop: '1px solid var(--color-slate-edge)' }}>
          <button
            onClick={onBackToLanding}
            className="btn-ghost"
            style={{ width: '100%', padding: '8px 12px', fontSize: '12px', justifyContent: 'center' }}
          >
            <ArrowLeft size={13} />
            Back to Website
          </button>
        </div>
      </aside>

      {/* ------------------------------------------------------------- */}
      {/* MAIN CONTENT WORKSPACE                                        */}
      {/* ------------------------------------------------------------- */}
      <main
        style={{
          marginLeft: '240px',
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
        }}
      >
        {/* Top Header Bar */}
        <header
          style={{
            height: '60px',
            borderBottom: '1px solid var(--color-slate-edge)',
            background: 'rgba(17, 17, 17, 0.75)',
            backdropFilter: 'blur(12px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '0 28px',
            position: 'sticky',
            top: 0,
            zIndex: 40,
          }}
        >
          {/* Active Status Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <div
                style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: isConnected ? '#4ade80' : '#f59e0b',
                  boxShadow: isConnected ? '0 0 8px #4ade80' : 'none',
                }}
              />
              <span style={{ fontSize: '12px', color: '#ffffff', fontWeight: 500 }}>
                {isConnected ? 'SlothSwitch Engine Online' : 'Connecting to Local Server'}
              </span>
            </div>
            <span style={{ color: 'var(--color-slate-edge)' }}>|</span>
            <span style={{ fontSize: '12px', color: 'var(--color-ash)', fontFamily: 'var(--font-mono)' }}>
              Port 8080
            </span>
          </div>

          {/* Right Refresh */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={loadAllData}
              disabled={isLoading}
              className="btn-ghost"
              style={{ padding: '6px 12px', fontSize: '12px' }}
              title="Refresh telemetry"
            >
              <RefreshCw size={12} className={isLoading ? 'spin-animate' : ''} />
              <span>Refresh</span>
            </button>
          </div>
        </header>

        {/* Tab View Body */}
        <div style={{ padding: '28px', flex: 1, maxWidth: '1200px', width: '100%' }}>
          {activeTab === 'overview' && (
            <OverviewView
              stats={stats}
              recentTraces={traces}
              onSelectTrace={(t) => {
                setSelectedTrace(t)
                setActiveTab('traces')
              }}
              onNavigateToPlayground={() => setActiveTab('playground')}
            />
          )}

          {activeTab === 'playground' && (
            <PlaygroundView onTraceGenerated={handleTraceGenerated} />
          )}

          {activeTab === 'traces' && (
            <TracesView
              traces={traces}
              selectedTrace={selectedTrace}
              onSelectTrace={setSelectedTrace}
            />
          )}

          {activeTab === 'models' && <ModelsView modelsInfo={modelsInfo} />}

          {activeTab === 'policies' && <PoliciesView workflows={workflows} />}

          {activeTab === 'benchmarks' && <BenchmarksView benchmarkData={benchmarks} />}

          {activeTab === 'settings' && <SettingsView />}
        </div>
      </main>
    </div>
  )
}
