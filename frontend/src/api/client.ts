import type {
  AssetDetail,
  AssetSummary,
  BaselineResult,
  ChatMessage,
  ComplianceResult,
  CveInfo,
  HealthCheck,
  MitreResult,
  NotificationConfig,
  PocResult,
  Report,
  ScanCreated,
  ScanDetail,
  ScanSummary,
  ScheduledScan,
  VerifyResult,
} from '../types';

const BASE = '/api/v1';

function headers(): Record<string, string> {
  const key = localStorage.getItem('cerberops_api_key') || '';
  const h: Record<string, string> = { 'Content-Type': 'application/json' };
  if (key) h['X-API-Key'] = key;
  return h;
}

export async function healthCheck(): Promise<HealthCheck> {
  const r = await fetch(`${BASE}/health`);
  return r.json();
}

export async function startScan(
  target: string,
  scanners: string[] = ['nmap', 'nuclei', 'zap'],
  allowInternal = false,
  smartRecon = true,
  tags: string[] = []
): Promise<ScanCreated> {
  const r = await fetch(`${BASE}/scan`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({
      target,
      scanners,
      allow_internal: allowInternal,
      smart_recon: smartRecon,
      tags,
    }),
  });
  if (!r.ok) {
    const err = await r.json();
    throw new Error(err.detail || 'Failed to start scan');
  }
  return r.json();
}

export async function listScans(limit = 50): Promise<ScanSummary[]> {
  const r = await fetch(`${BASE}/scan?limit=${limit}`, { headers: headers() });
  return r.json();
}

export async function getScan(jobId: string): Promise<ScanDetail> {
  const r = await fetch(`${BASE}/scan/${jobId}`, { headers: headers() });
  if (!r.ok) throw new Error('Scan not found');
  return r.json();
}

export async function getReport(jobId: string): Promise<Report> {
  const r = await fetch(`${BASE}/report/${jobId}`, { headers: headers() });
  if (!r.ok) {
    const err = await r.json();
    throw new Error(err.detail || 'Report not available');
  }
  return r.json();
}

export async function deleteScan(jobId: string): Promise<void> {
  await fetch(`${BASE}/scan/${jobId}`, { method: 'DELETE', headers: headers() });
}

export async function generatePoc(findingId: string, regenerate = false): Promise<PocResult> {
  const r = await fetch(`${BASE}/findings/${findingId}/poc?regenerate=${regenerate}`, {
    method: 'POST',
    headers: headers(),
  });
  if (!r.ok) {
    const err = await r.json();
    throw new Error(err.detail || 'Failed to generate PoC');
  }
  return r.json();
}

export async function chatWithScan(
  jobId: string,
  message: string,
  history: ChatMessage[] = []
): Promise<{ response: string; ai_model_used: string }> {
  const r = await fetch(`${BASE}/scan/${jobId}/chat`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ message, history }),
  });
  if (!r.ok) {
    const err = await r.json();
    throw new Error(err.detail || 'Chat failed');
  }
  return r.json();
}

// Export
export function getExportUrl(jobId: string, format: 'json' | 'html'): string {
  return `${BASE}/report/${jobId}/export?format=${format}`;
}

// Scheduled scans
export async function listScheduledScans(): Promise<ScheduledScan[]> {
  const r = await fetch(`${BASE}/scheduler`, { headers: headers() });
  return r.json();
}

export async function createScheduledScan(data: {
  target: string; scanners: string[]; tags: string[];
  schedule: string; enabled: boolean; allow_internal: boolean; smart_recon: boolean;
}): Promise<ScheduledScan> {
  const r = await fetch(`${BASE}/scheduler`, {
    method: 'POST', headers: headers(), body: JSON.stringify(data),
  });
  if (!r.ok) { const e = await r.json(); throw new Error(e.detail || 'Failed'); }
  return r.json();
}

export async function deleteScheduledScan(id: string): Promise<void> {
  await fetch(`${BASE}/scheduler/${id}`, { method: 'DELETE', headers: headers() });
}

export async function toggleScheduledScan(id: string, enabled: boolean): Promise<ScheduledScan> {
  const r = await fetch(`${BASE}/scheduler/${id}`, {
    method: 'PATCH', headers: headers(), body: JSON.stringify({ enabled }),
  });
  return r.json();
}

// Notifications
export async function listNotifications(): Promise<NotificationConfig[]> {
  const r = await fetch(`${BASE}/notifications`, { headers: headers() });
  return r.json();
}

export async function createNotification(data: {
  name: string; type: string; config: Record<string, string>; events: string[]; enabled: boolean;
}): Promise<NotificationConfig> {
  const r = await fetch(`${BASE}/notifications`, {
    method: 'POST', headers: headers(), body: JSON.stringify(data),
  });
  if (!r.ok) { const e = await r.json(); throw new Error(e.detail || 'Failed'); }
  return r.json();
}

export async function deleteNotification(id: string): Promise<void> {
  await fetch(`${BASE}/notifications/${id}`, { method: 'DELETE', headers: headers() });
}

export async function testNotification(id: string): Promise<void> {
  await fetch(`${BASE}/notifications/${id}/test`, { method: 'POST', headers: headers() });
}

// Assets
export async function listAssets(): Promise<AssetSummary[]> {
  const r = await fetch(`${BASE}/assets`, { headers: headers() });
  return r.json();
}

export async function getAsset(assetId: string): Promise<AssetDetail> {
  const r = await fetch(`${BASE}/assets/${assetId}`, { headers: headers() });
  if (!r.ok) throw new Error('Asset not found');
  return r.json();
}

// Intelligence
export async function getBaseline(jobId: string): Promise<BaselineResult> {
  const r = await fetch(`${BASE}/scan/${jobId}/baseline`, { headers: headers() });
  return r.json();
}

export async function getMitre(jobId: string): Promise<MitreResult> {
  const r = await fetch(`${BASE}/scan/${jobId}/mitre`, { headers: headers() });
  return r.json();
}

export async function getCompliance(jobId: string): Promise<ComplianceResult> {
  const r = await fetch(`${BASE}/scan/${jobId}/compliance`, { headers: headers() });
  return r.json();
}

export async function getCveInfo(cveId: string): Promise<CveInfo> {
  const r = await fetch(`${BASE}/cve/${cveId}`, { headers: headers() });
  if (!r.ok) throw new Error('CVE info not available');
  return r.json();
}

export async function verifyFinding(findingId: string): Promise<VerifyResult> {
  const r = await fetch(`${BASE}/findings/${findingId}/verify`, { method: 'POST', headers: headers() });
  if (!r.ok) throw new Error('Verification failed');
  return r.json();
}
