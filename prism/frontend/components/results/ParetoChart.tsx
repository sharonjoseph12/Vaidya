"use client";

import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, Tooltip, ResponsiveContainer } from "recharts";
import { formatCurrency } from "@/lib/utils";
import type { ParetoOption } from "@/lib/types";

interface ParetoChartProps {
  options: ParetoOption[];
}

export default function ParetoChart({ options }: ParetoChartProps) {
  if (!options || options.length === 0) return null;

  return (
    <div className="glass-card p-5 h-64 flex flex-col">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-2">
        Cost vs. Outcome Trade-offs
      </h3>
      <p className="text-xs text-gray-500 mb-4">Pareto frontier of available interventions</p>
      
      <div className="flex-1 w-full min-h-[200px] min-w-0">
        <ResponsiveContainer minWidth={0} minHeight={0} width="100%" height={220}>
          <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
            <XAxis 
              type="number" 
              dataKey="cost" 
              name="Cost" 
              tickFormatter={(v) => `₹${v}`} 
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              label={{ value: "Cost (INR)", position: "insideBottom", offset: -15, fill: "#94a3b8", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis 
              type="number" 
              dataKey="qaly_gain" 
              name="Benefit" 
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              label={{ value: "Health Benefit (QALY)", angle: -90, position: "insideLeft", offset: 10, fill: "#94a3b8", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <ZAxis type="category" dataKey="label" name="Option" />
            <Tooltip 
              cursor={{ strokeDasharray: "3 3" }}
              contentStyle={{ backgroundColor: "#111827", borderColor: "#1f2937", borderRadius: "8px" }}
              formatter={(value, name) => {
                if (value == null || value === "") return ["—", String(name ?? "")];
                const label = String(name ?? "");
                if (label === "Cost") return [formatCurrency(Number(value)), label];
                if (label === "Benefit" || label === "qaly_gain") return [`${value} QALY`, label];
                return [String(value), label];
              }}
            />
            <Scatter name="Options" data={options} fill="#3b82f6" shape="circle" />
          </ScatterChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
