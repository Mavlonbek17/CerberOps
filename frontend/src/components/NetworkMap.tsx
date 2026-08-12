import { useState } from 'react';
import { Network, Globe, Radio, Server } from 'lucide-react';
import type { ScanSummary, ScanDetail } from '../types';

interface Props {
  scans: ScanSummary[];
  selectedScan: ScanDetail | null;
  onSelectScan: (id: string) => void;
}

export default function NetworkMap({ scans, selectedScan, onSelectScan }: Props) {
  const [activeHost, setActiveHost] = useState<string | null>(null);

  const targets = Array.from(new Set(scans.map((s) => s.target)));

  return (
    <div className="bg-surface-container-low border border-outline-variant/50 rounded-md p-6 space-y-6 min-h-[600px] flex flex-col">
      <div className="flex items-center justify-between border-b border-outline-variant/40 pb-4">
        <div>
          <h2 className="text-lg font-headline font-bold text-on-background uppercase tracking-wide flex items-center gap-2">
            <Network className="w-5 h-5 text-secondary" /> Network & Topology Map
          </h2>
          <p className="text-xs font-label text-on-surface-variant mt-1">
            Visual attack surface mapping across target hosts, discovered services, and vulnerabilities.
          </p>
        </div>
        <span className="text-xs font-label px-3 py-1 rounded bg-secondary/10 text-secondary border border-secondary/30">
          {targets.length} Discovered Target{targets.length === 1 ? '' : 's'}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        {/* Visual Map Canvas */}
        <div className="lg:col-span-8 bg-surface-container border border-outline-variant/40 rounded-md p-6 relative flex flex-col justify-between overflow-hidden min-h-[380px]">
          <div
            className="absolute inset-0 pointer-events-none"
            style={{
              backgroundImage: 'radial-gradient(#302840 1.5px, transparent 1.5px)',
              backgroundSize: '20px 24px',
              opacity: 0.35,
            }}
          />

          {/* Central Orchestrator Node */}
          <div className="relative z-10 flex justify-center mb-8">
            <div className="bg-surface-container-high border-2 border-primary rounded-md px-5 py-3 shadow-[0_0_20px_rgba(0,214,255,0.25)] flex items-center gap-3">
              <Radio className="w-5 h-5 text-primary animate-pulse" />
              <div>
                <div className="font-headline text-sm font-bold text-on-background">CerberOps Hub</div>
                <div className="font-label text-[10px] text-secondary">Local Security Orchestrator</div>
              </div>
            </div>
          </div>

          {/* Connected Target Nodes */}
          <div className="relative z-10 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 my-auto">
            {scans.slice(0, 6).map((s) => {
              const active = (selectedScan && selectedScan.id === s.id) || activeHost === s.target;
              return (
                <div
                  key={s.id}
                  onClick={() => {
                    setActiveHost(s.target);
                    onSelectScan(s.id);
                  }}
                  className={`bg-surface-container-low border rounded-md p-4 cursor-pointer transition-all hover:scale-[1.02] ${
                    active
                      ? 'border-secondary bg-secondary/10 shadow-[0_0_15px_rgba(0,255,204,0.2)]'
                      : 'border-outline-variant/60 hover:border-outline-variant'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <Globe className={`w-4 h-4 ${active ? 'text-secondary' : 'text-on-surface-variant'}`} />
                    <span className="text-[10px] font-label px-2 py-0.5 rounded bg-surface-container-high text-on-surface-variant">
                      {s.status}
                    </span>
                  </div>
                  <div className="font-headline text-xs font-bold text-on-background truncate">
                    {s.target.replace(/^https?:\/\//, '')}
                  </div>
                  <div className="flex items-center justify-between mt-3 text-[10px] font-label text-on-surface-variant">
                    <span>{s.scanners.join(', ')}</span>
                    <span className={s.findings_count > 0 ? 'text-tertiary font-bold' : 'text-secondary'}>
                      {s.findings_count} vulns
                    </span>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="relative z-10 text-[10px] font-label text-on-surface-variant text-center mt-6 uppercase tracking-wider">
            Click any node to focus scan findings & telemetry
          </div>
        </div>

        {/* Selected Target Details Panel */}
        <div className="lg:col-span-4 bg-surface-container-high/40 border border-outline-variant/40 rounded-md p-5 flex flex-col justify-between">
          <div>
            <h3 className="font-headline text-sm font-bold text-on-background mb-4 uppercase tracking-wide flex items-center gap-2">
              <Server className="w-4 h-4 text-secondary" /> Node Inspector
            </h3>

            {selectedScan ? (
              <div className="space-y-4 font-label text-xs">
                <div className="p-3 bg-surface-container border border-outline-variant/40 rounded-md">
                  <div className="text-[10px] text-on-surface-variant uppercase">Target Host</div>
                  <div className="font-bold text-sm text-primary mt-0.5">{selectedScan.target}</div>
                  <div className="text-[10px] text-on-surface-variant mt-1">
                    Status: <span className="text-secondary font-bold uppercase">{selectedScan.status}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="text-[10px] text-on-surface-variant uppercase font-bold">Services & Ports</div>
                  <div className="bg-surface-container p-3 border border-outline-variant/30 rounded-md space-y-2 max-h-48 overflow-y-auto">
                    {selectedScan.findings.length === 0 ? (
                      <div className="text-on-surface-variant text-[11px]">No open ports or services mapped.</div>
                    ) : (
                      selectedScan.findings.map((f) => (
                        <div key={f.id} className="flex justify-between items-center text-[11px] border-b border-outline-variant/20 pb-1.5 last:border-0 last:pb-0">
                          <div>
                            <span className="font-bold text-on-background">{f.host}</span>
                            {f.port && <span className="text-secondary ml-1">:{f.port}</span>}
                          </div>
                          <span className={`px-1.5 py-0.5 rounded text-[9px] uppercase font-bold ${
                            f.severity === 'critical' ? 'bg-error-container text-error' : 'bg-surface-container-high text-on-surface-variant'
                          }`}>
                            {f.severity}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {selectedScan.recon_summary && (
                  <div className="p-3 bg-secondary/10 border border-secondary/25 rounded-md text-[11px]">
                    <span className="font-bold text-secondary">Fingerprint:</span> {selectedScan.recon_summary}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-on-surface-variant text-xs font-label py-12">
                Select a target node on the left to inspect topology details.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
