"use client";

import { formatDate } from "@/lib/utils";
import type { HealthRecord } from "@/lib/types";

interface HealthHistoryTimelineProps {
  records: HealthRecord[];
}

export default function HealthHistoryTimeline({ records }: HealthHistoryTimelineProps) {
  if (!records || records.length === 0) {
    return (
      <div className="glass-card p-6 text-center text-gray-400">
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
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-6">
        ABDM Health History
      </h3>
      
      <div className="relative border-l border-gray-700 ml-3 space-y-6">
        {sortedRecords.map((record, idx) => (
          <div key={`${record.type}-${record.date}-${idx}`} className="relative pl-6">
            {/* Timeline dot */}
            <div className="absolute -left-3.5 top-1 w-7 h-7 bg-gray-800 rounded-full border-2 border-gray-700 flex items-center justify-center text-xs">
              {getIcon(record.type)}
            </div>

            <div className="bg-gray-800/30 rounded-lg p-3 border border-gray-700/50 hover:border-gray-600 transition-colors">
              <div className="flex justify-between items-start mb-1">
                <span className="font-medium text-blue-300">{record.type}</span>
                <span className="text-xs text-gray-500">{formatDate(record.date)}</span>
              </div>
              
              {record.findings && (
                <p className="text-sm text-gray-300 mt-2">{record.findings}</p>
              )}
              
              {record.parameter && record.value !== undefined && (
                <div className="mt-2 text-sm">
                  <span className="text-gray-400">{record.parameter}: </span>
                  <span className="font-semibold text-white">{record.value} {record.unit}</span>
                </div>
              )}
              
              {record.codes && record.codes.length > 0 && (
                <div className="mt-2 flex gap-2 flex-wrap">
                  {record.codes.map((c, codeIdx) => (
                    <span key={`${idx}-${codeIdx}-${c}`} className="text-xs bg-gray-900 text-gray-400 px-2 py-0.5 rounded border border-gray-800">
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
