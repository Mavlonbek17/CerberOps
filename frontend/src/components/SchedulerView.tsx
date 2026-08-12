import { useState, useEffect } from 'react';
import { CalendarClock, Plus, Trash2, Play, Pause, Clock, Network, Radar, Globe } from 'lucide-react';
import { listScheduledScans, createScheduledScan, deleteScheduledScan, toggleScheduledScan } from '../api/client';
import type { ScheduledScan } from '../types';

const SCANNERS_OPTIONS = [
  { id: 'nmap', label: 'Nmap', icon: Network },
  { id: 'nuclei', label: 'Nuclei', icon: Radar },
  { id: 'zap', label: 'ZAP', icon: Globe },
];

export default function SchedulerView() {
  const [schedules, setSchedules] = useState<ScheduledScan[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [target, setTarget] = useState('');
  const [scanners, setScanners] = useState(['nmap', 'nuclei']);
  const [schedule, setSchedule] = useState<'daily' | 'weekly' | 'monthly'>('weekly');
  const [tags, setTags] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    listScheduledScans().then(setSchedules).catch(console.error).finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!target.trim() || scanners.length === 0) return;
    setSaving(true);
    try {
      const created = await createScheduledScan({
        target: target.trim(), scanners, tags, schedule,
        enabled: true, allow_internal: false, smart_recon: true,
      });
      setSchedules(s => [created, ...s]);
      setTarget(''); setTags([]); setShowForm(false);
    } catch (e) { console.error(e); } finally { setSaving(false); }
  };

  const handleToggle = async (id: string, enabled: boolean) => {
    const updated = await toggleScheduledScan(id, !enabled);
    setSchedules(s => s.map(x => x.id === id ? updated : x));
  };

  const handleDelete = async (id: string) => {
    await deleteScheduledScan(id);
    setSchedules(s => s.filter(x => x.id !== id));
  };

  const relTime = (iso: string | null) => {
    if (!iso) return 'Never';
    const d = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
    if (d < 60) return 'just now';
    const m = Math.floor(d / 60);
    if (m < 60) return `${m}m ago`;
    const h = Math.floor(m / 60);
    return h < 24 ? `${h}h ago` : `${Math.floor(h/24)}d ago`;
  };

  const nextTime = (iso: string | null) => {
    if (!iso) return '—';
    const diff = Math.floor((new Date(iso).getTime() - Date.now()) / 1000);
    if (diff < 0) return 'Due now';
    const h = Math.floor(diff / 3600);
    if (h < 24) return `in ${h}h`;
    return `in ${Math.floor(h/24)}d`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[20px] font-bold text-on-background">Scheduler</h2>
          <p className="text-[13px] text-on-surface-variant mt-1">Automate recurring scans on a daily, weekly, or monthly basis.</p>
        </div>
        <button
          onClick={() => setShowForm(v => !v)}
          className="flex items-center gap-2 bg-primary text-on-primary font-semibold px-5 py-2.5 rounded-xl text-[14px] cursor-pointer hover:brightness-110 transition-all"
        >
          <Plus className="w-4 h-4" /> New Schedule
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <form onSubmit={handleCreate} className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-outline-variant">
            <h3 className="text-[14px] font-semibold text-on-background">New Scheduled Scan</h3>
          </div>
          <div className="px-5 py-5 space-y-4">
            <div className="space-y-1.5">
              <label className="text-[13px] font-medium text-on-surface-variant">Target</label>
              <input
                type="text" value={target} onChange={e => setTarget(e.target.value)}
                placeholder="https://example.com"
                className="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-[14px] text-on-background font-mono focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-[13px] font-medium text-on-surface-variant">Frequency</label>
                <select value={schedule} onChange={e => setSchedule(e.target.value as 'daily' | 'weekly' | 'monthly')}
                  className="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3 text-[14px] text-on-background focus:outline-none focus:border-primary cursor-pointer">
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <label className="text-[13px] font-medium text-on-surface-variant">Scanners</label>
                <div className="flex gap-2">
                  {SCANNERS_OPTIONS.map(({ id, label }) => {
                    const on = scanners.includes(id);
                    return (
                      <button key={id} type="button" onClick={() => setScanners(s => on ? s.filter(x => x !== id) : [...s, id])}
                        className={`flex-1 py-3 rounded-xl border text-[13px] font-medium transition-all cursor-pointer ${on ? 'bg-primary/10 border-primary/40 text-primary' : 'bg-surface-container-low border-outline-variant text-on-surface-variant hover:border-outline'}`}>
                        {label}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Tags input */}
            <div className="space-y-1.5">
              <label className="text-[13px] font-medium text-on-surface-variant">
                Tags <span className="text-on-surface-variant/50 font-normal">(optional — press Enter to add)</span>
              </label>
              <div className="flex flex-wrap gap-2 p-3 bg-surface-container-low border border-outline-variant rounded-xl min-h-[44px]">
                {tags.map(tag => (
                  <span key={tag} className="flex items-center gap-1 px-2.5 py-1 bg-primary/10 border border-primary/25 text-primary text-[12px] font-medium rounded-lg">
                    {tag}
                    <button type="button" onClick={() => setTags(t => t.filter(x => x !== tag))} className="hover:text-error cursor-pointer">×</button>
                  </span>
                ))}
                <input
                  type="text"
                  placeholder={tags.length === 0 ? "production, web-app…" : ""}
                  className="flex-1 min-w-[120px] bg-transparent text-[13px] text-on-background placeholder:text-on-surface-variant/40 focus:outline-none"
                  onKeyDown={(e) => {
                    if ((e.key === 'Enter' || e.key === ',') && e.currentTarget.value.trim()) {
                      e.preventDefault();
                      const val = e.currentTarget.value.trim().replace(/,/g, '');
                      if (val && !tags.includes(val)) setTags(t => [...t, val]);
                      e.currentTarget.value = '';
                    }
                  }}
                />
              </div>
            </div>
          </div>
          <div className="px-5 py-4 border-t border-outline-variant bg-surface-container-high/40 flex gap-3 justify-end">
            <button type="button" onClick={() => setShowForm(false)} className="px-4 py-2.5 rounded-xl text-[14px] font-medium text-on-surface-variant border border-outline-variant hover:border-outline cursor-pointer transition-colors">Cancel</button>
            <button type="submit" disabled={!target.trim() || scanners.length === 0 || saving}
              className="px-6 py-2.5 rounded-xl bg-primary text-on-primary font-semibold text-[14px] cursor-pointer hover:brightness-110 transition-all disabled:opacity-40 disabled:cursor-not-allowed">
              {saving ? 'Saving…' : 'Create Schedule'}
            </button>
          </div>
        </form>
      )}

      {/* Schedule list */}
      {loading ? (
        <div className="text-center py-12 text-on-surface-variant text-[13px]">Loading…</div>
      ) : schedules.length === 0 && !showForm ? (
        <div className="bg-surface-container border border-outline-variant rounded-xl py-16 text-center">
          <CalendarClock className="w-10 h-10 text-outline mx-auto mb-3" />
          <p className="text-[14px] font-medium text-on-background">No scheduled scans yet</p>
          <p className="text-[13px] text-on-surface-variant mt-1">Create one to automatically scan targets on a recurring basis.</p>
        </div>
      ) : schedules.length > 0 ? (
        <div className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
          <div className="grid grid-cols-12 px-5 py-3 border-b border-outline-variant bg-surface-container-high text-[12px] font-semibold text-on-surface-variant uppercase tracking-wide">
            <div className="col-span-4">Target</div>
            <div className="col-span-2">Frequency</div>
            <div className="col-span-2">Last run</div>
            <div className="col-span-2">Next run</div>
            <div className="col-span-2 text-right">Actions</div>
          </div>
          <div className="divide-y divide-outline-variant/60">
            {schedules.map(s => (
              <div key={s.id} className={`grid grid-cols-12 px-5 py-4 items-center text-[13px] ${!s.enabled ? 'opacity-50' : ''}`}>
                <div className="col-span-4">
                  <div className="font-medium text-on-background truncate pr-3">{s.target.replace(/^https?:\/\//, '')}</div>
                  <div className="text-[11px] text-on-surface-variant mt-0.5">{s.scanners.map(x => x.toUpperCase()).join(' · ')}</div>
                </div>
                <div className="col-span-2">
                  <span className="capitalize text-on-surface-variant">{s.schedule}</span>
                </div>
                <div className="col-span-2 text-on-surface-variant">{relTime(s.last_run_at)}</div>
                <div className="col-span-2 flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-primary shrink-0" />
                  <span className="text-primary font-medium">{nextTime(s.next_run_at)}</span>
                </div>
                <div className="col-span-2 flex items-center justify-end gap-2">
                  <button onClick={() => handleToggle(s.id, s.enabled)} title={s.enabled ? 'Pause' : 'Resume'}
                    className="p-2 rounded-lg hover:bg-surface-container-high transition-colors cursor-pointer text-on-surface-variant hover:text-on-background">
                    {s.enabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </button>
                  <button onClick={() => handleDelete(s.id)} title="Delete"
                    className="p-2 rounded-lg hover:bg-error/10 transition-colors cursor-pointer text-on-surface-variant hover:text-error">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
