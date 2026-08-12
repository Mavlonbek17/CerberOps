import { Terminal } from 'lucide-react';

export default function LogsView() {
  return (
    <div className="bg-surface-container-low border border-outline-variant/50 rounded-md p-6 space-y-4 flex flex-col h-[600px]">
      <div className="flex items-center justify-between border-b border-outline-variant/40 pb-4">
        <div>
          <h2 className="text-lg font-headline font-bold text-on-background uppercase tracking-wide flex items-center gap-2">
            <Terminal className="w-5 h-5 text-secondary" /> System & Scanner Logs
          </h2>
          <p className="text-xs font-label text-on-surface-variant mt-1">
            Real-time execution telemetry from Nmap, Nuclei, OWASP ZAP, and Celery workers.
          </p>
        </div>
      </div>

      <div className="flex-1 bg-surface-container-lowest border border-outline-variant/60 rounded p-4 font-mono text-xs text-on-surface-variant overflow-y-auto space-y-1">
        <div className="text-secondary">[CERBEROPS] System initialized. API and Celery workers online.</div>
        <div className="text-on-surface-variant">[HEALTH] PostgreSQL connected | Redis connected | Ollama model ready.</div>
        <div>[NMAP] Engine initialized: version 7.95</div>
        <div>[NUCLEI] Engine initialized: version 3.11.1 (templates cached)</div>
        <div className="text-tertiary">[AI_RECON] Smart Recon module ready for pre-scan fingerprinting.</div>
        <div className="text-tertiary">[AI_TRIAGE] Zero-Noise False Positive Filter enabled (low/medium tiers).</div>
        <div className="text-tertiary">[AI_POC] Autonomous PoC Generator ready for High/Critical findings.</div>
      </div>
    </div>
  );
}
