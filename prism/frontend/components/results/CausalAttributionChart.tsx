"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { formatPercent } from "@/lib/utils";

interface CausalAttributionChartProps {
  attributions: Record<string, number>;
}

export default function CausalAttributionChart({ attributions }: CausalAttributionChartProps) {
  const data = Object.entries(attributions)
    .map(([factor, weight]) => ({
      name: factor.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()),
      value: weight,
    }))
    .sort((a, b) => b.value - a.value);

  // Gradient colors based on weight
  const getColor = (index: number) => {
    const colors = ["#3b82f6", "#06b6d4", "#22c55e", "#f59e0b", "#a855f7"];
    return colors[index % colors.length];
  };

  return (
    <div className="glass-card p-5 h-64 flex flex-col">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">Feature Importance</h3>
      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 0, right: 20, left: -20, bottom: 0 }}>
            <XAxis type="number" hide domain={[0, 'dataMax']} />
            <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: "#94a3b8", fontSize: 12 }} width={120} />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.05)" }}
              contentStyle={{ backgroundColor: "#111827", borderColor: "#1f2937", borderRadius: "8px" }}
              formatter={(value) => {
                const n = typeof value === "number" ? value : Number(value) || 0;
                return [formatPercent(n, 1), "Contribution"];
              }}
            />
            <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={20}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getColor(index)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
