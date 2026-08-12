import { useState } from 'react';
import { Shield, ExternalLink, FileText, ChevronDown, ChevronUp } from 'lucide-react';
import type { ScanDetail as ScanDetailType, Finding, Severity } from '../types';

interface Props {
  scan: ScanDetailType;
  onViewReport: (jobId: string) => void;
}

const SEVERITY_COLORS: Record<Severity, string> = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  info: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
};

const SEVERITY_ORDER: Severity[] = ['critical', 'high', 'medium', 'low', 'info'];

function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${SEVERITY_COLORS[severity]}`}>
      {severity.toUpperCase()}
    </span>
  );
}

function FindingRow({ finding }: { finding: Finding }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border-b border-[var(--border)] last:border-0">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-3 text-left hover:bg-[var(--bg-primary)] transition-colors flex items-start gap-3"
      >
        <SeverityBadge severity={finding.severity} />
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium">{finding.title}</div>
          <div className="text-xs text-[var(--text-secondary)] mt-0.5">
            {finding.host}{finding.port ? `:${finding.port}` : ''}
            {finding.scanner_source && ` | ${finding.scanner_source}`}
          </div>
        </div>
        {expanded ? <ChevronUp className="w-4 h-4 mt-1 shrink-0" /> : <ChevronDown className="w-4 h-4 mt-1 shrink-0" />}
      </button>

      {expanded && (
        <div className="px-3 pb-3 ml-20 text-sm space-y-2">
          {finding.description && (
            <div>
              <span className="text-[var(--text-secondary)]">Description: </span>
              {finding.description}
            </div>
          )}
          {finding.url && (
            <div className="flex items-center gap-1">
              <span className="text-[var(--text-secondary)]">URL: </span>
              <a href={finding.url} target="_blank" rel="noopener noreferrer" className="text-[var(--accent)] hover:underline flex items-center gap-1">
                {finding.url.substring(0, 80)} <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}
          {finding.cve_ids.length > 0 && (
            <div>
              <span className="text-[var(--text-secondary)]">CVEs: </span>
              {finding.cve_ids.map((cve) => (
                <a
                  key={cve}
                  href={`https://nvd.nist.gov/vuln/detail/${cve}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[var(--accent)] hover:underline mr-2"
                >
                  {cve}
                </a>
              ))}
            </div>
          )}
          {finding.evidence && (
            <div>
              <span className="text-[var(--text-secondary)]">Evidence: </span>
              <code className="text-xs bg-[var(--bg-primary)] px-1.5 py-0.5 rounded">{finding.evidence.substring(0, 200)}</code>
            </div>
          )}
          {finding.remediation && (
            <div className="mt-2 p-2 bg-[var(--success)]/10 border border-[var(--success)]/20 rounded text-xs">
              <span className="font-medium text-[var(--success)]">Remediation: </span>
              {finding.remediation}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ScanDetailView({ scan, onViewReport }: Props) {
  const sortedFindings = [...scan.findings].sort(
    (a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity)
  );

  return (
    <div className="bg-[var(--bg-card)] rounded-lg border border-[var(--border)]">
      {/* Header */}
      <div className="p-4 border-b border-[var(--border)]">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Shield className="w-5 h-5 text-[var(--accent)]" />
            Scan Results
          </h2>
          {scan.status === 'completed' && (
            <button
              onClick={() => onViewReport(scan.id)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-[var(--accent)]/10 text-[var(--accent)] hover:bg-[var(--accent)]/20 rounded-lg transition-colors"
            >
              <FileText className="w-4 h-4" />
              AI Report
            </button>
          )}
        </div>

        <div className="text-sm text-[var(--text-secondary)] mb-3">
          Target: <span className="text-[var(--text-primary)]">{scan.target}</span>
        </div>

        {/* Progress bar */}
        {scan.status !== 'completed' && scan.status !== 'failed' && (
          <div className="w-full h-1.5 bg-[var(--bg-primary)] rounded-full overflow-hidden mb-3">
            <div
              className="h-full bg-[var(--accent)] rounded-full transition-all duration-500"
              style={{ width: `${scan.progress}%` }}
            />
          </div>
        )}

        {/* Severity summary */}
        <div className="flex gap-2 flex-wrap">
          {SEVERITY_ORDER.map((sev) => {
            const count = scan.severity_counts[sev] || 0;
            if (count === 0) return null;
            return (
              <span key={sev} className={`px-2 py-1 rounded text-xs font-medium border ${SEVERITY_COLORS[sev]}`}>
                {count} {sev.toUpperCase()}
              </span>
            );
          })}
          {scan.findings_count === 0 && scan.status === 'completed' && (
            <span className="text-sm text-[var(--success)]">No vulnerabilities found</span>
          )}
        </div>
      </div>

      {/* Findings list */}
      <div className="max-h-[600px] overflow-y-auto">
        {sortedFindings.map((f) => (
          <FindingRow key={f.id} finding={f} />
        ))}
      </div>
    </div>
  );
}
