"use client";

interface TrajectoryControlsProps {
  showIntervention: boolean;
  setShowIntervention: (val: boolean) => void;
  showConfidence: boolean;
  setShowConfidence: (val: boolean) => void;
  horizon: number;
  setHorizon: (val: number) => void;
}

export default function TrajectoryControls({
  showIntervention, setShowIntervention,
  showConfidence, setShowConfidence,
  horizon, setHorizon
}: TrajectoryControlsProps) {
  return (
    <div className="glass-card p-4 flex flex-col gap-4">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Simulation Controls</h3>
      
      {/* Toggles */}
      <div className="flex flex-col gap-3">
        <label className="flex items-center justify-between cursor-pointer group">
          <span className="text-sm text-gray-300 group-hover:text-white transition-colors">Show Intervention Plan</span>
          <div className={`w-10 h-6 rounded-full transition-colors relative ${showIntervention ? "bg-blue-600" : "bg-gray-700"}`}>
            <div className={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform ${showIntervention ? "translate-x-4" : ""}`} />
          </div>
          <input type="checkbox" className="hidden" checked={showIntervention} onChange={(e) => setShowIntervention(e.target.checked)} />
        </label>
        
        <label className="flex items-center justify-between cursor-pointer group">
          <span className="text-sm text-gray-300 group-hover:text-white transition-colors">Show Uncertainty Bands</span>
          <div className={`w-10 h-6 rounded-full transition-colors relative ${showConfidence ? "bg-blue-600" : "bg-gray-700"}`}>
            <div className={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform ${showConfidence ? "translate-x-4" : ""}`} />
          </div>
          <input type="checkbox" className="hidden" checked={showConfidence} onChange={(e) => setShowConfidence(e.target.checked)} />
        </label>
      </div>

      <hr className="border-gray-800" />

      {/* Slider */}
      <div>
        <div className="flex justify-between text-sm mb-2">
          <span className="text-gray-300">Prediction Horizon</span>
          <span className="text-blue-400 font-medium">{horizon} Months</span>
        </div>
        <input 
          type="range" 
          min="3" max="24" step="3" 
          value={horizon} 
          onChange={(e) => setHorizon(parseInt(e.target.value))}
          className="w-full accent-blue-500 cursor-pointer bg-gray-800 rounded-lg appearance-none h-2"
        />
        <div className="flex justify-between text-xs text-gray-500 mt-1 px-1">
          <span>3m</span>
          <span>12m</span>
          <span>24m</span>
        </div>
      </div>
    </div>
  );
}
