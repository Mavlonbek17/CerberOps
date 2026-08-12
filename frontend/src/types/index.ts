export type ScanStatus = 'queued' | 'running' | 'parsing' | 'analyzing' | 'completed' | 'failed' | 'cancelled';
export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type AiVerdict = 'unreviewed' | 'confirmed' | 'likely_false_positive';

export interface ScanCreated {
  job_id: string;
  status: ScanStatus;
  message: string;
}

export interface Finding {
  id: string;
  title: string;
  description: string;
  severity: Severity;
  host: string;
  port: number | null;
  protocol: string | null;
  url: string | null;
  evidence: string | null;
  scanner_source: string;
  scanner_sources: string[];
  cve_ids: string[];
  reference_urls: string[];
  remediation: string | null;
  is_duplicate: boolean;
  created_at: string;
  ai_verdict: AiVerdict;
  ai_triage_notes: string | null;
  has_poc: boolean;
  cvss_score: number | null;
  cvss_vector: string | null;
}

export interface ScanDetail {
  id: string;
  target: string;
  status: ScanStatus;
  scanners: string[];
  progress: number;
  error_message: string | null;
  findings_count: number;
  severity_counts: Record<string, number>;
  findings: Finding[];
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  smart_recon: boolean;
  recon_summary: string | null;
  ai_scan_plan: string | null;
  tags: string[];
}

export interface ScanSummary {
  id: string;
  target: string;
  status: ScanStatus;
  scanners: string[];
  findings_count: number;
  progress?: number;
  created_at: string;
  tags: string[];
}

export interface Report {
  id: string;
  scan_job_id: string;
  executive_summary: string;
  technical_details: string;
  remediation_plan: string;
  ai_model_used: string;
  generated_at: string;
}

export interface HealthCheck {
  status: string;
  version: string;
  scanners: Record<string, boolean>;
  ollama_available: boolean;
  database: boolean;
}

export interface PocResult {
  finding_id: string;
  poc_code: string;
  poc_explanation: string;
  ai_model_used: string;
  generated_at: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export type ScheduleInterval = 'daily' | 'weekly' | 'monthly';

export interface ScheduledScan {
  id: string;
  target: string;
  scanners: string[];
  tags: string[];
  schedule: ScheduleInterval;
  enabled: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  created_at: string;
}

export interface NotificationConfig {
  id: string;
  name: string;
  type: 'slack' | 'webhook' | 'email';
  config: Record<string, string>;
  events: string[];
  enabled: boolean;
  created_at: string;
}
