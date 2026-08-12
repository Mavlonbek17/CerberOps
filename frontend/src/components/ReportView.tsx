import { ArrowLeft, Brain, Clock, FileDown } from 'lucide-react';
import type { Report } from '../types';

interface Props {
  report: Report;
  onBack: () => void;
}

export default function ReportView({ report, onBack }: Props) {
  return (
    <section className="bg-surface-container-low border border-outline-variant/50 rounded-md overflow-hidden h-full flex flex-col">
      <div className="px-4 py-3 border-b border-outline-variant/50 flex items-center justify-between shrink-0 bg-surface-container-high">
        <button
          onClick={onBack}
          className="flex items-center gap-2 text-sm font-label text-on-surface-variant hover:text-on-background transition-colors cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to findings
        </button>
        <div className="flex items-center gap-5 text-sm font-label text-on-surface-variant">
          <span className="flex items-center gap-1.5">
            <Brain className="w-4 h-4 text-secondary" />
            {report.ai_model_used}
          </span>
          <span className="flex items-center gap-1.5">
            <Clock className="w-4 h-4" />
            {new Date(report.generated_at).toLocaleString()}
          </span>
          <button
            onClick={() => {
              const blob = new Blob(
                [
                  `# Security Report\n\n## Executive Summary\n${report.executive_summary}\n\n## Technical Details\n${report.technical_details}\n\n## Remediation Plan\n${report.remediation_plan}`,
                ],
                { type: 'text/markdown' },
              );
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `cerberops-report-${report.scan_job_id.slice(0, 8)}.md`;
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="flex items-center gap-1.5 text-secondary hover:text-secondary-fixed-dim transition-colors cursor-pointer font-medium"
          >
            <FileDown className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-5 space-y-5">
        <section>
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-1 h-6 rounded-full bg-secondary" />
            <h3 className="text-base font-headline font-semibold uppercase tracking-wider text-secondary">Executive Summary</h3>
          </div>
          <p className="text-sm text-on-surface-variant leading-relaxed whitespace-pre-wrap pl-4">{report.executive_summary}</p>
        </section>

        <div className="border-t border-outline-variant/50" />

        <section>
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-1 h-6 rounded-full bg-tertiary" />
            <h3 className="text-base font-headline font-semibold uppercase tracking-wider text-tertiary">Technical Details</h3>
          </div>
          <div className="text-sm text-on-surface-variant leading-relaxed whitespace-pre-wrap font-mono bg-surface-container p-4 rounded-md border border-outline-variant/45">
            {report.technical_details}
          </div>
        </section>

        <div className="border-t border-outline-variant/50" />

        <section>
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-1 h-6 rounded-full bg-primary" />
            <h3 className="text-base font-headline font-semibold uppercase tracking-wider text-primary">Remediation Plan</h3>
          </div>
          <div className="text-sm text-on-surface leading-relaxed whitespace-pre-wrap bg-primary/10 p-4 rounded-md border border-primary/25">
            {report.remediation_plan}
          </div>
        </section>
      </div>
    </section>
  );
}
