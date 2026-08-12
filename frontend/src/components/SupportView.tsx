import { HelpCircle, ShieldCheck, Cpu } from 'lucide-react';
import type { HealthCheck } from '../types';

interface Props {
  health: HealthCheck | null;
}

export default function SupportView({ health }: Props) {
  return (
    <div className="bg-surface-container-low border border-outline-variant/50 rounded-md p-6 space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between border-b border-outline-variant/40 pb-4">
        <div>
          <h2 className="text-lg font-headline font-bold text-on-background uppercase tracking-wide flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-secondary" /> Support & System Diagnostics
          </h2>
          <p className="text-xs font-label text-on-surface-variant mt-1">
            System status, local environment diagnostics, and platform documentation.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-label text-xs">
        <div className="bg-surface-container border border-outline-variant/40 rounded-md p-4 space-y-2">
          <div className="font-bold text-on-background flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-secondary" /> Scanner Engine Health
          </div>
          <div className="space-y-1 text-on-surface-variant pt-1">
            <div className="flex justify-between">
              <span>Nmap:</span>
              <span className={health?.scanners?.nmap ? 'text-secondary font-bold' : 'text-error'}>
                {health?.scanners?.nmap ? 'Available' : 'Missing'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Nuclei:</span>
              <span className={health?.scanners?.nuclei ? 'text-secondary font-bold' : 'text-error'}>
                {health?.scanners?.nuclei ? 'Available' : 'Missing'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>OWASP ZAP Daemon:</span>
              <span className={health?.scanners?.zap ? 'text-secondary font-bold' : 'text-on-surface-variant'}>
                {health?.scanners?.zap ? 'Online' : 'Stopped (Docker)'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-surface-container border border-outline-variant/40 rounded-md p-4 space-y-2">
          <div className="font-bold text-on-background flex items-center gap-2">
            <Cpu className="w-4 h-4 text-primary" /> AI & Database Connectivity
          </div>
          <div className="space-y-1 text-on-surface-variant pt-1">
            <div className="flex justify-between">
              <span>Ollama Engine:</span>
              <span className={health?.ollama_available ? 'text-secondary font-bold' : 'text-error'}>
                {health?.ollama_available ? 'Online (11434)' : 'Offline'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>PostgreSQL:</span>
              <span className={health?.database ? 'text-secondary font-bold' : 'text-error'}>
                {health?.database ? 'Connected' : 'Offline'}
              </span>
            </div>
            <div className="flex justify-between">
              <span>Platform Version:</span>
              <span className="text-on-background font-bold">{health?.version || '0.1.0'}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
