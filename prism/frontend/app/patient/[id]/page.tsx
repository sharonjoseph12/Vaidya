"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { getResults } from "@/lib/api";
import type { DiagnosticResult } from "@/lib/types";

// US1 Components
import DiseaseProbabilityCard from "@/components/results/DiseaseProbabilityCard";
import UncertaintyBands from "@/components/results/UncertaintyBands";

// US2 Components
import CausalGraphViz from "@/components/results/CausalGraphViz";
import CausalAttributionChart from "@/components/results/CausalAttributionChart";
import CounterfactualCard from "@/components/results/CounterfactualCard";

// US3 Components
import TrajectoryChart from "@/components/results/TrajectoryChart";
import TrajectoryControls from "@/components/results/TrajectoryControls";
import DigitalTwinSummary from "@/components/results/DigitalTwinSummary";

// US4 Components
import InterventionPlanDisplay from "@/components/results/InterventionPlan";
import ParetoChart from "@/components/results/ParetoChart";
import ActiveUncertaintyReduction from "@/components/results/ActiveUncertaintyReduction";

export default function PatientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  
  const [result, setResult] = useState<DiagnosticResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Trajectory controls state
  const [showIntervention, setShowIntervention] = useState(true);
  const [showConfidence, setShowConfidence] = useState(true);
  const [horizon, setHorizon] = useState(12);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await getResults(id);
        setResult(data);
      } catch (err: any) {
        setError(err.message || "Failed to load results");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center gradient-bg">
        <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gradient-bg">
        <div className="text-4xl mb-4">⚠️</div>
        <h2 className="text-2xl font-bold text-red-400">Error</h2>
        <p className="text-gray-400 mt-2">{error || "Results not found"}</p>
        <button onClick={() => router.push("/dashboard")} className="mt-6 px-6 py-2 bg-gray-800 rounded hover:bg-gray-700 transition">Back to Dashboard</button>
      </div>
    );
  }

  return (
    <div className="min-h-screen gradient-bg p-6 md:p-10 text-gray-100 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header (US1/US5) */}
        <header className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 glass-card p-6 border-b border-blue-500/30">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center gap-3">
              Patient Assessment <span className="text-sm font-normal text-gray-400 font-mono">#{id.split("-")[0]}</span>
            </h1>
            <p className="text-gray-400 mt-1">
              Primary Diagnosis: <span className="text-blue-400 font-semibold">{result.primary_diagnosis?.replace(/_/g, " ")}</span>
            </p>
          </div>
          <div className="flex gap-3">
            <button className="px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-600 rounded-lg text-sm font-medium transition flex items-center gap-2">
              <span>📄</span> Download PDF
            </button>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition shadow-[0_0_15px_rgba(59,130,246,0.3)] flex items-center gap-2">
              <span>☁️</span> Push to ABDM
            </button>
          </div>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Diagnostics (US1) */}
          <div className="lg:col-span-1 space-y-6">
            <h2 className="text-xl font-bold text-white border-b border-gray-800 pb-2">1. Diagnostics (SENSE)</h2>
            
            <div className="space-y-4">
              {Object.entries(result.disease_probabilities || {}).slice(0, 4).map(([disease, prob]) => (
                <DiseaseProbabilityCard 
                  key={disease} 
                  disease={disease} 
                  probability={prob} 
                  confidenceInterval={result.uncertainty_bounds?.[disease]}
                />
              ))}
            </div>

            {result.uncertainty_bounds && (
              <UncertaintyBands uncertainties={result.uncertainty_bounds} />
            )}
          </div>

          {/* Middle Column: Causality & Trajectory (US2, US3) */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* US2: Causal Explanation */}
            <section className="space-y-4">
              <h2 className="text-xl font-bold text-white border-b border-gray-800 pb-2">2. Causal Engine (REASON)</h2>
              
              {result.causal_results?.narrative && (
                <p className="text-gray-300 bg-gray-800/40 p-4 rounded-lg border-l-4 border-purple-500 text-sm leading-relaxed">
                  {result.causal_results.narrative}
                </p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {result.causal_results?.attributions && (
                  <CausalAttributionChart attributions={result.causal_results.attributions} />
                )}
                {result.causal_results?.attributions && result.primary_diagnosis && (
                  <CausalGraphViz 
                    attributions={result.causal_results.attributions} 
                    primaryDiagnosis={result.primary_diagnosis}
                    dotString={result.causal_results.causal_graph_dot || ""} 
                  />
                )}
              </div>

              {result.causal_results?.counterfactuals?.[0] && (
                <CounterfactualCard 
                  explanation={result.causal_results.counterfactuals[0]} 
                  originalProbability={result.confidence_score || 0.8} 
                />
              )}
            </section>

            {/* US3: Health Trajectory */}
            <section className="space-y-4">
              <h2 className="text-xl font-bold text-white border-b border-gray-800 pb-2">3. Digital Twin (PROJECT)</h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <div className="lg:col-span-2">
                  {result.twin_trajectory && (
                    <TrajectoryChart 
                      trajectory={result.twin_trajectory} 
                      showIntervention={showIntervention}
                      showConfidence={showConfidence}
                    />
                  )}
                </div>
                <div className="space-y-4">
                  <TrajectoryControls 
                    showIntervention={showIntervention} setShowIntervention={setShowIntervention}
                    showConfidence={showConfidence} setShowConfidence={setShowConfidence}
                    horizon={horizon} setHorizon={setHorizon}
                  />
                  {result.twin_trajectory && (
                    <DigitalTwinSummary trajectory={result.twin_trajectory} />
                  )}
                </div>
              </div>
            </section>
            
            {/* US4: Interventions */}
            <section className="space-y-4">
              <h2 className="text-xl font-bold text-white border-b border-gray-800 pb-2">4. Interventions (ACT)</h2>
              
              {result.intervention_plan?.active_uncertainty_reduction && (
                <ActiveUncertaintyReduction recommendation={result.intervention_plan.active_uncertainty_reduction} />
              )}

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="lg:col-span-1">
                  {result.intervention_plan && (
                    <InterventionPlanDisplay plan={result.intervention_plan} />
                  )}
                </div>
                <div className="lg:col-span-1">
                  {result.intervention_plan?.pareto_options && (
                    <ParetoChart options={result.intervention_plan.pareto_options} />
                  )}
                </div>
              </div>
            </section>

          </div>
        </div>

      </div>
    </div>
  );
}
