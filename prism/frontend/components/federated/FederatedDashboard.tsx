"use client";

import { useEffect, useState } from "react";
import { getFLStatus, getFLRounds } from "@/lib/api";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { FLStatus, FLRound } from "@/lib/types";
import { formatPercent } from "@/lib/utils";

export default function FederatedDashboard() {
  const [status, setStatus] = useState<FLStatus | null>(null);
  const [rounds, setRounds] = useState<FLRound[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoadError(null);
        const [statusData, roundsData] = await Promise.all([
          getFLStatus(),
          getFLRounds(20)
        ]);
        setStatus(statusData);
        setRounds(roundsData.rounds.reverse()); // Chronological for chart
      } catch (err) {
        console.error("Failed to load FL data", err);
        setLoadError(
          err instanceof Error ? err.message : "Could not load federated learning data. Is the API running?",
        );
      } finally {
        setLoading(false);
      }
    }
    fetchData();
    const interval = setInterval(fetchData, 10000); // Poll every 10s
    return () => clearInterval(interval);
  }, []);

  if (loadError) {
    return (
      <div className="glass-card p-6 border border-red-500/25 text-red-200 text-sm">
        {loadError}
      </div>
    );
  }

  if (loading || !status) {
    return <div className="glass-card p-6 animate-pulse bg-gray-800/50 h-64"></div>;
  }

  // Chart data
  const chartData = rounds.map(r => ({
    round: r.round_number,
    accuracy: r.metrics?.accuracy || 0,
    loss: r.metrics?.loss || 0,
  }));

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <div className="flex justify-between items-center glass-card p-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className={`w-4 h-4 rounded-full ${status.server_status === 'running' ? 'bg-green-500' : 'bg-red-500'}`}></div>
            {status.server_status === 'running' && <div className="absolute inset-0 bg-green-500 rounded-full animate-ping opacity-75"></div>}
          </div>
          <h2 className="text-xl font-bold text-white">Federated Learning Server</h2>
        </div>
        <div className="text-sm text-gray-400 font-mono">
          Model: {status.global_model_version}
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-4 border-b-2 border-blue-500">
          <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Current Round</div>
          <div className="text-3xl font-bold text-white">{status.current_round}</div>
        </div>
        <div className="glass-card p-4 border-b-2 border-green-500">
          <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Active Nodes</div>
          <div className="text-3xl font-bold text-white">{status.active_nodes} <span className="text-sm text-gray-500 font-normal">/ {status.total_nodes}</span></div>
        </div>
        <div className="glass-card p-4 border-b-2 border-purple-500">
          <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Privacy Budget (ε)</div>
          <div className="text-3xl font-bold text-white">{status.cumulative_dp_epsilon.toFixed(2)} <span className="text-sm text-gray-500 font-normal">spent</span></div>
        </div>
        <div className="glass-card p-4 border-b-2 border-amber-500">
          <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">Global Accuracy</div>
          <div className="text-3xl font-bold text-white">{formatPercent(status.last_round_metrics?.accuracy || 0)}</div>
        </div>
      </div>

      {/* Accuracy Chart */}
      <div className="glass-card p-5 h-80">
        <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-4">Model Convergence</h3>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
            <XAxis dataKey="round" stroke="#94a3b8" tick={{fontSize: 12}} />
            <YAxis stroke="#94a3b8" tick={{fontSize: 12}} domain={[0.5, 1]} tickFormatter={(v) => formatPercent(v)} />
            <Tooltip 
              contentStyle={{ backgroundColor: "#111827", borderColor: "#1f2937", borderRadius: "8px" }}
              formatter={(value) => formatPercent(typeof value === "number" ? value : Number(value) || 0)}
            />
            <Line type="monotone" dataKey="accuracy" stroke="#22c55e" strokeWidth={3} dot={false} activeDot={{ r: 8 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
