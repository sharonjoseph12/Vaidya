"use client";

import type { TwinTrajectory } from "@/lib/types";

interface DigitalTwinSummaryProps {
  trajectory: TwinTrajectory;
}

export default function DigitalTwinSummary({ trajectory }: DigitalTwinSummaryProps) {
  const tBaseline = trajectory.months_to_critical;
  const tIntervention = trajectory.months_to_critical_with_intervention;
  const timeGained = (tIntervention && tBaseline) ? tIntervention - tBaseline : 0;

  return (
    <div className="glass-card p-4 bg-gradient-to-br from-blue-900/10 to-cyan-900/10">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">Prognostic Summary</h3>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="p-3 bg-gray-800/50 rounded-lg">
          <div className="text-xs text-gray-400 mb-1">Time to Critical Risk</div>
          <div className="text-xl font-bold text-red-400">
            {tBaseline ? `${tBaseline.toFixed(1)} Months` : "Stable"}
          </div>
          <div className="text-xs text-gray-500 mt-1">Baseline trajectory</div>
        </div>
        
        <div className="p-3 bg-gray-800/50 rounded-lg">
          <div className="text-xs text-gray-400 mb-1">With Intervention</div>
          <div className="text-xl font-bold text-green-400">
            {tIntervention ? `${tIntervention.toFixed(1)} Months` : "Stable"}
          </div>
          {timeGained > 0 && (
            <div className="text-xs text-green-500 mt-1 font-medium">
              +{timeGained.toFixed(1)} months gained
            </div>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500 pt-3 border-t border-gray-800">
        <span>Active Intervention:</span>
        <span className="text-gray-300 font-medium bg-gray-800 px-2 py-1 rounded">
          {trajectory.intervention_applied?.replace(/_/g, " ")}
        </span>
      </div>
    </div>
  );
}
