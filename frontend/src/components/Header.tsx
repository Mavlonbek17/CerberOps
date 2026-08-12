import { Shield, Activity } from 'lucide-react';
import type { HealthCheck } from '../types';

interface Props {
  health: HealthCheck | null;
}

export default function Header({ health }: Props) {
  return (
    <header className="border-b border-[var(--border)] bg-[var(--bg-secondary)]">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Shield className="w-8 h-8 text-[var(--accent)]" />
          <div>
            <h1 className="text-xl font-bold tracking-tight">CerberOps</h1>
            <p className="text-xs text-[var(--text-secondary)]">
              DevSecOps Vulnerability Orchestrator
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {health && (
            <div className="flex items-center gap-2 text-sm">
              <Activity className="w-4 h-4" />
              <span className="text-[var(--text-secondary)]">v{health.version}</span>
              <span
                className={`inline-block w-2 h-2 rounded-full ${
                  health.status === 'healthy' ? 'bg-[var(--success)]' : 'bg-[var(--critical)]'
                }`}
              />
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
