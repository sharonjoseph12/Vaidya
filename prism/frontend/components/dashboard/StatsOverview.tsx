"use client";

interface StatsOverviewProps {
  stats?: {
    scansToday: number;
    highRiskDetected: number;
    avgConfidence: number;
    activeNodes: number;
  };
}

export default function StatsOverview({ stats }: StatsOverviewProps) {
  // Use mock data if not provided (would normally come from API)
  const data = stats || {
    scansToday: 42,
    highRiskDetected: 7,
    avgConfidence: 0.86,
    activeNodes: 4,
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="glass-card p-5 border-l-4 border-blue-500">
        <div className="text-gray-400 text-sm mb-1">Scans Today</div>
        <div className="text-3xl font-bold text-white">{data.scansToday}</div>
        <div className="text-xs text-green-400 mt-2">↑ 12% vs yesterday</div>
      </div>
      
      <div className="glass-card p-5 border-l-4 border-red-500">
        <div className="text-gray-400 text-sm mb-1">High Risk Detected</div>
        <div className="text-3xl font-bold text-red-400">{data.highRiskDetected}</div>
        <div className="text-xs text-gray-500 mt-2">Requires immediate attention</div>
      </div>
      
      <div className="glass-card p-5 border-l-4 border-purple-500">
        <div className="text-gray-400 text-sm mb-1">Avg AI Confidence</div>
        <div className="text-3xl font-bold text-white">{(data.avgConfidence * 100).toFixed(1)}%</div>
        <div className="text-xs text-gray-500 mt-2">Across all modalities</div>
      </div>
      
      <div className="glass-card p-5 border-l-4 border-green-500">
        <div className="text-gray-400 text-sm mb-1">Active FL Nodes</div>
        <div className="text-3xl font-bold text-white">{data.activeNodes}</div>
        <div className="text-xs text-green-400 mt-2">Model syncing online</div>
      </div>
    </div>
  );
}
