import { useState } from 'react';
import {
  Key,
  Cpu,
  ShieldCheck,
  Save,
  Check,
  Eye,
  EyeOff,
  Zap,
  AlertTriangle,
} from 'lucide-react';
import type { HealthCheck } from '../types';

interface Props {
  health: HealthCheck | null;
}

const MODELS = [
  { value: 'qwen2.5-coder:latest', label: 'qwen2.5-coder', tag: 'Recommended' },
  { value: 'llama3.2:latest',      label: 'llama3.2',       tag: 'General'     },
  { value: 'deepseek-coder:6.7b',  label: 'deepseek-coder', tag: 'Lightweight' },
  { value: 'mistral:latest',       label: 'mistral',        tag: 'Fast'        },
];

export default function SettingsView({ health }: Props) {
  const [apiKey, setApiKey]         = useState(localStorage.getItem('cerberops_api_key') || '');
  const [showKey, setShowKey]       = useState(false);
  const [ollamaUrl, setOllamaUrl]   = useState('http://localhost:11434');
  const [model, setModel]           = useState('qwen2.5-coder:latest');
  const [smartRecon, setSmartRecon] = useState(true);
  const [fpFilter, setFpFilter]     = useState(true);
  const [saved, setSaved]           = useState(false);

  const ollamaOk = health?.ollama_available ?? false;

  const save = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('cerberops_api_key', apiKey.trim());
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="max-w-2xl space-y-8">

      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-[20px] font-bold text-on-background">Settings</h2>
          <p className="text-[13px] text-on-surface-variant mt-1">Configure API keys, local AI engine, and scanner defaults.</p>
        </div>
        <button
          form="settings-form"
          type="submit"
          className={`flex items-center gap-2 font-semibold text-[14px] px-5 py-2.5 rounded-xl cursor-pointer transition-all ${
            saved
              ? 'bg-[#3fb950] text-white'
              : 'bg-primary text-on-primary hover:brightness-110'
          }`}
        >
          {saved ? <Check className="w-4 h-4" /> : <Save className="w-4 h-4" />}
          {saved ? 'Saved!' : 'Save changes'}
        </button>
      </div>

      <form id="settings-form" onSubmit={save} className="space-y-6">

        {/* ── API Key ── */}
        <div className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
          <div className="flex items-center gap-3 px-5 py-4 border-b border-outline-variant">
            <div className="w-8 h-8 rounded-lg bg-primary/12 flex items-center justify-center shrink-0">
              <Key className="w-4 h-4 text-primary" />
            </div>
            <div>
              <h3 className="text-[14px] font-semibold text-on-background">API Key</h3>
              <p className="text-[12px] text-on-surface-variant mt-0.5">
                Sent as <code className="font-mono bg-surface-container-high px-1 py-0.5 rounded text-[11px]">X-API-Key</code> header. Leave blank for local mode.
              </p>
            </div>
          </div>
          <div className="px-5 py-4">
            <div className="relative">
              <input
                type={showKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="sk-…"
                className="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3.5 pr-12 text-[14px] text-on-background font-mono focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all placeholder:text-on-surface-variant/50"
              />
              <button
                type="button"
                onClick={() => setShowKey((v) => !v)}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-background cursor-pointer p-1 rounded transition-colors"
              >
                {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </div>

        {/* ── Local AI (Ollama) ── */}
        <div className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
          <div className="flex items-center gap-3 px-5 py-4 border-b border-outline-variant">
            <div className="w-8 h-8 rounded-lg bg-[#bc8cff]/12 flex items-center justify-center shrink-0">
              <Cpu className="w-4 h-4 text-[#bc8cff]" />
            </div>
            <div>
              <h3 className="text-[14px] font-semibold text-on-background">Local AI (Ollama)</h3>
              <p className="text-[12px] text-on-surface-variant mt-0.5">Runs entirely on your machine — no data leaves your network.</p>
            </div>
            {/* Status badge */}
            <div className={`ml-auto flex items-center gap-2 px-3 py-1.5 rounded-lg text-[12px] font-medium ${
              ollamaOk ? 'bg-[#3fb950]/12 text-[#3fb950]' : 'bg-[#f85149]/12 text-[#f85149]'
            }`}>
              <span className={`w-2 h-2 rounded-full ${ollamaOk ? 'bg-[#3fb950]' : 'bg-[#f85149]'}`} />
              {ollamaOk ? 'Connected' : 'Offline'}
            </div>
          </div>

          <div className="px-5 py-5 space-y-5">
            {/* Base URL */}
            <div className="space-y-1.5">
              <label className="text-[13px] font-medium text-on-surface-variant">Base URL</label>
              <input
                type="text"
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant rounded-xl px-4 py-3.5 text-[14px] text-on-background font-mono focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all"
              />
            </div>

            {/* Model selector */}
            <div className="space-y-2">
              <label className="text-[13px] font-medium text-on-surface-variant">Model</label>
              <div className="grid grid-cols-2 gap-2.5">
                {MODELS.map((m) => {
                  const active = model === m.value;
                  return (
                    <button
                      key={m.value}
                      type="button"
                      onClick={() => setModel(m.value)}
                      className={`text-left px-4 py-3.5 rounded-xl border text-[13px] transition-all cursor-pointer ${
                        active
                          ? 'bg-primary/10 border-primary/40 text-on-background'
                          : 'bg-surface-container-low border-outline-variant text-on-surface-variant hover:text-on-background hover:border-outline hover:bg-surface-container-high/40'
                      }`}
                    >
                      <div className={`font-semibold ${active ? 'text-primary' : ''}`}>{m.label}</div>
                      <div className="text-[11px] text-on-surface-variant mt-1">{m.tag}</div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* ── Scanner Defaults ── */}
        <div className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
          <div className="flex items-center gap-3 px-5 py-4 border-b border-outline-variant">
            <div className="w-8 h-8 rounded-lg bg-[#3fb950]/12 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-4 h-4 text-[#3fb950]" />
            </div>
            <div>
              <h3 className="text-[14px] font-semibold text-on-background">Scanner Defaults</h3>
              <p className="text-[12px] text-on-surface-variant mt-0.5">Applied automatically when launching new scans.</p>
            </div>
          </div>

          <div className="divide-y divide-outline-variant/60">
            {[
              {
                icon: <Zap className="w-4 h-4 text-[#bc8cff]" />,
                label: 'AI Smart Recon',
                desc: 'Fingerprint the target and let the AI narrow scanner template scope before running.',
                value: smartRecon,
                set: setSmartRecon,
                activeColor: 'bg-[#bc8cff]',
              },
              {
                icon: <ShieldCheck className="w-4 h-4 text-[#3fb950]" />,
                label: 'False Positive Filter',
                desc: 'Automatically triage findings using the local LLM to reduce noise.',
                value: fpFilter,
                set: setFpFilter,
                activeColor: 'bg-[#3fb950]',
              },
            ].map((row) => (
              <div
                key={row.label}
                className="flex items-center gap-4 px-5 py-4 cursor-pointer hover:bg-surface-container-high/30 transition-colors"
                onClick={() => row.set(!row.value)}
              >
                <div className="w-8 h-8 rounded-lg bg-surface-container-high flex items-center justify-center shrink-0">
                  {row.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[14px] font-medium text-on-background">{row.label}</div>
                  <div className="text-[12px] text-on-surface-variant mt-0.5">{row.desc}</div>
                </div>
                {/* Toggle */}
                <div
                  className={`relative w-11 h-6 rounded-full transition-all shrink-0 ${
                    row.value ? row.activeColor : 'bg-surface-container-highest border border-outline-variant'
                  }`}
                >
                  <div className={`absolute top-0.5 w-5 h-5 rounded-full shadow transition-all ${
                    row.value ? 'left-5 bg-white' : 'left-0.5 bg-outline'
                  }`} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Ollama offline warning */}
        {!ollamaOk && (
          <div className="flex items-start gap-3 px-4 py-4 rounded-xl border border-[#d29922]/30 bg-[#d29922]/6">
            <AlertTriangle className="w-4 h-4 text-[#d29922] shrink-0 mt-0.5" />
            <p className="text-[13px] text-on-background leading-relaxed">
              <span className="font-semibold text-[#d29922]">Ollama not detected.</span>{' '}
              AI features require Ollama. Install at{' '}
              <code className="font-mono text-[12px] bg-surface-container-high px-1 py-0.5 rounded">ollama.com</code>{' '}
              then run{' '}
              <code className="font-mono text-[12px] bg-surface-container-high px-1 py-0.5 rounded">ollama serve</code>.
            </p>
          </div>
        )}
      </form>
    </div>
  );
}
