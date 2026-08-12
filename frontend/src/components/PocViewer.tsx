import { useState } from 'react';
import { Terminal, Loader2, Copy, Check, RefreshCw, AlertTriangle } from 'lucide-react';
import { generatePoc } from '../api/client';
import type { PocResult } from '../types';

interface Props {
  findingId: string;
  hasPoc: boolean;
}

export default function PocViewer({ findingId, hasPoc }: Props) {
  const [poc, setPoc] = useState<PocResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [open, setOpen] = useState(false);

  const load = async (regenerate: boolean) => {
    setLoading(true);
    setError(null);
    try {
      const result = await generatePoc(findingId, regenerate);
      setPoc(result);
      setOpen(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to generate PoC');
    } finally {
      setLoading(false);
    }
  };

  const copy = () => {
    if (!poc) return;
    navigator.clipboard.writeText(poc.poc_code);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  if (!open) {
    return (
      <button
        onClick={() => load(false)}
        disabled={loading}
        className="flex items-center gap-1.5 text-xs font-label px-3 py-1.5 rounded bg-primary/12 text-primary border border-primary/30 hover:bg-primary/18 transition-colors font-semibold cursor-pointer disabled:opacity-50 uppercase tracking-wide"
      >
        {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Terminal className="w-3.5 h-3.5" />}
        {loading ? 'Generating PoC...' : hasPoc ? 'View PoC' : 'Generate PoC'}
      </button>
    );
  }

  return (
    <div className="mt-3 bg-surface-container border border-primary/25 rounded-md overflow-hidden">
      <div className="px-4 py-2.5 border-b border-outline-variant/55 bg-primary/10 flex items-center justify-between">
        <span className="text-xs font-bold text-primary uppercase tracking-wider flex items-center gap-1.5 font-label">
          <Terminal className="w-3.5 h-3.5" /> Verification Script
        </span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => load(true)}
            disabled={loading}
            title="Regenerate"
            className="p-1.5 rounded-md hover:bg-surface-container-high text-on-surface-variant hover:text-on-background transition-colors cursor-pointer"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={copy}
            title="Copy"
            className="p-1.5 rounded-md hover:bg-surface-container-high text-on-surface-variant hover:text-on-background transition-colors cursor-pointer"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 text-sm text-on-error-container flex items-center gap-2 bg-error-container/65">
          <AlertTriangle className="w-4 h-4 shrink-0" /> {error}
        </div>
      )}

      {poc && (
        <>
          <pre className="p-4 text-xs font-mono text-on-surface-variant overflow-x-auto whitespace-pre leading-relaxed">
            {poc.poc_code}
          </pre>
          <div className="px-4 py-3 border-t border-outline-variant/55 bg-surface-container-high/35 text-xs text-on-surface-variant leading-relaxed">
            <span className="font-semibold text-on-background">AI explanation ({poc.ai_model_used}):</span> {poc.poc_explanation}
          </div>
        </>
      )}
    </div>
  );
}
