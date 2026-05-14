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
          <h3 className="font-semibold text-white">{label}</h3>
          <span
            className="text-xs px-2 py-0.5 rounded-full font-medium"
            style={{ backgroundColor: `${color}20`, color }}
          >
            {level}
          </span>
        </div>
        {trend && (
          <span className={`text-lg ${
            trend === "up" ? "text-red-400" : trend === "down" ? "text-green-400" : "text-gray-400"
          }`}>
            {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"}
          </span>
        )}
      </div>

      {/* Probability bar */}
      <div className="mb-2">
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-400">Probability</span>
          <span className="font-mono font-bold" style={{ color }}>
            {formatPercent(probability)}
          </span>
        </div>
        <div className="h-2.5 bg-gray-800 rounded-full overflow-hidden">
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
        <div className="text-xs text-gray-500 mt-2">
          90% CI: {formatPercent(confidenceInterval[0])} – {formatPercent(confidenceInterval[1])}
        </div>
      )}
    </motion.div>
  );
}
