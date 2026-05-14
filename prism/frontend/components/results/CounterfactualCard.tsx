"use client";

import { motion } from "framer-motion";
import { formatPercent } from "@/lib/utils";
import type { CounterfactualExplanation } from "@/lib/types";

interface CounterfactualCardProps {
  explanation: CounterfactualExplanation;
  originalProbability: number;
}

export default function CounterfactualCard({ explanation, originalProbability }: CounterfactualCardProps) {
  const diff = originalProbability - explanation.new_probability;
  const isImprovement = diff > 0;
  
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card p-4 bg-gradient-to-br from-indigo-900/20 to-purple-900/20"
    >
      <div className="flex justify-between items-start mb-3">
        <h4 className="font-semibold text-white flex items-center gap-2">
          <span className="text-purple-400">⚡</span> What-If Scenario
        </h4>
        <span className="text-xs px-2 py-1 bg-gray-800 rounded-full text-gray-300">
          Feasibility: {formatPercent(explanation.feasibility_score)}
        </span>
      </div>

      <div className="mb-4">
        <p className="text-sm text-gray-400 mb-2">If we change:</p>
        <ul className="space-y-1">
          {Object.entries(explanation.changes).map(([feature, [oldVal, newVal]]) => (
            <li key={feature} className="text-sm flex items-center gap-2">
              <span className="text-gray-300 bg-gray-800 px-2 py-0.5 rounded">{feature.replace(/_/g, " ")}</span>
              <span className="text-gray-500 line-through">{oldVal}</span>
              <span className="text-gray-400">→</span>
              <span className="text-green-400 font-medium">{newVal}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="pt-3 border-t border-gray-700/50 flex justify-between items-center">
        <div className="text-sm text-gray-400">New Risk Probability</div>
        <div className="flex items-center gap-2">
          <span className="text-gray-500 line-through text-xs">{formatPercent(originalProbability)}</span>
          <span className={`font-bold text-lg ${isImprovement ? "text-green-400" : "text-red-400"}`}>
            {formatPercent(explanation.new_probability)}
          </span>
          <span className={`text-xs ${isImprovement ? "text-green-400" : "text-red-400"}`}>
            ({isImprovement ? "↓" : "↑"} {formatPercent(Math.abs(diff))})
          </span>
        </div>
      </div>
    </motion.div>
  );
}
