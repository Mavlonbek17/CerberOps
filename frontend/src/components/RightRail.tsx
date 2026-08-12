import { Activity, Loader2 } from 'lucide-react';
import type { ScanDetail, ScanSummary } from '../types';

interface Props {
  scan: ScanDetail | null;
  scans: ScanSummary[];
}

function relativeTime(iso: string): string {
  const d = Date.now() - new Date(iso).getTime();
  const s = Math.floor(d / 1000);
  if (s < 60) return 'just now';
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function SeverityPanel({ scan }: { scan: ScanDetail | null }) {
  const counts = scan?.severity_counts ?? {};
  const bins = [
    { label: 'C', count: counts.critical ?? 0, color: 'bg-red' },
    { label: 'H', count: counts.high ?? 0, color: 'bg-orange' },
    { label: 'M', count: counts.medium ?? 0, color: 'bg-amber' },
    { label: 'L', count: counts.low ?? 0, color: 'bg-secondary' },
    { label: 'I', count: counts.info ?? 0, color: 'bg-blue' },
  ];
  const maxVal = Math.max(...bins.map((b) => b.count), 1);

  return (
    <div className="bg-surface-container border border-outline-variant rounded-xl p-4">
      <h3 className="text-[13px] font-semibold text-on-background mb-4">Severity</h3>

      <div className="flex items-end gap-2 h-24 mb-2">
        {bins.map((bin) => {
          const height = bin.count > 0 ? Math.max((bin.count / maxVal) * 100, 12) : 4;
          return (
            <div key={bin.label} className="flex-1 flex flex-col items-center justify-end h-full">
              <div className={`w-full rounded-sm ${bin.color}`} style={{ height: `${height}%` }} />
            </div>
          );
        })}
      </div>

      <div className="flex justify-between text-[11px] text-on-surface-variant font-medium">
        {bins.map((bin) => <span key={bin.label} className="flex-1 text-center">{bin.label}</span>)}
      </div>
    </div>
  );
}

function statusColor(status: string): string {
  if (status === 'completed') return 'text-secondary';
  if (['running', 'parsing', 'analyzing', 'queued'].includes(status)) return 'text-primary';
  if (status === 'failed') return 'text-error';
  return 'text-on-surface-variant';
}

export default function RightRail({ scan, scans }: Props) {
  const recent = scans.slice(0, 8);
  return (
    <div className="flex flex-col gap-4 h-full">
      <SeverityPanel scan={scan} />

      <div className="bg-surface-container border border-outline-variant rounded-xl flex-1 overflow-hidden flex flex-col">
        <div className="px-4 py-3 border-b border-outline-variant">
          <h3 className="text-[13px] font-semibold text-on-background">Activity</h3>
        </div>
        <div className="flex-1 overflow-y-auto divide-y divide-outline-variant/60">
          {recent.length === 0 && (
            <div className="p-4 text-[12px] text-on-surface-variant">No activity yet</div>
          )}
          {recent.map((s) => (
            <div key={s.id} className="flex items-center gap-2.5 px-4 py-2.5 text-[12px]">
              {['running', 'parsing', 'analyzing'].includes(s.status) ? (
                <Loader2 className={`w-3.5 h-3.5 animate-spin ${statusColor(s.status)}`} />
              ) : (
                <Activity className={`w-3.5 h-3.5 ${statusColor(s.status)}`} />
              )}
              <span className={`truncate flex-1 min-w-0 font-medium ${statusColor(s.status)}`}>
                {s.target.replace(/^https?:\/\//, '').replace(/\/$/, '')}
              </span>
              <span className="text-on-surface-variant shrink-0">{relativeTime(s.created_at)}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
