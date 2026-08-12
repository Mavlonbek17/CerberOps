import { useState } from 'react';
import { Network, Radar, Globe, ArrowRight, Loader2, Sparkles, Lock, Search } from 'lucide-react';

interface Props {
  onSubmit: (target: string, scanners: string[], allowInternal: boolean, smartRecon: boolean) => void;
  loading: boolean;
}

const SCANNERS = [
  {
    id: 'nmap',
    label: 'Nmap',
    desc: 'Ports & Services',
    icon: Network,
    activeColor: 'text-[#4493f8]',
    activeBg: 'bg-[#4493f8]/10',
    activeBorder: 'border-[#4493f8]/40',
    iconBg: 'bg-[#4493f8]/15',
    dot: 'bg-[#4493f8]',
  },
  {
    id: 'nuclei',
    label: 'Nuclei',
    desc: 'CVEs & Misconfig',
    icon: Radar,
    activeColor: 'text-[#f85149]',
    activeBg: 'bg-[#f85149]/10',
    activeBorder: 'border-[#f85149]/40',
    iconBg: 'bg-[#f85149]/15',
    dot: 'bg-[#f85149]',
  },
  {
    id: 'zap',
    label: 'ZAP',
    desc: 'Web App DAST',
    icon: Globe,
    activeColor: 'text-[#d29922]',
    activeBg: 'bg-[#d29922]/10',
    activeBorder: 'border-[#d29922]/40',
    iconBg: 'bg-[#d29922]/15',
    dot: 'bg-[#d29922]',
  },
];

export default function ScanForm({ onSubmit, loading }: Props) {
  const [target, setTarget] = useState('');
  const [scanners, setScanners] = useState<string[]>(['nmap', 'nuclei']);
  const [allowInternal, setAllowInternal] = useState(false);
  const [smartRecon, setSmartRecon] = useState(true);

  const toggle = (id: string) =>
    setScanners((p) => (p.includes(id) ? p.filter((s) => s !== id) : [...p, id]));

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!target.trim() || scanners.length === 0) return;
    onSubmit(target.trim(), scanners, allowInternal, smartRecon);
  };

  const ready = target.trim().length > 0 && scanners.length > 0 && !loading;

  return (
    <form
      id="new-scan-form"
      onSubmit={submit}
      className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden"
    >
      {/* Card header */}
      <div className="px-6 py-4 border-b border-outline-variant">
        <h3 className="text-[15px] font-semibold text-on-background">New Scan</h3>
        <p className="text-[13px] text-on-surface-variant mt-0.5">Enter a target URL or IP address to begin</p>
      </div>

      <div className="px-6 py-5 space-y-5">
        {/* Target input — full width, tall */}
        <div className="space-y-1.5">
          <label className="text-[13px] font-medium text-on-surface-variant">Target</label>
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant/60 pointer-events-none" />
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder="https://example.com  or  93.184.216.34"
              disabled={loading}
              className="w-full bg-surface-container-low border border-outline-variant rounded-xl pl-11 pr-4 py-4 text-[15px] text-on-background font-mono focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all placeholder:text-on-surface-variant/40 disabled:opacity-50"
            />
          </div>
        </div>

        {/* Scanner engine cards */}
        <div className="space-y-1.5">
          <label className="text-[13px] font-medium text-on-surface-variant">Scan Engines</label>
          <div className="grid grid-cols-3 gap-3">
            {SCANNERS.map(({ id, label, desc, icon: Icon, activeColor, activeBg, activeBorder, iconBg, dot }) => {
              const on = scanners.includes(id);
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => toggle(id)}
                  className={`flex flex-col gap-3 p-4 rounded-xl border text-left transition-all cursor-pointer ${
                    on
                      ? `${activeBg} ${activeBorder}`
                      : 'bg-surface-container-low border-outline-variant hover:border-outline hover:bg-surface-container-high/30'
                  }`}
                >
                  {/* Icon + toggle */}
                  <div className="flex items-start justify-between w-full">
                    <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${on ? iconBg : 'bg-surface-container-high'}`}>
                      <Icon className={`w-4.5 h-4.5 ${on ? activeColor : 'text-on-surface-variant'}`} strokeWidth={1.8} />
                    </div>
                    <div className={`w-4.5 h-4.5 rounded-full border-2 flex items-center justify-center transition-all mt-0.5 ${
                      on ? `${activeBorder} ${activeBg}` : 'border-outline-variant'
                    }`}>
                      {on && <div className={`w-2 h-2 rounded-full ${dot}`} />}
                    </div>
                  </div>
                  {/* Label + desc */}
                  <div>
                    <div className={`text-[14px] font-semibold leading-tight ${on ? activeColor : 'text-on-background'}`}>
                      {label}
                    </div>
                    <div className="text-[11px] text-on-surface-variant mt-0.5">{desc}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Options row */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <button
            type="button"
            onClick={() => setSmartRecon((v) => !v)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-lg border text-[13px] font-medium transition-all cursor-pointer ${
              smartRecon
                ? 'bg-[#bc8cff]/10 border-[#bc8cff]/40 text-[#bc8cff]'
                : 'bg-transparent border-outline-variant text-on-surface-variant hover:text-on-background hover:border-outline'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" strokeWidth={1.8} />
            Smart Recon
            <span className={`w-1.5 h-1.5 rounded-full ${smartRecon ? 'bg-[#bc8cff]' : 'bg-outline-variant'}`} />
          </button>

          <label className={`flex items-center gap-2 px-3.5 py-2 rounded-lg border text-[13px] font-medium cursor-pointer transition-all ${
            allowInternal
              ? 'bg-[#d29922]/10 border-[#d29922]/40 text-[#d29922]'
              : 'border-outline-variant text-on-surface-variant hover:text-on-background hover:border-outline'
          }`}>
            <Lock className="w-3.5 h-3.5" strokeWidth={1.8} />
            <input
              type="checkbox"
              checked={allowInternal}
              onChange={(e) => setAllowInternal(e.target.checked)}
              className="sr-only"
            />
            Internal targets
            <span className={`w-1.5 h-1.5 rounded-full ${allowInternal ? 'bg-[#d29922]' : 'bg-outline-variant'}`} />
          </label>
        </div>
      </div>

      {/* Launch Scan — full-width footer button */}
      <div className="px-6 py-4 border-t border-outline-variant bg-surface-container-high/40">
        <button
          type="submit"
          disabled={!ready}
          className="w-full flex items-center justify-center gap-2.5 bg-primary text-on-primary font-semibold py-3.5 rounded-xl text-[15px] cursor-pointer hover:brightness-110 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading ? (
            <><Loader2 className="w-5 h-5 animate-spin" /> Scanning…</>
          ) : (
            <><span>Launch Scan</span><ArrowRight className="w-5 h-5" /></>
          )}
        </button>
      </div>
    </form>
  );
}
