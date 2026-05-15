"use client";

import { ComposedChart, Line, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { formatPercent } from "@/lib/utils";
import type { TwinTrajectory } from "@/lib/types";

interface TrajectoryChartProps {
  trajectory: TwinTrajectory;
  showIntervention: boolean;
  showConfidence: boolean;
}

export default function TrajectoryChart({ trajectory, showIntervention, showConfidence }: TrajectoryChartProps) {
  // Merge baseline and intervention data for the chart
  const data = trajectory.without_intervention.map((baseline, i) => {
    const intervention = trajectory.with_best_intervention[i];
    const disease = "tb_prob"; // Example, should be dynamic based on primary diagnosis
    
    const baseValue = baseline.values[disease] || 0;
    const intValue = intervention ? intervention.values[disease] || 0 : 0;
    
    // Mock confidence intervals (±10% to ±20% growing over time)
    const ciSpread = 0.05 + (i * 0.02);
    
    return {
      month: baseline.month,
      baseline: baseValue,
      intervention: intValue,
      baseLow: Math.max(0, baseValue - ciSpread),
      baseHigh: Math.min(1, baseValue + ciSpread),
      intLow: Math.max(0, intValue - ciSpread),
      intHigh: Math.min(1, intValue + ciSpread),
    };
  });

  return (
    <div className="glass-card p-5 h-80 flex flex-col">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">
        Digital Twin Disease Trajectory
      </h3>
      <div className="flex-1 w-full min-h-[260px] min-w-0">
        <ResponsiveContainer minWidth={0} minHeight={0} width="100%" height={260}>
          <ComposedChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <XAxis 
              dataKey="month" 
              tickFormatter={(m) => `M+${m}`} 
              tick={{ fill: "#94a3b8", fontSize: 12 }} 
              axisLine={false} 
              tickLine={false}
            />
            <YAxis 
              tickFormatter={(v) => formatPercent(v)} 
              domain={[0, 1]} 
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{ backgroundColor: "#111827", borderColor: "#1f2937", borderRadius: "8px" }}
              labelFormatter={(label) => `Month ${label}`}
              formatter={(value, name) => {
                const n = typeof value === "number" ? value : Number(value) || 0;
                const nm = String(name ?? "");
                if (nm === "baseline") return [formatPercent(n), "Without Intervention"];
                if (nm === "intervention") return [formatPercent(n), "With Intervention"];
                return [String(value ?? ""), nm];
              }}
            />
            
            <ReferenceLine x={0} stroke="#4b5563" strokeDasharray="3 3" label={{ position: "top", value: "Today", fill: "#94a3b8", fontSize: 12 }} />
            <ReferenceLine y={0.8} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.5} label={{ position: "insideTopLeft", value: "Critical Risk Threshold", fill: "#ef4444", fontSize: 10 }} />

            {/* Confidence Bands */}
            {showConfidence && (
              <Area key="baseHigh" type="monotone" dataKey="baseHigh" stroke="none" fill="#ef4444" fillOpacity={0.05} />
            )}
            {showConfidence && (
              <Area key="baseLow" type="monotone" dataKey="baseLow" stroke="none" fill="#111827" fillOpacity={1} />
            )}
            {showConfidence && showIntervention && (
              <Area key="intHigh" type="monotone" dataKey="intHigh" stroke="none" fill="#22c55e" fillOpacity={0.05} />
            )}
            {showConfidence && showIntervention && (
              <Area key="intLow" type="monotone" dataKey="intLow" stroke="none" fill="#111827" fillOpacity={1} />
            )}

            {/* Main Lines */}
            <Line 
              type="monotone" 
              dataKey="baseline" 
              stroke="#ef4444" 
              strokeWidth={3} 
              dot={false}
              activeDot={{ r: 6 }}
              isAnimationActive={true}
              strokeDasharray="5 5"
            />
            {showIntervention && (
              <Line 
                type="monotone" 
                dataKey="intervention" 
                stroke="#22c55e" 
                strokeWidth={3} 
                dot={false}
                activeDot={{ r: 6 }}
                isAnimationActive={true}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      
      {/* Legend */}
      <div className="flex gap-6 mt-4 justify-center text-xs">
        <div className="flex items-center gap-2 text-gray-400">
          <div className="w-4 h-1 border-b-2 border-red-500 border-dashed" /> Baseline Trajectory
        </div>
        {showIntervention && (
          <div className="flex items-center gap-2 text-gray-400">
            <div className="w-4 h-1 bg-green-500 rounded" /> With Intervention
          </div>
        )}
      </div>
    </div>
  );
}
