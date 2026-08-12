import { useMemo, useState } from 'react';
import {
  BarChart3,
  Calendar,
  CheckCircle2,
  Download,
  ExternalLink,
  Eye,
  EyeOff,
  FileDown,
  FileText,
  Loader2,
  MessageSquare,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import type { Finding, HealthCheck, ScanDetail, ScanSummary, Severity } from '../types';
import { getExportUrl } from '../api/client';
import ChatPanel from './ChatPanel';
import PocViewer from './PocViewer';

interface Props {
  scan: ScanDetail | null;
  health: HealthCheck | null;
  scans: ScanSummary[];
  onViewReport: (jobId: string) => void;
  onNavigateToChat?: () => void;
}

type Tab = 'overview' | 'findings' | 'chat' | 'scheduler';

const SEV_ORDER: Severity[] = ['critical', 'high', 'medium', 'low', 'info'];

const SEV: Record<Severity, { label: string; color: string; dot: string; badge: string }> = {
  critical: { label: 'Critical', color: 'text-error',            dot: 'bg-error',    badge: 'bg-error/12 border-error/30 text-error' },
  high:     { label: 'High',     color: 'text-orange',           dot: 'bg-orange',   badge: 'bg-orange/12 border-orange/30 text-orange' },
  medium:   { label: 'Medium',   color: 'text-tertiary',         dot: 'bg-tertiary', badge: 'bg-tertiary/12 border-tertiary/30 text-tertiary' },
  low:      { label: 'Low',      color: 'text-secondary',        dot: 'bg-secondary', badge: 'bg-secondary/12 border-secondary/30 text-secondary' },
  info:     { label: 'Info',     color: 'text-on-surface-variant', dot: 'bg-outline',   badge: 'bg-surface-container-highest border-outline-variant text-on-surface-variant' },
};

function AiVerdictBadge({ finding }: { finding: Finding }) {
  if (finding.ai_verdict === 'likely_false_positive') {
    return (
      <span title={finding.ai_triage_notes || ''} className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded bg-surface-container-highest border border-outline-variant text-on-surface-variant">
        <EyeOff className="w-3 h-3" /> Filtered
      </span>
    );
  }
  if (finding.ai_verdict === 'confirmed') {
    return (
      <span title={finding.ai_triage_notes || ''} className="inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded bg-secondary/10 border border-secondary/30 text-secondary">
        <CheckCircle2 className="w-3 h-3" /> Confirmed
      </span>
    );
  }
  return null;
}

function SmartReconBanner({ scan }: { scan: ScanDetail }) {
  if (!scan.smart_recon || !scan.recon_summary) return null;
  return (
    <div className="flex gap-3 px-4 py-3 rounded-lg border border-secondary/25 bg-secondary/6 text-[13px] text-on-surface-variant">
      <Sparkles className="w-4 h-4 text-secondary shrink-0 mt-0.5" />
      <span><span className="font-semibold text-secondary">Smart Recon:</span> {scan.recon_summary}{scan.ai_scan_plan ? ` ${scan.ai_scan_plan}` : ''}</span>
    </div>
  );
}

export default function LiveResults({ scan, health, scans, onViewReport, onNavigateToChat }: Props) {
  const [tab, setTab] = useState<Tab>('overview');
  const [showFiltered, setShowFiltered] = useState(false);

  const scannerCount = health ? Object.values(health.scanners).filter(Boolean).length : 0;
  const isRunning = scan && ['queued', 'running', 'parsing', 'analyzing'].includes(scan.status);

  const orderedFindings = useMemo(
    () => (scan ? [...scan.findings].sort((a, b) => SEV_ORDER.indexOf(a.severity) - SEV_ORDER.indexOf(b.severity)) : []),
    [scan],
  );
  const visibleFindings = useMemo(
    () => orderedFindings.filter((f) => showFiltered || f.ai_verdict !== 'likely_false_positive'),
    [orderedFindings, showFiltered],
  );
  const hiddenCount = orderedFindings.length - visibleFindings.length;

  const tabs: { id: Tab; label: string; icon: typeof FileText }[] = [
    { id: 'overview',  label: 'Overview',  icon: FileText },
    { id: 'findings',  label: `Findings (${visibleFindings.length})`, icon: BarChart3 },
    { id: 'chat',      label: 'AI Chat',   icon: MessageSquare },
    { id: 'scheduler', label: 'Scheduler', icon: Calendar },
  ];

  return (
    <section className="bg-surface-container border border-outline-variant rounded-xl flex flex-col h-full overflow-hidden">

      {/* Header */}
      <div className="px-5 py-3 border-b border-outline-variant flex justify-between items-center shrink-0">
        <h3 className="text-[14px] font-semibold text-on-background flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-primary" /> Results
        </h3>
        {isRunning && scan && (
          <span className="flex items-center gap-1.5 text-[12px] font-medium text-primary">
            <Loader2 className="w-3 h-3 animate-spin" /> {scan.status} · {scan.progress}%
          </span>
        )}
      </div>

      {/* Tabs */}
      <div className="flex items-center border-b border-outline-variant px-3 shrink-0 overflow-x-auto gap-0.5">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => {
              if (id === 'chat' && onNavigateToChat) { onNavigateToChat(); return; }
              setTab(id);
            }}
            className={`flex items-center gap-1.5 px-3 py-2.5 text-[13px] font-medium border-b-2 transition-colors cursor-pointer whitespace-nowrap ${
              tab === id ? 'text-primary border-primary' : 'text-on-surface-variant border-transparent hover:text-on-background'
            }`}
          >
            <Icon className="w-3.5 h-3.5" /> {label}
          </button>
        ))}
        {scan?.status === 'completed' && (
          <div className="ml-auto flex items-center gap-1">
            <button
              onClick={() => window.open(getExportUrl(scan.id, 'html'), '_blank')}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-[12px] font-medium text-on-surface-variant hover:text-on-background hover:bg-surface-container-high transition-colors cursor-pointer"
            >
              <FileDown className="w-3 h-3" /> Export HTML
            </button>
            <button
              onClick={() => window.open(getExportUrl(scan.id, 'json'), '_blank')}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-[12px] font-medium text-on-surface-variant hover:text-on-background hover:bg-surface-container-high transition-colors cursor-pointer"
            >
              <Download className="w-3 h-3" /> JSON
            </button>
            <button
              onClick={() => onViewReport(scan.id)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-[12px] font-medium text-on-surface-variant hover:text-on-background hover:bg-surface-container-high transition-colors cursor-pointer"
            >
              <ExternalLink className="w-3 h-3" /> Report
            </button>
          </div>
        )}
      </div>

      {/* Body */}
      <div className="flex-1 p-5 overflow-y-auto">
        {!scan ? (
          <div className="h-full flex flex-col items-center justify-center text-center gap-3 py-12">
            <ShieldCheck className="w-10 h-10 text-outline" />
            <p className="text-[14px] font-medium text-on-background">No scan selected</p>
            <p className="text-[13px] text-on-surface-variant">Select a scan from the left panel.</p>
          </div>
        ) : tab === 'overview' ? (
          <div className="space-y-5">
            <SmartReconBanner scan={scan} />
            <div className="grid grid-cols-4 gap-3">
              {[
                { v: String(scans.length), l: 'Scans', c: 'text-primary' },
                { v: String(scan.findings_count), l: 'Findings', c: scan.findings_count > 0 ? 'text-tertiary' : 'text-on-surface-variant' },
                { v: `${scannerCount}/3`, l: 'Scanners', c: 'text-on-background' },
                { v: health?.ollama_available ? 'Online' : 'Off', l: 'AI', c: health?.ollama_available ? 'text-secondary' : 'text-on-surface-variant' },
              ].map(({ v, l, c }) => (
                <div key={l} className="bg-surface-container-high border border-outline-variant rounded-lg px-3 py-3">
                  <div className={`text-lg font-bold ${c}`}>{v}</div>
                  <div className="text-[11px] text-on-surface-variant font-medium uppercase">{l}</div>
                </div>
              ))}
            </div>

            {/* Findings table */}
            <div className="border border-outline-variant rounded-lg overflow-hidden">
              <div className="flex justify-between items-center px-4 py-2.5 border-b border-outline-variant bg-surface-container-high">
                <span className="text-[13px] font-semibold text-on-background">Findings ({visibleFindings.slice(0, 10).length})</span>
                {hiddenCount > 0 && (
                  <button onClick={() => setShowFiltered((v) => !v)} className="text-[11px] text-on-surface-variant hover:text-primary flex items-center gap-1 cursor-pointer">
                    {showFiltered ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                    {showFiltered ? 'Hide filtered' : `${hiddenCount} filtered`}
                  </button>
                )}
              </div>
              {visibleFindings.slice(0, 10).length === 0 ? (
                <div className="px-4 py-8 text-center text-[13px] text-on-surface-variant">No findings for {scan.target}</div>
              ) : (
                <div className="divide-y divide-outline-variant/60">
                  {visibleFindings.slice(0, 10).map((f) => (
                    <div key={f.id} className="flex items-center gap-3 px-4 py-3 hover:bg-surface-container-high/50 transition-colors text-[13px]">
                      <span className={`w-2 h-2 rounded-full shrink-0 ${SEV[f.severity].dot}`} />
                      <span className="font-medium text-on-background truncate flex-1 min-w-0">{f.host}</span>
                      <span className="text-on-surface-variant text-[11px] uppercase shrink-0">{f.scanner_source}</span>
                      <span className={`text-[11px] font-semibold shrink-0 ${SEV[f.severity].color}`}>{SEV[f.severity].label}</span>
                      <span className="text-on-surface-variant font-mono text-[11px] shrink-0">{f.port ?? '—'}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

        ) : tab === 'findings' ? (
          <div className="space-y-3">
            {hiddenCount > 0 && (
              <button onClick={() => setShowFiltered((v) => !v)} className="flex items-center gap-2 text-[13px] px-4 py-2 rounded-lg bg-surface-container-high border border-outline-variant text-on-surface-variant hover:text-on-background transition-colors cursor-pointer font-medium">
                {showFiltered ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                {showFiltered ? `Hide ${hiddenCount} filtered` : `${hiddenCount} hidden by AI — show`}
              </button>
            )}
            {visibleFindings.length === 0 ? (
              <div className="text-center text-on-surface-variant py-16 text-[13px]">
                {isRunning ? 'Scan in progress…' : 'No vulnerabilities detected.'}
              </div>
            ) : visibleFindings.map((f) => {
              const sev = SEV[f.severity];
              const canPoc = f.severity === 'critical' || f.severity === 'high';
              return (
                <article key={f.id} className={`border rounded-xl p-5 space-y-3 ${f.ai_verdict === 'likely_false_positive' ? 'border-outline-variant/40 opacity-50' : 'border-outline-variant hover:border-outline transition-colors'}`}>
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`inline-flex items-center gap-1 text-[12px] font-semibold px-2 py-1 rounded border ${sev.badge}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${sev.dot}`} /> {sev.label}
                      </span>
                      {f.cvss_score !== null && f.cvss_score !== undefined && (
                        <span className="inline-flex items-center text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-surface-container-highest border border-outline-variant text-on-surface-variant">
                          CVSS {f.cvss_score.toFixed(1)}
                        </span>
                      )}
                      <h4 className="text-[14px] font-semibold text-on-background">{f.title}</h4>
                      <AiVerdictBadge finding={f} />
                    </div>
                    <span className="text-[12px] text-on-surface-variant">{f.host}{f.port ? `:${f.port}` : ''} · <span className="uppercase font-medium">{f.scanner_source}</span></span>
                  </div>
                  {f.description && <p className="text-[13px] text-on-surface-variant leading-relaxed">{f.description}</p>}
                  {f.cve_ids.length > 0 && (
                    <div className="flex gap-1.5 flex-wrap">
                      {f.cve_ids.map((cve) => (
                        <a key={cve} href={`https://nvd.nist.gov/vuln/detail/${cve}`} target="_blank" rel="noopener noreferrer" className="text-[11px] font-medium px-2 py-1 rounded bg-error/8 border border-error/25 text-error hover:bg-error/15 transition-colors">{cve}</a>
                      ))}
                    </div>
                  )}
                  {canPoc && <PocViewer findingId={f.id} hasPoc={f.has_poc} />}
                </article>
              );
            })}
          </div>
        ) : tab === 'chat' ? (
          scan.status === 'completed' ? (
            <ChatPanel jobId={scan.id} target={scan.target} />
          ) : (
            <div className="h-full flex flex-col items-center justify-center gap-3 py-12 text-center">
              <MessageSquare className="w-10 h-10 text-outline" />
              <p className="text-[14px] font-medium text-on-background">Chat available after scan completes</p>
            </div>
          )
        ) : (
          <div className="h-full flex flex-col items-center justify-center gap-3 py-12 text-center">
            <Calendar className="w-10 h-10 text-outline" />
            <p className="text-[14px] font-medium text-on-background">Scheduler & Automation</p>
            <p className="text-[13px] text-on-surface-variant">Recurring scans and CI/CD integrations.</p>
          </div>
        )}
      </div>
    </section>
  );
}
