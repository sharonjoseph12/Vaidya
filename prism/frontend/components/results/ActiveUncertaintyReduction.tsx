"use client";

import { motion } from "framer-motion";
import { formatCurrency, formatPercent } from "@/lib/utils";
import type { TestRecommendation } from "@/lib/types";

interface ActiveUncertaintyReductionProps {
  recommendation: TestRecommendation;
}

export default function ActiveUncertaintyReduction({ recommendation }: ActiveUncertaintyReductionProps) {
  if (!recommendation) return null;

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="glass-card p-5 border-blue-500/30 shadow-[0_0_15px_rgba(59,130,246,0.15)] relative overflow-hidden"
    >
      <div className="absolute -right-4 -top-4 text-blue-500/10 text-9xl">?</div>
      
      <div className="relative z-10">
        <h3 className="text-sm font-semibold text-blue-400 uppercase tracking-wide mb-1 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" /> 
          Next Best Action
        </h3>
        <p className="text-xs text-gray-400 mb-4">To maximize diagnostic certainty</p>

        <div className="flex justify-between items-start mb-3">
          <div className="text-xl font-bold text-white">
            {recommendation.recommended_test.replace(/_/g, " ")}
          </div>
          <div className="text-sm font-semibold bg-gray-800 px-3 py-1 rounded-full text-gray-300">
            {formatCurrency(recommendation.cost)}
          </div>
        </div>

        <p className="text-sm text-gray-300 mb-4">{recommendation.rationale}</p>

        <div className="bg-blue-900/20 p-3 rounded-lg border border-blue-500/20 flex items-center justify-between">
          <span className="text-sm text-blue-200">Expected Uncertainty Reduction</span>
          <span className="font-bold text-lg text-blue-400">
            {formatPercent(recommendation.expected_uncertainty_reduction)}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
