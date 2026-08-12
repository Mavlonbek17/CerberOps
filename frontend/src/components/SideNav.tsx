import {
  LayoutDashboard,
  Radar,
  MessageSquare,
  History,
  Network,
  Settings,
  HelpCircle,
  Terminal,
  Plus,
  CalendarClock,
  Boxes,
} from 'lucide-react';

export type NavView =
  | 'dashboard'
  | 'live_scans'
  | 'ai_chat'
  | 'scan_history'
  | 'network_map'
  | 'assets'
  | 'scheduler'
  | 'settings'
  | 'logs'
  | 'support';

interface Props {
  currentView: NavView;
  onViewChange: (view: NavView) => void;
  onNewScan: () => void;
}

const MAIN_ITEMS: {
  label: string;
  view: NavView;
  icon: typeof LayoutDashboard;
  activeColor: string;
  activeBg: string;
  activeDot: string;
}[] = [
  { label: 'Dashboard',    view: 'dashboard',    icon: LayoutDashboard, activeColor: 'text-[#4493f8]', activeBg: 'bg-[#4493f8]/12', activeDot: 'bg-[#4493f8]' },
  { label: 'Live Scans',   view: 'live_scans',   icon: Radar,           activeColor: 'text-[#3fb950]', activeBg: 'bg-[#3fb950]/12', activeDot: 'bg-[#3fb950]' },
  { label: 'AI Chat',      view: 'ai_chat',      icon: MessageSquare,   activeColor: 'text-[#bc8cff]', activeBg: 'bg-[#bc8cff]/12', activeDot: 'bg-[#bc8cff]' },
  { label: 'Scan History', view: 'scan_history', icon: History,         activeColor: 'text-[#d29922]', activeBg: 'bg-[#d29922]/12', activeDot: 'bg-[#d29922]' },
  { label: 'Network Map',  view: 'network_map',  icon: Network,         activeColor: 'text-[#4493f8]', activeBg: 'bg-[#4493f8]/12', activeDot: 'bg-[#4493f8]' },
  { label: 'Assets',       view: 'assets',       icon: Boxes,           activeColor: 'text-[#d29922]', activeBg: 'bg-[#d29922]/12', activeDot: 'bg-[#d29922]' },
  { label: 'Scheduler',    view: 'scheduler',    icon: CalendarClock,   activeColor: 'text-[#3fb950]', activeBg: 'bg-[#3fb950]/12', activeDot: 'bg-[#3fb950]' },
];

const FOOTER_ITEMS: { label: string; view: NavView; icon: typeof HelpCircle }[] = [
  { label: 'Settings', view: 'settings', icon: Settings },
  { label: 'Logs',     view: 'logs',     icon: Terminal },
  { label: 'Support',  view: 'support',  icon: HelpCircle },
];

export default function SideNav({ currentView, onViewChange, onNewScan }: Props) {
  return (
    <aside
      className="flex flex-col shrink-0 h-full bg-surface-container-low border-r border-outline-variant"
      style={{ width: '248px', minWidth: '248px' }}
    >
      {/* New Scan CTA */}
      <div className="px-5 pt-6 pb-5 flex justify-center">
        <button
          onClick={onNewScan}
          className="flex items-center gap-2.5 bg-primary text-on-primary font-semibold px-6 py-2.5 rounded-xl text-[14px] cursor-pointer hover:brightness-110 transition-all shadow-sm"
        >
          <Plus className="w-4 h-4" strokeWidth={2.5} />
          New Scan
        </button>
      </div>

      {/* Section label */}
      <div className="px-5 pb-2">
        <span className="text-[11px] font-bold text-on-surface-variant/60 uppercase tracking-widest">Menu</span>
      </div>

      {/* Main nav */}
      <nav className="flex-1 overflow-y-auto px-3 flex flex-col gap-1">
        {MAIN_ITEMS.map(({ label, view, icon: Icon, activeColor, activeBg, activeDot }) => {
          const active = currentView === view;
          return (
            <button
              key={view}
              onClick={() => onViewChange(view)}
              className={`w-full flex items-center gap-3.5 px-4 py-3.5 rounded-xl text-[14px] font-medium transition-all text-left cursor-pointer group ${
                active
                  ? `${activeBg} ${activeColor}`
                  : 'text-on-surface-variant hover:text-on-background hover:bg-surface-container-high/50'
              }`}
            >
              <Icon
                className={`w-5 h-5 shrink-0 transition-colors ${active ? activeColor : 'text-on-surface-variant group-hover:text-on-background'}`}
                strokeWidth={active ? 2.2 : 1.8}
              />
              <span className="flex-1">{label}</span>
              {active && <span className={`w-2 h-2 rounded-full shrink-0 ${activeDot}`} />}
            </button>
          );
        })}
      </nav>

      {/* Footer nav */}
      <div className="border-t border-outline-variant px-3 pt-4 pb-4 flex flex-col gap-1">
        <div className="px-2 pb-2">
          <span className="text-[11px] font-bold text-on-surface-variant/60 uppercase tracking-widest">System</span>
        </div>
        {FOOTER_ITEMS.map(({ label, view, icon: Icon }) => {
          const active = currentView === view;
          return (
            <button
              key={view}
              onClick={() => onViewChange(view)}
              className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-xl text-[14px] font-medium transition-all text-left cursor-pointer group ${
                active
                  ? 'bg-primary/12 text-primary'
                  : 'text-on-surface-variant hover:text-on-background hover:bg-surface-container-high/50'
              }`}
            >
              <Icon
                className={`w-5 h-5 shrink-0 ${active ? 'text-primary' : 'text-on-surface-variant group-hover:text-on-background'}`}
                strokeWidth={1.8}
              />
              {label}
            </button>
          );
        })}
      </div>
    </aside>
  );
}
