"use client";

import { getRiskColor, formatPercent, DISEASE_LABELS } from "@/lib/utils";

interface UncertaintyBandsProps {
  uncertainties: Record<string, [number, number]>;
}

export default function UncertaintyBands({ uncertainties }: UncertaintyBandsProps) {
  const entries = Object.entries(uncertainties).sort(
    ([, a], [, b]) => (b[0] + b[1]) / 2 - (a[0] + a[1]) / 2,
  );

  return (
    <div className="glass-card p-5">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">
        Uncertainty Bounds (90% Conformal)
      </h3>
      <div className="space-y-3">
        {entries.map(([disease, [low, high]]) => {
          const mid = (low + high) / 2;
          const color = getRiskColor(mid);
          const label = DISEASE_LABELS[disease] || disease;

          return (
            <div key={disease} className="flex items-center gap-3">
              <span className="w-24 text-xs text-gray-400 truncate">{label}</span>
              <div className="flex-1 h-5 bg-gray-800 rounded-full relative">
                <div
                  className="absolute h-full rounded-full opacity-30"
                  style={{
                    left: `${low * 100}%`,
                    width: `${(high - low) * 100}%`,
                    backgroundColor: color,
                  }}
                />
                <div
                  className="absolute w-2 h-full rounded-full"
                  style={{
                    left: `${mid * 100}%`,
                    backgroundColor: color,
                    transform: "translateX(-50%)",
                  }}
                />
              </div>
              <span className="w-24 text-xs font-mono text-gray-500 text-right">
                {formatPercent(low, 0)}–{formatPercent(high, 0)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
