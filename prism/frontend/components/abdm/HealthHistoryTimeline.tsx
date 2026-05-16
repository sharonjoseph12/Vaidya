"use client";

import { formatDate } from "@/lib/utils";
import type { HealthRecord } from "@/lib/types";

interface HealthHistoryTimelineProps {
  records: HealthRecord[];
}

export default function HealthHistoryTimeline({ records }: HealthHistoryTimelineProps) {
  if (!records || records.length === 0) {
    return (
      <div className="glass-card p-6 text-center" style={{ color: "var(--text-muted)" }}>
        <p>No historical health records found.</p>
        <p className="text-xs mt-1">Connect ABHA ID to fetch patient history.</p>
      </div>
    );
  }

  // Sort records by date descending
  const sortedRecords = [...records].sort(
    (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
  );

  const getIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case "prescription": return "💊";
      case "diagnosticreport": return "🔬";
      case "discharge": return "🏥";
      case "immunization": return "💉";
      default: return "📄";
    }
  };

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-semibold uppercase tracking-wide mb-6" style={{ color: "var(--text-secondary)" }}>
        ABDM Health History
      </h3>

      <div className="relative ml-3 space-y-6 border-l" style={{ borderColor: "var(--border)" }}>
        {sortedRecords.map((record, idx) => (
          <div key={idx} className="relative pl-6">
            {/* Timeline dot */}
            <div
              className="absolute -left-3.5 top-1 w-7 h-7 rounded-full border-2 flex items-center justify-center text-xs"
              style={{ background: "var(--surface-hover)", borderColor: "var(--border)" }}
            >
              {getIcon(record.type)}
            </div>

            <div
              className="rounded-lg p-3 border transition-colors"
              style={{ background: "var(--surface-hover)", borderColor: "var(--border)" }}
              onMouseEnter={e => (e.currentTarget.style.borderColor = "var(--text-muted)")}
              onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--border)")}
            >
              <div className="flex justify-between items-start mb-1">
                <span className="font-medium text-blue-400">{record.type}</span>
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>{formatDate(record.date)}</span>
              </div>

              {record.findings && (
                <p className="text-sm mt-2" style={{ color: "var(--text-secondary)" }}>{record.findings}</p>
              )}

              {record.parameter && record.value !== undefined && (
                <div className="mt-2 text-sm">
                  <span style={{ color: "var(--text-secondary)" }}>{record.parameter}: </span>
                  <span className="font-semibold" style={{ color: "var(--text)" }}>{record.value} {record.unit}</span>
                </div>
              )}

              {record.codes && record.codes.length > 0 && (
                <div className="mt-2 flex gap-2 flex-wrap">
                  {record.codes.map(c => (
                    <span
                      key={c}
                      className="text-xs px-2 py-0.5 rounded border"
                      style={{ background: "var(--surface)", color: "var(--text-muted)", borderColor: "var(--border)" }}
                    >
                      {c}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
