import { ArrowLeft, Brain, Clock } from 'lucide-react';
import type { Report } from '../types';

interface Props {
  report: Report;
  onBack: () => void;
}

export default function ReportView({ report, onBack }: Props) {
  return (
    <div className="bg-[var(--bg-card)] rounded-lg border border-[var(--border)]">
      <div className="p-4 border-b border-[var(--border)]">
        <div className="flex items-center justify-between">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to findings
          </button>
          <div className="flex items-center gap-3 text-xs text-[var(--text-secondary)]">
            <span className="flex items-center gap-1">
              <Brain className="w-3.5 h-3.5" />
              {report.ai_model_used}
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5" />
              {new Date(report.generated_at).toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6">
        <section>
          <h3 className="text-lg font-semibold mb-2 text-[var(--accent)]">Executive Summary</h3>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{report.executive_summary}</p>
        </section>

        <hr className="border-[var(--border)]" />

        <section>
          <h3 className="text-lg font-semibold mb-2 text-[var(--accent)]">Technical Details</h3>
          <div className="text-sm leading-relaxed whitespace-pre-wrap bg-[var(--bg-primary)] p-4 rounded-lg border border-[var(--border)]">
            {report.technical_details}
          </div>
        </section>

        <hr className="border-[var(--border)]" />

        <section>
          <h3 className="text-lg font-semibold mb-2 text-[var(--success)]">Remediation Plan</h3>
          <div className="text-sm leading-relaxed whitespace-pre-wrap bg-[var(--success)]/5 p-4 rounded-lg border border-[var(--success)]/20">
            {report.remediation_plan}
          </div>
        </section>
      </div>
    </div>
  );
}
