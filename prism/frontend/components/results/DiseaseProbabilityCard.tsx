"use client";

import { motion } from "framer-motion";
import { getRiskColor, getRiskLevel, formatPercent, DISEASE_LABELS } from "@/lib/utils";

interface DiseaseProbabilityCardProps {
  disease: string;
  probability: number;
  confidenceInterval?: [number, number];
  trend?: "up" | "down" | "stable";
}

export default function DiseaseProbabilityCard({
  disease,
  probability,
  confidenceInterval,
  trend,
}: DiseaseProbabilityCardProps) {
  const color = getRiskColor(probability);
  const level = getRiskLevel(probability);
  const label = DISEASE_LABELS[disease] || disease;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-4 hover:border-blue-500/30 transition-all duration-300 group"
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold" style={{ color: "var(--text)" }}>{label}</h3>
          <span
            className="text-xs px-2 py-0.5 rounded-full font-medium"
            style={{ backgroundColor: `${color}20`, color }}
          >
            {level}
          </span>
        </div>
        {trend && (
          <span className={`text-lg ${trend === "up" ? "text-red-400" : trend === "down" ? "text-green-400" : ""
            }`}
            style={trend === "stable" ? { color: "var(--text-muted)" } : undefined}
          >
            {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"}
          </span>
        )}
      </div>

      {/* Probability bar */}
      <div className="mb-2">
        <div className="flex justify-between text-sm mb-1">
          <span style={{ color: "var(--text-secondary)" }}>Probability</span>
          <span className="font-mono font-bold" style={{ color }}>
            {formatPercent(probability)}
          </span>
        </div>
        <div className="h-2.5 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: color }}
            initial={{ width: 0 }}
            animate={{ width: `${probability * 100}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Confidence interval */}
      {confidenceInterval && (
        <div className="text-xs mt-2" style={{ color: "var(--text-muted)" }}>
          90% CI: {formatPercent(confidenceInterval[0])} – {formatPercent(confidenceInterval[1])}
        </div>
      )}
    </motion.div>
  );
}
