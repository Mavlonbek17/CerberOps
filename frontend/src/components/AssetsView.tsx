import { useState, useEffect } from 'react';
import { Boxes, Globe, Server, Clock, ChevronRight, ArrowLeft } from 'lucide-react';
import { listAssets, getAsset } from '../api/client';
import type { AssetSummary, AssetDetail } from '../types';

function relTime(iso: string): string {
  const d = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (d < 60) return 'just now';
  const m = Math.floor(d / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  return h < 24 ? `${h}h ago` : `${Math.floor(h / 24)}d ago`;
}

export default function AssetsView() {
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<AssetDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    listAssets().then(setAssets).catch(console.error).finally(() => setLoading(false));
  }, []);

  const openAsset = async (id: string) => {
    setDetailLoading(true);
    try {
      const detail = await getAsset(id);
      setSelected(detail);
    } catch (e) {
      console.error(e);
    } finally {
      setDetailLoading(false);
    }
  };

  if (selected) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => setSelected(null)}
          className="flex items-center gap-2 text-[13px] font-medium text-on-surface-variant hover:text-on-background cursor-pointer transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Assets
        </button>

        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-[20px] font-bold text-on-background">{selected.target}</h2>
            <p className="text-[13px] text-on-surface-variant mt-1">
              Tracked since {new Date(selected.first_seen).toLocaleDateString()} · {selected.scan_count} scan(s)
            </p>
          </div>
        </div>

        {/* Tech stack */}
        <div className="bg-surface-container border border-outline-variant rounded-xl p-5">
          <h3 className="text-[14px] font-semibold text-on-background mb-3">Technology Stack</h3>
          {selected.tech_stack.length === 0 ? (
            <p className="text-[13px] text-on-surface-variant">No technologies fingerprinted yet.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {selected.tech_stack.map(t => (
                <span key={t} className="px-3 py-1.5 bg-[#4493f8]/10 border border-[#4493f8]/25 text-[#4493f8] text-[12px] font-medium rounded-lg">{t}</span>
              ))}
            </div>
          )}
        </div>

        {/* Open ports */}
        {selected.open_ports.length > 0 && (
          <div className="bg-surface-container border border-outline-variant rounded-xl p-5">
            <h3 className="text-[14px] font-semibold text-on-background mb-3">Open Ports</h3>
            <div className="flex flex-wrap gap-2">
              {selected.open_ports.map(p => (
                <span key={p} className="px-3 py-1.5 bg-surface-container-highest border border-outline-variant text-on-surface-variant text-[12px] font-mono font-medium rounded-lg">{p}</span>
              ))}
            </div>
          </div>
        )}

        {/* Subdomains */}
        <div className="bg-surface-container border border-outline-variant rounded-xl overflow-hidden">
          <div className="px-5 py-3.5 border-b border-outline-variant flex items-center justify-between">
            <h3 className="text-[14px] font-semibold text-on-background">Subdomains ({selected.subdomains.length})</h3>
          </div>
          {selected.subdomains.length === 0 ? (
            <div className="px-5 py-10 text-center text-[13px] text-on-surface-variant">No subdomains discovered yet.</div>
          ) : (
            <div className="divide-y divide-outline-variant/60">
              {selected.subdomains.map(s => (
                <div key={s.subdomain} className="flex items-center gap-3 px-5 py-3 text-[13px]">
                  <span className={`w-2 h-2 rounded-full shrink-0 ${s.is_alive ? 'bg-[#3fb950]' : 'bg-outline-variant'}`} />
                  <span className="font-mono font-medium text-on-background flex-1 min-w-0 truncate">{s.subdomain}</span>
                  {s.status_code && (
                    <span className={`text-[11px] font-mono px-1.5 py-0.5 rounded ${s.status_code < 400 ? 'text-[#3fb950]' : 'text-[#f85149]'}`}>{s.status_code}</span>
                  )}
                  {s.title && <span className="text-on-surface-variant text-[12px] truncate max-w-[200px]">{s.title}</span>}
                  <div className="flex gap-1 shrink-0">
                    {s.tech.slice(0, 3).map(t => (
                      <span key={t} className="text-[10px] px-1.5 py-0.5 bg-surface-container-highest text-on-surface-variant rounded">{t}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-[20px] font-bold text-on-background">Asset Inventory</h2>
        <p className="text-[13px] text-on-surface-variant mt-1">Targets, discovered subdomains, and fingerprinted technology stacks — built automatically as you scan.</p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-on-surface-variant text-[13px]">Loading…</div>
      ) : assets.length === 0 ? (
        <div className="bg-surface-container border border-outline-variant rounded-xl py-16 text-center">
          <Boxes className="w-10 h-10 text-outline mx-auto mb-3" />
          <p className="text-[14px] font-medium text-on-background">No assets tracked yet</p>
          <p className="text-[13px] text-on-surface-variant mt-1">Run a scan to start building your asset inventory.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {assets.map(a => (
            <button
              key={a.id}
              onClick={() => openAsset(a.id)}
              disabled={detailLoading}
              className="text-left bg-surface-container border border-outline-variant rounded-xl p-5 hover:border-outline transition-colors cursor-pointer disabled:opacity-50"
            >
              <div className="flex items-center justify-between mb-3">
                <Globe className="w-5 h-5 text-[#4493f8]" />
                <ChevronRight className="w-4 h-4 text-on-surface-variant" />
              </div>
              <div className="text-[14px] font-semibold text-on-background truncate">{a.target}</div>
              <div className="flex items-center gap-3 mt-2 text-[12px] text-on-surface-variant">
                <span className="flex items-center gap-1"><Server className="w-3 h-3" /> {a.subdomain_count} subdomains</span>
                <span className="flex items-center gap-1"><Clock className="w-3 h-3" /> {relTime(a.last_scanned)}</span>
              </div>
              {a.tech_stack.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {a.tech_stack.slice(0, 4).map(t => (
                    <span key={t} className="text-[10px] px-1.5 py-0.5 bg-surface-container-highest text-on-surface-variant rounded">{t}</span>
                  ))}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
