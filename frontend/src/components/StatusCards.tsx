import { RotateCw, AlertTriangle, Globe, Brain, Database, Wifi } from 'lucide-react';
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
      icon: RotateCw,
      value: String(totalScans),
      label: 'Scans',
      sub: 'total',
      iconColor: 'text-[#4493f8]',
      iconBg: 'bg-[#4493f8]/12',
      valuColor: 'text-[#4493f8]',
      border: 'border-[#4493f8]/20',
    },
    {
      icon: AlertTriangle,
      value: String(totalFindings),
      label: 'Findings',
      sub: totalFindings > 0 ? 'require review' : 'all clear',
      iconColor: totalFindings > 0 ? 'text-[#d29922]' : 'text-on-surface-variant',
      iconBg: totalFindings > 0 ? 'bg-[#d29922]/12' : 'bg-surface-container-high',
      valuColor: totalFindings > 0 ? 'text-[#d29922]' : 'text-on-surface-variant',
      border: totalFindings > 0 ? 'border-[#d29922]/20' : 'border-outline-variant',
    },
    {
      icon: Globe,
      value: `${scannerCount}/3`,
      label: 'Scanners',
      sub: 'active',
      iconColor: 'text-[#3fb950]',
      iconBg: 'bg-[#3fb950]/12',
      valuColor: 'text-[#3fb950]',
      border: 'border-[#3fb950]/20',
    },
    {
      icon: Brain,
      value: health?.ollama_available ? 'Online' : 'Offline',
      label: 'AI Engine',
      sub: 'Ollama',
      iconColor: health?.ollama_available ? 'text-[#bc8cff]' : 'text-on-surface-variant',
      iconBg: health?.ollama_available ? 'bg-[#bc8cff]/12' : 'bg-surface-container-high',
      valuColor: health?.ollama_available ? 'text-[#bc8cff]' : 'text-on-surface-variant',
      border: health?.ollama_available ? 'border-[#bc8cff]/20' : 'border-outline-variant',
    },
    {
      icon: Database,
      value: health?.database ? 'OK' : 'Down',
      label: 'Database',
      sub: 'PostgreSQL',
      iconColor: health?.database ? 'text-[#3fb950]' : 'text-[#f85149]',
      iconBg: health?.database ? 'bg-[#3fb950]/12' : 'bg-[#f85149]/12',
      valuColor: health?.database ? 'text-[#3fb950]' : 'text-[#f85149]',
      border: health?.database ? 'border-[#3fb950]/20' : 'border-[#f85149]/20',
    },
    {
      icon: Wifi,
      value: health ? 'Healthy' : '…',
      label: 'API',
      sub: 'backend',
      iconColor: health ? 'text-[#3fb950]' : 'text-[#d29922]',
      iconBg: health ? 'bg-[#3fb950]/12' : 'bg-[#d29922]/12',
      valuColor: health ? 'text-[#3fb950]' : 'text-[#d29922]',
      border: health ? 'border-[#3fb950]/20' : 'border-[#d29922]/20',
    },
  ];

  return (
    <div className="grid grid-cols-3 lg:grid-cols-6 gap-3">
      {cards.map(({ icon: Icon, value, label, sub, iconColor, iconBg, valuColor, border }) => (
        <div
          key={label}
          className={`bg-surface-container border ${border} rounded-xl px-4 py-4 flex flex-col gap-3`}
        >
          {/* Icon */}
          <div className={`w-9 h-9 rounded-lg ${iconBg} flex items-center justify-center`}>
            <Icon className={`w-4.5 h-4.5 ${iconColor}`} strokeWidth={1.8} />
          </div>
          {/* Value + label */}
          <div>
            <div className={`text-xl font-bold leading-tight ${valuColor}`}>{value}</div>
            <div className="text-[13px] font-medium text-on-background mt-0.5">{label}</div>
            <div className="text-[11px] text-on-surface-variant">{sub}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
