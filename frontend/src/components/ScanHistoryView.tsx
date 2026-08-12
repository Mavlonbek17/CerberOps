import { useState } from 'react';
import { Search, CheckCircle2, RotateCw, XCircle, Clock } from 'lucide-react';
import type { ScanSummary } from '../types';

interface Props {
  scans: ScanSummary[];
  onSelectScan: (id: string) => void;
  onCancelScan?: (id: string) => void;
}

const STATUS_ICON: Record<string, { icon: typeof Clock; color: string }> = {
  completed: { icon: CheckCircle2, color: 'text-secondary' },
  running:   { icon: RotateCw,     color: 'text-primary' },
  failed:    { icon: XCircle,      color: 'text-error' },
  cancelled: { icon: XCircle,      color: 'text-on-surface-variant' },
  queued:    { icon: Clock,        color: 'text-tertiary' },
  parsing:   { icon: RotateCw,     color: 'text-primary' },
  analyzing: { icon: RotateCw,     color: 'text-primary' },
};

export default function ScanHistoryView({ scans, onSelectScan }: Props) {
  const [filter, setFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const filtered = scans.filter((s) => {
    const matchesTarget = s.target.toLowerCase().includes(filter.toLowerCase());
    const matchesStatus = statusFilter === 'all' || s.status === statusFilter;
    return matchesTarget && matchesStatus;
  });

  return (
    <div className="space-y-5">
      <h2 className="text-[18px] font-semibold text-on-background">Scan History</h2>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-on-surface-variant absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter by target…"
            className="w-full pl-10 pr-4 py-3 bg-surface-container border border-outline-variant rounded-xl text-[14px] text-on-background focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-3 bg-surface-container border border-outline-variant rounded-xl text-[14px] text-on-background focus:outline-none focus:border-primary cursor-pointer min-w-[160px]"
        >
          <option value="all">All</option>
          <option value="completed">Completed</option>
          <option value="running">Running</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {/* Summary */}
      <div className="flex items-center gap-5 text-[13px] text-on-surface-variant">
        <span><span className="font-semibold text-on-background">{filtered.length}</span> results</span>
        <span><span className="font-semibold text-secondary">{scans.filter(s => s.status === 'completed').length}</span> completed</span>
        <span><span className="font-semibold text-error">{scans.filter(s => s.status === 'failed').length}</span> failed</span>
      </div>

      {/* Table */}
      <div className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
        <div className="grid grid-cols-12 px-5 py-3 border-b border-outline-variant bg-surface-container-high text-[12px] font-semibold text-on-surface-variant uppercase tracking-wide">
          <div className="col-span-5">Target</div>
          <div className="col-span-3">Scanners</div>
          <div className="col-span-2">Status</div>
          <div className="col-span-2 text-right">Findings</div>
        </div>

        <div className="divide-y divide-outline-variant/60">
          {filtered.length === 0 ? (
            <div className="py-12 text-center text-[13px] text-on-surface-variant">No scans match your filter.</div>
          ) : filtered.map((s) => {
            const st = STATUS_ICON[s.status] ?? STATUS_ICON['cancelled'];
            const Icon = st.icon;
            return (
              <div
                key={s.id}
                onClick={() => onSelectScan(s.id)}
                className="grid grid-cols-12 px-5 py-3.5 items-center hover:bg-surface-container-high/50 transition-colors cursor-pointer text-[13px]"
              >
                <div className="col-span-5 font-medium text-on-background truncate pr-3">{s.target}</div>
                <div className="col-span-3 text-on-surface-variant text-[12px]">{s.scanners.map(sc => sc.toUpperCase()).join(' · ')}</div>
                <div className={`col-span-2 flex items-center gap-1.5 ${st.color}`}>
                  <Icon className={`w-3.5 h-3.5 ${['running','parsing','analyzing'].includes(s.status) ? 'animate-spin' : ''}`} />
                  <span className="capitalize">{s.status}</span>
                </div>
                <div className={`col-span-2 text-right font-medium ${s.findings_count > 0 ? 'text-tertiary' : 'text-on-surface-variant'}`}>
                  {s.findings_count > 0 ? `${s.findings_count}` : '—'}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
