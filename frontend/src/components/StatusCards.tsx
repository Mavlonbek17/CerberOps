import { Scan, AlertTriangle, Shield, Brain } from 'lucide-react';
import type { HealthCheck } from '../types';

interface Props {
  health: HealthCheck | null;
  totalScans: number;
  totalFindings: number;
}

export default function StatusCards({ health, totalScans, totalFindings }: Props) {
  const scannerCount = health ? Object.values(health.scanners).filter(Boolean).length : 0;

  const cards = [
    {
      icon: Scan,
      label: 'Total Scans',
      value: totalScans,
      color: 'text-blue-400',
      bg: 'bg-blue-500/10',
    },
    {
      icon: AlertTriangle,
      label: 'Findings',
      value: totalFindings,
      color: 'text-orange-400',
      bg: 'bg-orange-500/10',
    },
    {
      icon: Shield,
      label: 'Scanners',
      value: `${scannerCount}/3`,
      color: 'text-green-400',
      bg: 'bg-green-500/10',
    },
    {
      icon: Brain,
      label: 'AI Engine',
      value: health?.ollama_available ? 'Online' : 'Offline',
      color: health?.ollama_available ? 'text-purple-400' : 'text-gray-400',
      bg: health?.ollama_available ? 'bg-purple-500/10' : 'bg-gray-500/10',
    },
  ];

  return (
    <div className="grid grid-cols-4 gap-4">
      {cards.map(({ icon: Icon, label, value, color, bg }) => (
        <div
          key={label}
          className="bg-[var(--bg-card)] rounded-lg border border-[var(--border)] p-4"
        >
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg ${bg}`}>
              <Icon className={`w-5 h-5 ${color}`} />
            </div>
            <div>
              <div className="text-2xl font-bold">{value}</div>
              <div className="text-xs text-[var(--text-secondary)]">{label}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
