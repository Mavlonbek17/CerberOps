import { useState, useEffect, useCallback } from 'react';
import {
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  RotateCw,
  ArrowRight,
  Activity,
} from 'lucide-react';
import Header from './components/Header';
import StatusCards from './components/StatusCards';
import ScanForm from './components/ScanForm';
import ScanList from './components/ScanList';
import LiveResults from './components/LiveResults';
import ReportView from './components/ReportView';
import SideNav, { type NavView } from './components/SideNav';
import RightRail from './components/RightRail';
import NetworkMap from './components/NetworkMap';
import SettingsView from './components/SettingsView';
import ScanHistoryView from './components/ScanHistoryView';
import LogsView from './components/LogsView';
import SupportView from './components/SupportView';
import ChatPanel from './components/ChatPanel';
import SchedulerView from './components/SchedulerView';
import type { ScanStatus } from './types';
import {
  healthCheck,
  startScan,
  listScans,
  getScan,
  getReport,
  deleteScan,
} from './api/client';
import type { HealthCheck, ScanSummary, ScanDetail, Report } from './types';

export default function App() {
  const [currentView, setCurrentView] = useState<NavView>('dashboard');
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [selectedScan, setSelectedScan] = useState<ScanDetail | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [showReport, setShowReport] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    return (localStorage.getItem('cerberops_theme') as 'dark' | 'light') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('cerberops_theme', theme);
  }, [theme]);

  const refresh = useCallback(async () => {
    try {
      const [h, s] = await Promise.all([healthCheck(), listScans()]);
      setHealth(h);
      setScans(s);
    } catch {
      // API might not be running yet
    }
  }, []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 10000);
    return () => clearInterval(id);
  }, [refresh]);

  // Poll active scan
  useEffect(() => {
    if (!selectedScan) return;
    const active = ['queued', 'running', 'parsing', 'analyzing'].includes(selectedScan.status);
    if (!active) return;
    const id = setInterval(async () => {
      try {
        const updated = await getScan(selectedScan.id);
        setSelectedScan(updated);
        if (['completed', 'failed', 'cancelled'].includes(updated.status)) refresh();
      } catch { /* ignore */ }
    }, 3000);
    return () => clearInterval(id);
  }, [selectedScan, refresh]);

  const handleStartScan = async (
    target: string,
    scanners: string[],
    allowInternal: boolean,
    smartRecon: boolean,
    tags: string[]
  ) => {
    setLoading(true);
    setError(null);
    try {
      const result = await startScan(target, scanners, allowInternal, smartRecon, tags);
      const detail = await getScan(result.job_id);
      setSelectedScan(detail);
      setShowReport(false);
      setReport(null);
      setCurrentView('dashboard');
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start scan');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectScan = async (id: string) => {
    try {
      const detail = await getScan(id);
      setSelectedScan(detail);
      setShowReport(false);
      setReport(null);
    } catch {
      setError('Failed to load scan details');
    }
  };

  const handleCancelScan = async (id: string) => {
    try {
      await deleteScan(id);
      await refresh();
      if (selectedScan?.id === id) {
        const updated = await getScan(id);
        setSelectedScan(updated);
      }
    } catch {
      setError('Failed to cancel scan');
    }
  };

  const handleViewReport = async (jobId: string) => {
    try {
      const r = await getReport(jobId);
      setReport(r);
      setShowReport(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Report not available yet');
    }
  };

  const handleNewScanClick = useCallback(() => {
    setCurrentView('dashboard');
    setTimeout(() => {
      const form = document.getElementById('new-scan-form');
      form?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const input = form?.querySelector('input[type="text"]') as HTMLInputElement | null;
      input?.focus();
    }, 50);
  }, []);

  const totalFindings = scans.reduce((sum, s) => sum + s.findings_count, 0);

  return (
    <div className="h-screen w-screen flex flex-col bg-background text-on-background overflow-hidden">
      <Header
        health={health}
        onViewChange={setCurrentView}
        theme={theme}
        onToggleTheme={() => setTheme(t => t === 'dark' ? 'light' : 'dark')}
      />

      {/* ── Below header: sidebar + main ── */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        <SideNav currentView={currentView} onViewChange={setCurrentView} onNewScan={handleNewScanClick} />

        {/* ── Main scroll area ── */}
        <main className="flex-1 min-w-0 h-full overflow-y-auto">

          {/* Error banner — sits above page content, full width */}
          {error && (
            <div className="mx-8 mt-6 bg-error-container border border-error/40 text-on-error-container rounded-xl px-5 py-3 text-sm font-label flex justify-between items-center">
              <span>{error}</span>
              <button onClick={() => setError(null)} className="hover:opacity-70 cursor-pointer font-bold ml-4">dismiss</button>
            </div>
          )}

          {/* ── DASHBOARD ── */}
          {currentView === 'dashboard' && (() => {
            const STATUS_MAP: Record<ScanStatus, { icon: typeof Clock; color: string; label: string }> = {
              queued:    { icon: Clock,        color: 'text-tertiary',          label: 'Queued' },
              running:   { icon: RotateCw,     color: 'text-primary',           label: 'Running' },
              parsing:   { icon: Loader2,      color: 'text-primary',           label: 'Parsing' },
              analyzing: { icon: Loader2,      color: 'text-primary',           label: 'Analyzing' },
              completed: { icon: CheckCircle2, color: 'text-secondary',         label: 'Done' },
              failed:    { icon: XCircle,      color: 'text-error',             label: 'Failed' },
              cancelled: { icon: XCircle,      color: 'text-on-surface-variant', label: 'Cancelled' },
            };

            const recentScans = scans.slice(0, 6);
            const recentActivity = scans.slice(0, 8);
            const relTime = (iso: string) => {
              const d = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
              if (d < 60) return 'just now';
              const m = Math.floor(d / 60);
              if (m < 60) return `${m}m ago`;
              const h = Math.floor(m / 60);
              if (h < 24) return `${h}h ago`;
              return `${Math.floor(h / 24)}d ago`;
            };

            return (
              <div className="px-8 py-8 flex flex-col gap-6">

                {/* Status cards */}
                <StatusCards health={health} totalScans={scans.length} totalFindings={totalFindings} />

                {/* New scan form */}
                <ScanForm onSubmit={handleStartScan} loading={loading} />

                {/* Two-column: Recent Scans + Activity */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">

                  {/* Recent Scans */}
                  <div className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
                    <div className="flex items-center justify-between px-5 py-3.5 border-b border-outline-variant">
                      <h3 className="text-[14px] font-semibold text-on-background">Recent Scans</h3>
                      <button
                        onClick={() => setCurrentView('scan_history')}
                        className="flex items-center gap-1 text-[12px] font-medium text-primary hover:underline cursor-pointer"
                      >
                        View all <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>

                    {recentScans.length === 0 ? (
                      <div className="px-5 py-10 text-center text-[13px] text-on-surface-variant">
                        No scans yet. Launch one above.
                      </div>
                    ) : (
                      <div className="divide-y divide-outline-variant/60">
                        {recentScans.map((s) => {
                          const st = STATUS_MAP[s.status];
                          const StIcon = st.icon;
                          const spinning = ['running','parsing','analyzing'].includes(s.status);
                          return (
                            <div
                              key={s.id}
                              onClick={() => { handleSelectScan(s.id); setCurrentView('live_scans'); }}
                              className="flex items-center gap-3 px-5 py-3 hover:bg-surface-container-high/60 transition-colors cursor-pointer"
                            >
                              <StIcon className={`w-4 h-4 shrink-0 ${st.color} ${spinning ? 'animate-spin' : ''}`} />
                              <span className="text-[13px] font-medium text-on-background truncate flex-1 min-w-0">
                                {s.target.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                              </span>
                              <span className="text-[12px] text-on-surface-variant shrink-0">
                                {s.scanners.map(sc => sc.toUpperCase()).join(' · ')}
                              </span>
                              <span className={`text-[12px] font-semibold shrink-0 ${s.findings_count > 0 ? 'text-tertiary' : 'text-on-surface-variant'}`}>
                                {s.findings_count > 0 ? `${s.findings_count} vulns` : '—'}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Activity Feed */}
                  <div className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
                    <div className="flex items-center justify-between px-5 py-3.5 border-b border-outline-variant">
                      <h3 className="text-[14px] font-semibold text-on-background">Activity</h3>
                      <button
                        onClick={() => setCurrentView('logs')}
                        className="flex items-center gap-1 text-[12px] font-medium text-primary hover:underline cursor-pointer"
                      >
                        All logs <ArrowRight className="w-3 h-3" />
                      </button>
                    </div>

                    {recentActivity.length === 0 ? (
                      <div className="px-5 py-10 text-center text-[13px] text-on-surface-variant">
                        No activity yet.
                      </div>
                    ) : (
                      <div className="divide-y divide-outline-variant/60">
                        {recentActivity.map((s) => (
                          <div key={s.id} className="flex items-center gap-3 px-5 py-3">
                            <Activity className="w-3.5 h-3.5 text-on-surface-variant shrink-0" />
                            <span className="text-[13px] font-medium text-on-background truncate flex-1 min-w-0">
                              {s.target.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                            </span>
                            <span className={`text-[12px] font-medium capitalize shrink-0 ${
                              s.status === 'completed' ? 'text-secondary' :
                              s.status === 'failed' ? 'text-error' :
                              'text-on-surface-variant'
                            }`}>
                              {s.status}
                            </span>
                            <span className="text-[12px] text-on-surface-variant shrink-0">
                              {relTime(s.created_at)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })()}

          {/* ── LIVE SCANS ── */}
          {currentView === 'live_scans' && (
            <div className="px-6 py-6 flex flex-col" style={{ height: 'calc(100vh - 64px)' }}>
              <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-5 min-h-0">
                <div className="lg:col-span-3 min-h-0 overflow-y-auto">
                  <ScanList
                    scans={scans}
                    onSelect={handleSelectScan}
                    onCancel={handleCancelScan}
                    selectedId={selectedScan?.id ?? null}
                  />
                </div>
                <div className="lg:col-span-6 min-h-0 overflow-hidden flex flex-col">
                  {showReport && report ? (
                    <ReportView report={report} onBack={() => setShowReport(false)} />
                  ) : (
                    <LiveResults
                      scan={selectedScan}
                      health={health}
                      scans={scans}
                      onViewReport={handleViewReport}
                      onNavigateToChat={() => setCurrentView('ai_chat')}
                    />
                  )}
                </div>
                <div className="lg:col-span-3 min-h-0 overflow-y-auto">
                  <RightRail scan={selectedScan} scans={scans} />
                </div>
              </div>
            </div>
          )}

          {/* ── AI CHAT ── */}
          {currentView === 'ai_chat' && (
            <div className="px-6 py-6" style={{ height: 'calc(100vh - 64px)' }}>
              <ChatPanel scans={scans} />
            </div>
          )}

          {/* ── SCAN HISTORY ── */}
          {currentView === 'scan_history' && (
            <div className="px-6 py-6">
              <ScanHistoryView
                scans={scans}
                onSelectScan={(id) => {
                  handleSelectScan(id);
                  setCurrentView('live_scans');
                }}
                onCancelScan={handleCancelScan}
              />
            </div>
          )}

          {/* ── NETWORK MAP ── */}
          {currentView === 'network_map' && (
            <div className="px-6 py-6">
              <NetworkMap
                scans={scans}
                selectedScan={selectedScan}
                onSelectScan={handleSelectScan}
              />
            </div>
          )}

          {/* ── SCHEDULER ── */}
          {currentView === 'scheduler' && (
            <div className="px-6 py-6">
              <SchedulerView />
            </div>
          )}

          {/* ── SETTINGS ── */}
          {currentView === 'settings' && (
            <div className="px-6 py-6">
              <SettingsView health={health} />
            </div>
          )}

          {/* ── LOGS ── */}
          {currentView === 'logs' && (
            <div className="px-6 py-6">
              <LogsView />
            </div>
          )}

          {/* ── SUPPORT ── */}
          {currentView === 'support' && (
            <div className="px-6 py-6">
              <SupportView health={health} />
            </div>
          )}

        </main>
      </div>
    </div>
  );
}
