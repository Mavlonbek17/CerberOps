import { useState } from 'react';
import {
  ShieldAlert,
  ExternalLink,
  FileText,
  ChevronDown,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import type { ScanDetail as ScanDetailType, Finding, Severity } from '../types';

interface Props {
  scan: ScanDetailType;
  onViewReport: (jobId: string) => void;
}

const SEV_STYLE: Record<Severity, { bg: string; text: string; dot: string }> = {
  critical: { bg: 'bg-crit/10 border-crit/20', text: 'text-crit', dot: 'bg-crit' },
  high: { bg: 'bg-high/10 border-high/20', text: 'text-high', dot: 'bg-high' },
  medium: { bg: 'bg-med/10 border-med/20', text: 'text-med', dot: 'bg-med' },
  low: { bg: 'bg-low/10 border-low/20', text: 'text-low', dot: 'bg-low' },
  info: { bg: 'bg-info/10 border-info/20', text: 'text-info', dot: 'bg-info' },
};

const SEV_ORDER: Severity[] = ['critical', 'high', 'medium', 'low', 'info'];

function SeverityPill({ severity }: { severity: Severity }) {
  const s = SEV_STYLE[severity];
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium border ${s.bg} ${s.text} uppercase tracking-wider`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {severity}
    </span>
  );
}

function FindingRow({ finding }: { finding: Finding }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="border-b border-border/50 last:border-0">
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-4 py-3 text-left hover:bg-surface-0/30 transition-colors flex items-start gap-3 cursor-pointer"
      >
        <div className="mt-0.5 shrink-0">
          <SeverityPill severity={finding.severity} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium leading-snug">{finding.title}</div>
          <div className="text-[11px] font-mono text-text-3 mt-0.5">
            {finding.host}
            {finding.port ? `:${finding.port}` : ''}
            <span className="mx-1.5 text-border">|</span>
            {finding.scanner_source}
          </div>
        </div>
        <div className="mt-1 shrink-0 text-text-3">
          {open ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </div>
      </button>

      {open && (
        <div className="px-4 pb-4 ml-[88px] space-y-2.5 text-sm">
          {finding.description && (
            <p className="text-text-2 leading-relaxed">{finding.description}</p>
          )}

          {finding.url && (
            <a
              href={finding.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-accent hover:text-accent-hover text-xs font-mono transition-colors"
            >
              {finding.url.substring(0, 80)}
              <ExternalLink className="w-3 h-3" />
            </a>
          )}

          {finding.cve_ids.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {finding.cve_ids.map((cve) => (
                <a
                  key={cve}
                  href={`https://nvd.nist.gov/vuln/detail/${cve}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[11px] font-mono px-2 py-0.5 rounded bg-crit/10 text-crit hover:bg-crit/20 transition-colors"
                >
                  {cve}
                </a>
              ))}
            </div>
          )}

          {finding.evidence && (
            <code className="block text-xs font-mono p-3 rounded-lg bg-surface-0 border border-border text-text-2 overflow-x-auto">
              {finding.evidence.substring(0, 300)}
            </code>
          )}

          {finding.remediation && (
            <div className="p-3 rounded-lg bg-ok/5 border border-ok/15 text-xs text-ok leading-relaxed">
              {finding.remediation}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ScanDetailView({ scan, onViewReport }: Props) {
  const sorted = [...scan.findings].sort(
    (a, b) => SEV_ORDER.indexOf(a.severity) - SEV_ORDER.indexOf(b.severity),
  );

  const isRunning = ['queued', 'running', 'parsing', 'analyzing'].includes(
    scan.status,
  );

  return (
    <div className="bg-surface-1 rounded-xl border border-border overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-border">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-accent" />
            <h2 className="text-sm font-semibold uppercase tracking-wider">
              Results
            </h2>
          </div>
          <div className="flex items-center gap-2">
            {scan.status === 'completed' && (
              <button
                onClick={() => onViewReport(scan.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-accent/10 text-accent hover:bg-accent/20 rounded-lg transition-colors border border-accent/20 cursor-pointer"
              >
                <FileText className="w-3.5 h-3.5" />
                AI Report
              </button>
            )}
          </div>
        </div>

        {/* Target */}
        <div className="font-mono text-sm text-text-2 mb-3">
          {scan.target}
        </div>

        {/* Progress */}
        {isRunning && (
          <div className="mb-3">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-1.5 text-xs text-accent">
                <Loader2 className="w-3 h-3 animate-spin" />
                <span className="capitalize">{scan.status}</span>
              </div>
              <span className="text-xs font-mono text-text-3">
                {scan.progress}%
              </span>
            </div>
            <div className="w-full h-1 bg-surface-3 rounded-full overflow-hidden">
              <div
                className="h-full bg-accent rounded-full transition-all duration-700 ease-out"
                style={{ width: `${scan.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Severity summary */}
        <div className="flex gap-2 flex-wrap">
          {SEV_ORDER.map((sev) => {
            const count = scan.severity_counts[sev] || 0;
            if (count === 0) return null;
            const s = SEV_STYLE[sev];
            return (
              <span
                key={sev}
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono font-medium border ${s.bg} ${s.text}`}
              >
                <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
                {count}
              </span>
            );
          })}
          {scan.findings_count === 0 && scan.status === 'completed' && (
            <span className="text-xs font-mono text-ok">
              No vulnerabilities found
            </span>
          )}
        </div>

        {scan.error_message && (
          <div className="mt-3 p-3 rounded-lg bg-crit/5 border border-crit/15 text-xs text-crit font-mono">
            {scan.error_message}
          </div>
        )}
      </div>

      {/* Findings */}
      <div className="max-h-[550px] overflow-y-auto">
        {sorted.length > 0 ? (
          sorted.map((f) => <FindingRow key={f.id} finding={f} />)
        ) : (
          !isRunning && (
            <div className="p-8 text-center text-text-3 text-sm">
              No findings to display
            </div>
          )
        )}
      </div>
    </div>
  );
}
