import { ShieldCheck, Activity, Settings } from 'lucide-react';
import type { HealthCheck } from '../types';
import type { NavView } from './SideNav';

interface Props {
  health: HealthCheck | null;
  onViewChange: (view: NavView) => void;
}

export default function Header({ health, onViewChange }: Props) {
  const isHealthy = health?.status === 'healthy';

  return (
    <header className="sticky top-0 z-50 h-16 bg-surface-container-low border-b border-outline-variant flex items-center justify-between px-6 shrink-0">

      {/* Brand */}
      <button
        onClick={() => onViewChange('dashboard')}
        className="flex items-center gap-2.5 cursor-pointer select-none"
      >
        <ShieldCheck className="w-5 h-5 text-primary" />
        <span className="text-lg font-bold text-on-background tracking-tight">
          CerberOps
        </span>
      </button>

      {/* Right */}
      <div className="flex items-center gap-3">
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[13px] font-medium ${
          isHealthy ? 'text-secondary' : 'text-error'
        }`}>
          <span className={`w-2 h-2 rounded-full ${isHealthy ? 'bg-secondary' : 'bg-error'}`} />
          {isHealthy ? 'All systems operational' : 'Degraded'}
        </div>

        <div className="w-px h-5 bg-outline-variant mx-1" />

        <button
          onClick={() => onViewChange('settings')}
          className="flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-surface-container-high transition-colors cursor-pointer text-on-surface-variant hover:text-on-background"
        >
          <Settings className="w-4 h-4" />
        </button>

        <button
          onClick={() => onViewChange('logs')}
          className="flex items-center gap-2 px-2.5 py-2 rounded-lg hover:bg-surface-container-high transition-colors cursor-pointer text-on-surface-variant hover:text-on-background"
        >
          <Activity className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
