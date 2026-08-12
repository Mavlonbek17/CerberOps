import { Clock, CheckCircle2, XCircle, Loader2, Trash2, RotateCw } from 'lucide-react';
import type { ScanSummary, ScanStatus } from '../types';

interface Props {
  scans: ScanSummary[];
  onSelect: (id: string) => void;
  onCancel: (id: string) => void;
  selectedId: string | null;
}

const STATUS: Record<ScanStatus, { icon: typeof Clock; color: string; label: string; spin?: boolean }> = {
  queued:    { icon: Clock,        color: 'text-tertiary',          label: 'Queued' },
  running:   { icon: RotateCw,     color: 'text-primary',           label: 'Running',   spin: true },
  parsing:   { icon: Loader2,      color: 'text-primary',           label: 'Parsing',   spin: true },
  analyzing: { icon: Loader2,      color: 'text-primary',           label: 'Analyzing', spin: true },
  completed: { icon: CheckCircle2, color: 'text-secondary',         label: 'Done' },
  failed:    { icon: XCircle,      color: 'text-error',             label: 'Failed' },
  cancelled: { icon: XCircle,      color: 'text-on-surface-variant', label: 'Cancelled' },
};

export default function ScanList({ scans, onSelect, onCancel, selectedId }: Props) {
  return (
    <div className="bg-surface-container border border-outline-variant rounded-xl flex flex-col h-full overflow-hidden">

      <div className="px-4 py-3 border-b border-outline-variant flex items-center justify-between shrink-0">
        <h3 className="text-[14px] font-semibold text-on-background">Scans</h3>
        <span className="text-[12px] text-on-surface-variant font-medium">{scans.length}</span>
      </div>

      <div className="flex-1 overflow-y-auto divide-y divide-outline-variant/60">
        {scans.length === 0 && (
          <div className="py-12 text-center text-[13px] text-on-surface-variant">
            No scans yet.
          </div>
        )}

        {scans.map((scan) => {
          const cfg = STATUS[scan.status];
          const Icon = cfg.icon;
          const isCancellable = ['queued', 'running', 'parsing', 'analyzing'].includes(scan.status);
          const sel = selectedId === scan.id;

          return (
            <div
              key={scan.id}
              className={`group relative px-4 py-3.5 transition-colors cursor-pointer ${
                sel ? 'bg-primary/8' : 'hover:bg-surface-container-high/60'
              }`}
              onClick={() => onSelect(scan.id)}
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-[13px] font-medium text-on-background truncate max-w-[180px]">
                  {scan.target.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                </span>
                <span className={`flex items-center gap-1 text-[11px] font-medium ${cfg.color}`}>
                  <Icon className={`w-3 h-3 ${cfg.spin ? 'animate-spin' : ''}`} />
                  {cfg.label}
                </span>
              </div>

              <div className="flex items-center justify-between text-[11px] text-on-surface-variant">
                <span>{scan.scanners.map((s) => s.toUpperCase()).join(' · ')}</span>
                <span className={scan.findings_count > 0 ? 'text-tertiary font-medium' : ''}>
                  {isCancellable && scan.progress !== undefined ? `${scan.progress}%` : `${scan.findings_count} findings`}
                </span>
              </div>

              {isCancellable && (
                <button
                  onClick={(e) => { e.stopPropagation(); onCancel(scan.id); }}
                  className="absolute top-3 right-3 p-1 rounded text-on-surface-variant hover:text-error opacity-0 group-hover:opacity-100 transition-all cursor-pointer"
                  title="Cancel scan"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
