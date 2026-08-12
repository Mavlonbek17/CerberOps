import { useState } from 'react';
import { Search, Radar, Globe, Network } from 'lucide-react';

interface Props {
  onSubmit: (target: string, scanners: string[], allowInternal: boolean) => void;
  loading: boolean;
}

const SCANNERS = [
  { id: 'nmap', label: 'Nmap', desc: 'Port & service discovery', icon: Network },
  { id: 'nuclei', label: 'Nuclei', desc: 'Vulnerability templates', icon: Radar },
  { id: 'zap', label: 'OWASP ZAP', desc: 'Web app scanning', icon: Globe },
];

export default function ScanForm({ onSubmit, loading }: Props) {
  const [target, setTarget] = useState('');
  const [selectedScanners, setSelectedScanners] = useState<string[]>(['nmap', 'nuclei', 'zap']);
  const [allowInternal, setAllowInternal] = useState(false);

  const toggleScanner = (id: string) => {
    setSelectedScanners((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!target.trim() || selectedScanners.length === 0) return;
    onSubmit(target.trim(), selectedScanners, allowInternal);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-[var(--bg-card)] rounded-lg border border-[var(--border)] p-6">
      <h2 className="text-lg font-semibold mb-4">New Scan</h2>

      {/* Target input */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-secondary)]" />
        <input
          type="text"
          value={target}
          onChange={(e) => setTarget(e.target.value)}
          placeholder="Enter target URL or IP (e.g., https://example.com)"
          className="w-full pl-11 pr-4 py-3 bg-[var(--bg-primary)] border border-[var(--border)] rounded-lg text-[var(--text-primary)] placeholder:text-[var(--text-secondary)] focus:outline-none focus:border-[var(--accent)] transition-colors"
          disabled={loading}
        />
      </div>

      {/* Scanner selection */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {SCANNERS.map(({ id, label, desc, icon: Icon }) => (
          <button
            key={id}
            type="button"
            onClick={() => toggleScanner(id)}
            className={`p-3 rounded-lg border text-left transition-all ${
              selectedScanners.includes(id)
                ? 'border-[var(--accent)] bg-[var(--accent)]/10'
                : 'border-[var(--border)] hover:border-[var(--text-secondary)]'
            }`}
          >
            <Icon className="w-5 h-5 mb-1" />
            <div className="text-sm font-medium">{label}</div>
            <div className="text-xs text-[var(--text-secondary)]">{desc}</div>
          </button>
        ))}
      </div>

      {/* Options */}
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 text-sm text-[var(--text-secondary)] cursor-pointer">
          <input
            type="checkbox"
            checked={allowInternal}
            onChange={(e) => setAllowInternal(e.target.checked)}
            className="rounded"
          />
          Allow internal targets (testing only)
        </label>

        <button
          type="submit"
          disabled={loading || !target.trim() || selectedScanners.length === 0}
          className="px-6 py-2.5 bg-[var(--accent)] hover:bg-[var(--accent-hover)] disabled:opacity-50 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
        >
          {loading ? 'Starting...' : 'Start Scan'}
        </button>
      </div>
    </form>
  );
}
