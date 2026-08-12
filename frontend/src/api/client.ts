import type { HealthCheck, Report, ScanCreated, ScanDetail, ScanSummary } from '../types';

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
  allowInternal = false
): Promise<ScanCreated> {
  const r = await fetch(`${BASE}/scan`, {
    method: 'POST',
    headers: headers(),
    body: JSON.stringify({ target, scanners, allow_internal: allowInternal }),
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
