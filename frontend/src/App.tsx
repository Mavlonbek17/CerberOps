import { useState, useEffect, useCallback } from 'react';
import Header from './components/Header';
import ScanForm from './components/ScanForm';
import ScanList from './components/ScanList';
import ScanDetailView from './components/ScanDetail';
import ReportView from './components/ReportView';
import StatusCards from './components/StatusCards';
import { healthCheck, startScan, listScans, getScan, getReport } from './api/client';
import type { HealthCheck, ScanSummary, ScanDetail, Report } from './types';

type View = 'dashboard' | 'report';

export default function App() {
  const [health, setHealth] = useState<HealthCheck | null>(null);
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [selectedScan, setSelectedScan] = useState<ScanDetail | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [view, setView] = useState<View>('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch health + scan list on mount
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
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, [refresh]);

  // Poll selected scan if it's in progress
  useEffect(() => {
    if (!selectedScan) return;
    const inProgress = ['queued', 'running', 'parsing', 'analyzing'].includes(selectedScan.status);
    if (!inProgress) return;

    const interval = setInterval(async () => {
      try {
        const updated = await getScan(selectedScan.id);
        setSelectedScan(updated);
        if (['completed', 'failed', 'cancelled'].includes(updated.status)) {
          refresh();
        }
      } catch { /* ignore */ }
    }, 3000);

    return () => clearInterval(interval);
  }, [selectedScan, refresh]);

  const handleStartScan = async (target: string, scanners: string[], allowInternal: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const result = await startScan(target, scanners, allowInternal);
      const detail = await getScan(result.job_id);
      setSelectedScan(detail);
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
      setView('dashboard');
      setReport(null);
    } catch {
      setError('Failed to load scan details');
    }
  };

  const handleViewReport = async (jobId: string) => {
    try {
      const r = await getReport(jobId);
      setReport(r);
      setView('report');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load report');
    }
  };

  const totalFindings = scans.reduce((sum, s) => sum + s.findings_count, 0);

  return (
    <div className="min-h-screen">
      <Header health={health} />

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Error banner */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 rounded-lg px-4 py-3 text-sm flex justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="hover:text-red-300">Dismiss</button>
          </div>
        )}

        {/* Status cards */}
        <StatusCards health={health} totalScans={scans.length} totalFindings={totalFindings} />

        {/* Scan form */}
        <ScanForm onSubmit={handleStartScan} loading={loading} />

        {/* Main content */}
        <div className="grid grid-cols-5 gap-6">
          {/* Left: Scan list */}
          <div className="col-span-2">
            <ScanList scans={scans} onSelect={handleSelectScan} selectedId={selectedScan?.id ?? null} />
          </div>

          {/* Right: Detail / Report */}
          <div className="col-span-3">
            {view === 'report' && report ? (
              <ReportView report={report} onBack={() => setView('dashboard')} />
            ) : selectedScan ? (
              <ScanDetailView scan={selectedScan} onViewReport={handleViewReport} />
            ) : (
              <div className="bg-[var(--bg-card)] rounded-lg border border-[var(--border)] p-12 text-center">
                <p className="text-[var(--text-secondary)]">
                  Select a scan from the list or start a new one.
                </p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
