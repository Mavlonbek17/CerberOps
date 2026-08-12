import { Clock, AlertTriangle, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import type { ScanSummary, ScanStatus } from '../types';

interface Props {
  scans: ScanSummary[];
  onSelect: (id: string) => void;
  selectedId: string | null;
}

const STATUS_CONFIG: Record<ScanStatus, { icon: typeof Clock; color: string; label: string }> = {
  queued: { icon: Clock, color: 'text-yellow-400', label: 'Queued' },
  running: { icon: Loader2, color: 'text-blue-400', label: 'Running' },
  parsing: { icon: Loader2, color: 'text-blue-400', label: 'Parsing' },
  analyzing: { icon: Loader2, color: 'text-purple-400', label: 'Analyzing' },
  completed: { icon: CheckCircle, color: 'text-green-400', label: 'Completed' },
  failed: { icon: XCircle, color: 'text-red-400', label: 'Failed' },
  cancelled: { icon: XCircle, color: 'text-gray-400', label: 'Cancelled' },
};

export default function ScanList({ scans, onSelect, selectedId }: Props) {
  if (scans.length === 0) {
    return (
      <div className="bg-[var(--bg-card)] rounded-lg border border-[var(--border)] p-6">
        <p className="text-[var(--text-secondary)] text-center">No scans yet. Start one above.</p>
      </div>
    );
  }

  return (
    <div className="bg-[var(--bg-card)] rounded-lg border border-[var(--border)]">
      <div className="p-4 border-b border-[var(--border)]">
        <h2 className="text-lg font-semibold">Recent Scans</h2>
      </div>
      <div className="divide-y divide-[var(--border)]">
        {scans.map((scan) => {
          const cfg = STATUS_CONFIG[scan.status];
          const Icon = cfg.icon;
          const isActive = scan.status === 'running' || scan.status === 'parsing' || scan.status === 'analyzing';

          return (
            <button
              key={scan.id}
              onClick={() => onSelect(scan.id)}
              className={`w-full p-4 text-left hover:bg-[var(--bg-primary)] transition-colors ${
                selectedId === scan.id ? 'bg-[var(--bg-primary)]' : ''
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium truncate max-w-[70%]">{scan.target}</span>
                <div className={`flex items-center gap-1.5 text-xs ${cfg.color}`}>
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'animate-spin' : ''}`} />
                  {cfg.label}
                </div>
              </div>
              <div className="flex items-center justify-between text-xs text-[var(--text-secondary)]">
                <span>{scan.scanners.join(', ')}</span>
                <div className="flex items-center gap-3">
                  {scan.findings_count > 0 && (
                    <span className="flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      {scan.findings_count}
                    </span>
                  )}
                  <span>{new Date(scan.created_at).toLocaleString()}</span>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
