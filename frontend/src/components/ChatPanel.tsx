import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Loader2, Sparkles, MessageSquare, CheckCircle2, Clock, XCircle, RotateCw, ChevronRight } from 'lucide-react';
import { chatWithScan } from '../api/client';
import type { ChatMessage, ScanSummary } from '../types';

interface Props {
  jobId?: string;
  target?: string;
  scans?: ScanSummary[];
}

const SUGGESTIONS = [
  'What is the most urgent vulnerability to fix first?',
  'Are there any exposed databases or unauthenticated ports?',
  'Generate an executive summary for my management team.',
  'Which findings are confirmed vs. likely false positives?',
];

const STATUS_ICON: Record<string, { icon: typeof Clock; color: string }> = {
  completed: { icon: CheckCircle2, color: 'text-secondary' },
  running:   { icon: RotateCw,     color: 'text-primary' },
  failed:    { icon: XCircle,      color: 'text-error' },
  cancelled: { icon: XCircle,      color: 'text-on-surface-variant' },
  queued:    { icon: Clock,        color: 'text-tertiary' },
  parsing:   { icon: RotateCw,     color: 'text-primary' },
  analyzing: { icon: RotateCw,     color: 'text-primary' },
};

function ChatArea({ jobId, target }: { jobId: string; target: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { setMessages([]); setInput(''); setError(null); }, [jobId]);
  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages, sending]);

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || sending) return;
    const next: ChatMessage[] = [...messages, { role: 'user', content: trimmed }];
    setMessages(next);
    setInput('');
    setSending(true);
    setError(null);
    try {
      const result = await chatWithScan(jobId, trimmed, messages);
      setMessages([...next, { role: 'assistant', content: result.response }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Chat failed');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex flex-col h-full min-h-0">
      {/* Context bar */}
      <div className="px-5 py-2.5 border-b border-outline-variant shrink-0 flex items-center gap-2 text-[12px]">
        <span className="text-on-surface-variant">Context:</span>
        <span className="font-mono font-medium text-primary bg-primary/8 border border-primary/20 px-2 py-0.5 rounded truncate max-w-[360px]">{target}</span>
        <span className="ml-auto text-secondary font-medium">Local AI</span>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-5 space-y-4 min-h-0">
        {messages.length === 0 && (
          <div className="max-w-lg mx-auto text-center py-10 space-y-4">
            <Sparkles className="w-10 h-10 text-primary mx-auto" />
            <h3 className="text-[16px] font-semibold text-on-background">Ask about this scan</h3>
            <p className="text-[13px] text-on-surface-variant">Data stays local — Ollama processes everything on your machine.</p>
            <div className="space-y-2 text-left">
              {SUGGESTIONS.map((s) => (
                <button key={s} onClick={() => send(s)} className="w-full text-left text-[13px] px-4 py-3 rounded-lg bg-surface-container border border-outline-variant text-on-surface-variant hover:border-outline hover:text-on-background transition-colors cursor-pointer">
                  "{s}"
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {m.role === 'assistant' && (
              <div className="w-7 h-7 rounded-lg bg-secondary/12 border border-secondary/25 text-secondary flex items-center justify-center shrink-0 mt-0.5">
                <Bot className="w-4 h-4" />
              </div>
            )}
            <div className={`max-w-[80%] rounded-xl px-4 py-3 text-[13px] leading-relaxed whitespace-pre-wrap ${
              m.role === 'user'
                ? 'bg-primary/10 border border-primary/20 text-on-background'
                : 'bg-surface-container border border-outline-variant text-on-surface-variant'
            }`}>
              {m.content}
            </div>
            {m.role === 'user' && (
              <div className="w-7 h-7 rounded-lg bg-primary/12 border border-primary/20 text-primary flex items-center justify-center shrink-0 mt-0.5">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {sending && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-lg bg-secondary/12 border border-secondary/25 text-secondary flex items-center justify-center shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="bg-surface-container border border-outline-variant rounded-xl px-4 py-3 text-[13px] text-on-surface-variant flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-primary" /> Analyzing…
            </div>
          </div>
        )}

        {error && <div className="text-[13px] text-error bg-error/8 border border-error/25 rounded-lg px-4 py-3">{error}</div>}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form onSubmit={(e) => { e.preventDefault(); send(input); }} className="flex items-center gap-3 px-5 py-3.5 border-t border-outline-variant shrink-0">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question…"
          disabled={sending}
          className="flex-1 px-4 py-3 bg-surface-container-low border border-outline-variant rounded-xl text-[14px] text-on-background focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all placeholder:text-on-surface-variant/60 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={sending || !input.trim()}
          className="flex items-center gap-2 bg-primary text-on-primary font-semibold px-5 py-3 rounded-xl cursor-pointer hover:brightness-110 transition-all disabled:opacity-40 disabled:cursor-not-allowed shrink-0 text-[14px]"
        >
          <Send className="w-4 h-4" /> Send
        </button>
      </form>
    </div>
  );
}

export default function ChatPanel({ jobId, target, scans }: Props) {
  const [selectedScanId, setSelectedScanId] = useState<string | null>(null);

  if (jobId && target) {
    return <div className="flex flex-col h-full"><ChatArea jobId={jobId} target={target} /></div>;
  }

  const allScans = scans ?? [];
  const completedScans = allScans.filter((s) => s.status === 'completed');
  const activeScan = selectedScanId ? allScans.find((s) => s.id === selectedScanId) : completedScans[0] ?? null;
  const activeId = activeScan?.id ?? null;

  return (
    <div className="flex h-full bg-surface-container border border-outline-variant rounded-xl overflow-hidden">

      {/* Scan selector sidebar */}
      <div className="w-72 shrink-0 border-r border-outline-variant flex flex-col bg-surface-container-low">
        <div className="px-4 py-4 border-b border-outline-variant">
          <h3 className="text-[14px] font-semibold text-on-background flex items-center gap-2">
            <MessageSquare className="w-4 h-4 text-primary" /> AI Chat
          </h3>
          <p className="text-[12px] text-on-surface-variant mt-1">Select a completed scan to chat about.</p>
        </div>

        <div className="flex-1 overflow-y-auto py-2 px-2 space-y-0.5">
          {allScans.length === 0 && (
            <div className="py-10 text-center text-[13px] text-on-surface-variant px-4">No scans yet.</div>
          )}
          {allScans.map((s) => {
            const st = STATUS_ICON[s.status] ?? STATUS_ICON['cancelled'];
            const Icon = st.icon;
            const sel = activeId === s.id;
            const ready = s.status === 'completed';
            return (
              <button
                key={s.id}
                onClick={() => ready && setSelectedScanId(s.id)}
                disabled={!ready}
                className={`w-full text-left px-3 py-2.5 rounded-lg transition-colors cursor-pointer text-[13px] ${
                  sel ? 'bg-primary/10 text-on-background' : ready ? 'hover:bg-surface-container text-on-surface-variant hover:text-on-background' : 'opacity-40 cursor-not-allowed text-on-surface-variant'
                }`}
              >
                <div className="flex items-center gap-2">
                  <Icon className={`w-3 h-3 shrink-0 ${st.color} ${['running','parsing','analyzing'].includes(s.status) ? 'animate-spin' : ''}`} />
                  <span className="truncate flex-1 min-w-0 font-medium">{s.target.replace(/^https?:\/\//, '').replace(/\/$/, '')}</span>
                  {sel && <ChevronRight className="w-3 h-3 text-primary shrink-0" />}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Chat area */}
      <div className="flex-1 min-w-0 flex flex-col">
        {activeId && activeScan ? (
          <ChatArea key={activeId} jobId={activeId} target={activeScan.target} />
        ) : (
          <div className="flex flex-col items-center justify-center gap-4 h-full py-16 text-center px-8">
            <Sparkles className="w-10 h-10 text-primary" />
            <h3 className="text-[16px] font-semibold text-on-background">Select a scan</h3>
            <p className="text-[13px] text-on-surface-variant max-w-sm">
              {allScans.length === 0 ? 'No scans yet — launch one from the Dashboard.' : 'Pick a completed scan from the left panel to start chatting.'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
