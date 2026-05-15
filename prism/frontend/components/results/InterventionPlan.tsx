"use client";

import { formatCurrency, formatPercent } from "@/lib/utils";
import type { InterventionPlan } from "@/lib/types";

interface InterventionPlanDisplayProps {
  plan: InterventionPlan;
}

export default function InterventionPlanDisplay({ plan }: InterventionPlanDisplayProps) {
  if (!plan?.recommendations?.length) return null;

  return (
    <div className="space-y-4">
      {plan.recommendations.map((rec, index) => (
        <div 
          key={`${index}-${rec.rank}-${rec.intervention}`}
          className="glass-card p-4 hover:border-blue-500/30 transition-colors relative overflow-hidden group"
        >
          {/* Rank Ribbon */}
          <div className="absolute top-0 left-0 w-12 h-12 bg-blue-600 rounded-br-full flex items-start justify-start p-2">
            <span className="text-white font-bold text-sm">#{rec.rank}</span>
          </div>

          <div className="pl-10">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-semibold text-lg text-white">{rec.intervention.replace(/_/g, " ")}</h3>
              
              {rec.cost_govt === 0 ? (
                <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-xs font-bold ring-1 ring-green-500/50">
                  ₹0 FREE (Govt)
                </span>
              ) : (
                <span className="px-3 py-1 bg-gray-800 text-gray-300 rounded-full text-xs font-semibold">
                  {formatCurrency(rec.cost_private)}
                </span>
              )}
            </div>

            <p className="text-sm text-gray-400 mb-4">{rec.description}</p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-gray-800/50 p-2 rounded">
                <div className="text-xs text-gray-500 mb-1">Expected Benefit</div>
                <div className="font-medium text-green-400">+{rec.qaly_gain.toFixed(1)} QALY</div>
              </div>
              <div className="bg-gray-800/50 p-2 rounded">
                <div className="text-xs text-gray-500 mb-1">Time to Effect</div>
                <div className="font-medium text-blue-400">{rec.time_to_effect_days} Days</div>
              </div>
              <div className="bg-gray-800/50 p-2 rounded">
                <div className="text-xs text-gray-500 mb-1">Side Effect Risk</div>
                <div className="font-medium text-amber-400">{formatPercent(rec.side_effect_risk || 0, 1)}</div>
              </div>
              <div className="bg-gray-800/50 p-2 rounded">
                <div className="text-xs text-gray-500 mb-1">Applicable Scheme</div>
                <div className="font-medium text-purple-400 truncate">{rec.scheme || "None"}</div>
              </div>
            </div>

            {rec.nearest_facility && (
              <div className="mt-3 pt-3 border-t border-gray-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-blue-500">🏥</span>
                  <span className="text-sm font-medium text-gray-300">{rec.nearest_facility.name}</span>
                </div>
                <span className="text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded">
                  {rec.nearest_facility.distance_km} km away
                </span>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
