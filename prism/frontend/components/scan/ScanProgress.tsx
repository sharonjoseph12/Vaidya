"use client";

import { motion } from "framer-motion";

const STAGES = [
  { key: "sensing", label: "Sensing", icon: "🔬", color: "#3b82f6" },
  { key: "reasoning", label: "Reasoning", icon: "🧠", color: "#a855f7" },
  { key: "projecting", label: "Projecting", icon: "📈", color: "#06b6d4" },
  { key: "optimizing", label: "Optimizing", icon: "⚡", color: "#22c55e" },
];

interface ScanProgressProps {
  stage: string;
  progress: number;
  message?: string;
}

export default function ScanProgress({ stage, progress, message }: ScanProgressProps) {
  const currentIndex = STAGES.findIndex((s) => s.key === stage);
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (progress * circumference);

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Progress ring */}
      <div className="relative w-48 h-48">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 200 200">
          <circle cx="100" cy="100" r={radius} fill="none" stroke="#1f2937" strokeWidth="8" />
          <motion.circle
            cx="100" cy="100" r={radius}
            fill="none"
            stroke={STAGES[Math.max(0, currentIndex)]?.color || "#3b82f6"}
            strokeWidth="8"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold">{Math.round(progress * 100)}%</span>
          <span className="text-xs text-gray-400 mt-1">{stage === "complete" ? "Done" : "Processing"}</span>
        </div>
      </div>

      {/* Stage indicators */}
      <div className="flex gap-4">
        {STAGES.map((s, i) => {
          const isActive = i === currentIndex;
          const isDone = i < currentIndex || stage === "complete";
          return (
            <motion.div
              key={s.key}
              className={`flex flex-col items-center gap-1 transition-all duration-300 ${
                isDone ? "opacity-100" : isActive ? "opacity-100" : "opacity-30"
              }`}
              animate={isActive ? { scale: [1, 1.1, 1] } : {}}
              transition={{ repeat: Infinity, duration: 1.5 }}
            >
              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${
                isDone ? "bg-green-500/20 ring-1 ring-green-500" :
                isActive ? "bg-blue-500/20 ring-1 ring-blue-500 pulse-ring" :
                "bg-gray-800"
              }`}>
                {isDone ? "✓" : s.icon}
              </div>
              <span className="text-xs">{s.label}</span>
            </motion.div>
          );
        })}
      </div>

      {/* Message */}
      {message && (
        <p className="text-sm text-gray-400 text-center max-w-xs">{message}</p>
      )}
    </div>
  );
}
