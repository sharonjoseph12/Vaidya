"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getResults, getPatient } from "@/lib/api";
import type { DiagnosticResult, Patient } from "@/lib/types";

import DiseaseProbabilityCard from "@/components/results/DiseaseProbabilityCard";
import UncertaintyBands from "@/components/results/UncertaintyBands";
import CausalGraphViz from "@/components/results/CausalGraphViz";
import CausalAttributionChart from "@/components/results/CausalAttributionChart";
import CounterfactualCard from "@/components/results/CounterfactualCard";
import TrajectoryChart from "@/components/results/TrajectoryChart";
import TrajectoryControls from "@/components/results/TrajectoryControls";
import DigitalTwinSummary from "@/components/results/DigitalTwinSummary";
import InterventionPlanDisplay from "@/components/results/InterventionPlan";
import ParetoChart from "@/components/results/ParetoChart";
import ActiveUncertaintyReduction from "@/components/results/ActiveUncertaintyReduction";
import SessionComparison from "@/components/results/SessionComparison";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

function getAuthHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("prism_token") || "DEMO_TOKEN";
  return { Authorization: `Bearer ${token}` };
}

type ActiveTab = "results" | "compare";

export default function PatientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [result, setResult] = useState<DiagnosticResult | null>(null);
  const [patient, setPatient] = useState<Patient | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [abdmStatus, setAbdmStatus] = useState<"idle" | "pushing" | "success" | "error">("idle");
  const [pdfStatus, setPdfStatus] = useState<"idle" | "loading" | "error">("idle");
  const [activeTab, setActiveTab] = useState<ActiveTab>("results");
  const [showIntervention, setShowIntervention] = useState(true);
  const [showConfidence, setShowConfidence] = useState(true);
  const [horizon, setHorizon] = useState(12);

  useEffect(() => {
    async function loadData() {
      try {
        const [resultsSettled, patientSettled] = await Promise.allSettled([
          getResults(id),
          getPatient(id),
        ]);
        if (resultsSettled.status === "fulfilled") {
          setResult(resultsSettled.value);
        } else {
          setError((resultsSettled.reason as Error)?.message || "Failed to load results");
        }
        if (patientSettled.status === "fulfilled") {
          setPatient(patientSettled.value);
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load results");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [id]);

  const handlePushToABDM = async () => {
    setAbdmStatus("pushing");
    try {
      const res = await fetch(`${API_BASE}/abdm/push-report`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify({ patient_id: id, report_data: result }),
      });
      if (!res.ok) throw new Error("Failed to push to ABDM");
      setAbdmStatus("success");
      setTimeout(() => setAbdmStatus("idle"), 3000);
    } catch (err) {
      console.error(err);
      setAbdmStatus("error");
      setTimeout(() => setAbdmStatus("idle"), 3000);
    }
  };

  const handleDownloadPDF = async () => {
    setPdfStatus("loading");
    try {
      const res = await fetch(`${API_BASE}/diagnostics/report/${id}/pdf`, {
        headers: getAuthHeaders(),
      });
      if (!res.ok) throw new Error("PDF generation failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `prism_report_${id.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      setPdfStatus("idle");
    } catch (err) {
      console.error(err);
      setPdfStatus("error");
      setTimeout(() => setPdfStatus("idle"), 3000);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center gradient-bg">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gradient-bg">
        <div className="text-4xl mb-4">⚠️</div>
        <h2 className="text-xl font-bold text-red-600">Error</h2>
        <p className="text-sm mt-2" style={{ color: "var(--text-secondary)" }}>{error || "Results not found"}</p>
        <button
          onClick={() => router.push("/dashboard")}
          className="mt-6 px-6 py-2 rounded-lg hover:opacity-80 transition text-sm border"
          style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text)" }}
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  const hasEmptyDiseaseProbs = Object.keys(result.disease_probabilities || {}).length === 0;

  return (
    <div className="min-h-screen gradient-bg p-6 md:p-10 font-sans" style={{ color: "var(--text)" }}>
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 text-sm" style={{ color: "var(--text-muted)" }}>
          <Link href="/patients" className="hover:text-blue-600 transition-colors">
            ← Patients
          </Link>
          <span>/</span>
          <span className="font-mono" style={{ color: "var(--text-muted)" }}>{id.split("-")[0]}</span>
        </nav>

        {/* Header */}
        <header className="glass-card p-6">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
              <h1 className="text-xl font-bold flex items-center gap-3" style={{ color: "var(--text)" }}>
                Patient Assessment
                <span className="text-sm font-normal font-mono" style={{ color: "var(--text-muted)" }}>#{id.split("-")[0]}</span>
              </h1>
              {!hasEmptyDiseaseProbs && result.primary_diagnosis && (
                <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
                  Primary Diagnosis:{" "}
                  <span className="text-blue-600 font-semibold">
                    {result.primary_diagnosis.replace(/_/g, " ")}
                  </span>
                </p>
              )}
              {patient?.demographics ? (
                <div className="mt-2 flex flex-wrap gap-3 text-sm" style={{ color: "var(--text-secondary)" }}>
                  {patient.demographics.name && (
                    <span className="font-medium" style={{ color: "var(--text)" }}>{patient.demographics.name}</span>
                  )}
                  {patient.demographics.age && <span>{patient.demographics.age}y</span>}
                  {patient.demographics.sex && <span>{patient.demographics.sex}</span>}
                  {patient.demographics.location && (
                    <span>📍 {patient.demographics.location}</span>
                  )}
                  {patient.abha_id && (
                    <span className="text-blue-600 text-xs font-mono">ABHA: {patient.abha_id}</span>
                  )}
                </div>
              ) : (
                <p className="mt-2 text-sm italic" style={{ color: "var(--text-muted)" }}>Demographics unavailable</p>
              )}
            </div>

            <div className="flex gap-2 flex-wrap print:hidden">
              <button
                onClick={() => router.push(`/scan?patientId=${id}`)}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition shadow-sm"
              >
                📷 New Scan
              </button>
              <button
                onClick={handleDownloadPDF}
                disabled={pdfStatus === "loading"}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition border ${pdfStatus === "error"
                  ? "bg-red-50 border-red-200 text-red-600"
                  : ""
                  }`}
                style={pdfStatus !== "error" ? { background: "var(--surface)", borderColor: "var(--border)", color: "var(--text)" } : undefined}
              >
                {pdfStatus === "loading"
                  ? "⏳ Generating..."
                  : pdfStatus === "error"
                    ? "⚠ Failed"
                    : "📄 Download PDF"}
              </button>
              <button
                onClick={handlePushToABDM}
                disabled={abdmStatus === "pushing" || abdmStatus === "success"}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition shadow-sm ${abdmStatus === "success"
                  ? "bg-green-600 text-white"
                  : abdmStatus === "error"
                    ? "bg-red-600 text-white"
                    : "bg-blue-600 hover:bg-blue-700 text-white"
                  }`}
              >
                ☁️{" "}
                {abdmStatus === "pushing"
                  ? "Pushing..."
                  : abdmStatus === "success"
                    ? "Pushed!"
                    : abdmStatus === "error"
                      ? "Failed"
                      : "Push to ABDM"}
              </button>
            </div>
          </div>
        </header>

        {/* Model unavailable banner */}
        {hasEmptyDiseaseProbs && (
          <div className="glass-card p-4 bg-amber-50 border border-amber-200 flex items-start gap-3">
            <span className="text-amber-500 text-lg mt-0.5">⚠</span>
            <div>
              <p className="text-amber-800 font-medium text-sm">
                Disease analysis pending model integration
              </p>
              <p className="text-amber-600 text-xs mt-0.5">
                The AI diagnostic models are not yet integrated. Vital signs (rPPG) are shown where
                available. Disease probabilities will appear once the Layer 1 models are deployed.
              </p>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 border-b" style={{ borderColor: "var(--border)" }}>
          {(["results", "compare"] as ActiveTab[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-2.5 text-sm font-medium transition-all border-b-2 -mb-px ${activeTab === tab
                ? "border-blue-600 text-blue-600"
                : "border-transparent"
                }`}
              style={activeTab !== tab ? { color: "var(--text-secondary)" } : undefined}
            >
              {tab === "results" ? "📋 Results" : "📊 Compare Scans"}
            </button>
          ))}
        </div>

        {/* Results Tab */}
        {activeTab === "results" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Diagnostics */}
            <div className="lg:col-span-1 space-y-5">
              <h2 className="text-base font-bold border-b pb-2" style={{ color: "var(--text)", borderColor: "var(--border)" }}>
                1. Diagnostics (SENSE)
              </h2>

              {hasEmptyDiseaseProbs ? (
                <div className="glass-card p-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>
                  <div className="text-3xl mb-2">🔬</div>
                  <p>No disease probabilities available yet.</p>
                  <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                    Awaiting Layer 1 model integration.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {Object.entries(result.disease_probabilities || {})
                    .slice(0, 4)
                    .map(([disease, prob]) => (
                      <DiseaseProbabilityCard
                        key={disease}
                        disease={disease}
                        probability={prob}
                        confidenceInterval={result.uncertainty_bounds?.[disease]}
                      />
                    ))}
                </div>
              )}

              {result.uncertainty_bounds &&
                Object.keys(result.uncertainty_bounds).length > 0 && (
                  <UncertaintyBands uncertainties={result.uncertainty_bounds} />
                )}
            </div>

            {/* Right: Causality, Trajectory, Interventions */}
            <div className="lg:col-span-2 space-y-6">
              {/* Causal Engine */}
              <section className="space-y-4">
                <h2 className="text-base font-bold border-b pb-2" style={{ color: "var(--text)", borderColor: "var(--border)" }}>
                  2. Causal Engine (REASON)
                </h2>
                {result.causal_results?.narrative && (
                  <p className="bg-purple-50 border border-purple-200 border-l-4 border-l-purple-500 p-4 rounded-xl text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                    {result.causal_results.narrative}
                  </p>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {result.causal_results?.attributions && (
                    <CausalAttributionChart
                      attributions={result.causal_results.attributions}
                    />
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

              {/* Digital Twin */}
              <section className="space-y-4">
                <h2 className="text-base font-bold border-b pb-2" style={{ color: "var(--text)", borderColor: "var(--border)" }}>
                  3. Digital Twin (PROJECT)
                </h2>
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
                      showIntervention={showIntervention}
                      setShowIntervention={setShowIntervention}
                      showConfidence={showConfidence}
                      setShowConfidence={setShowConfidence}
                      horizon={horizon}
                      setHorizon={setHorizon}
                    />
                    {result.twin_trajectory && (
                      <DigitalTwinSummary trajectory={result.twin_trajectory} />
                    )}
                  </div>
                </div>
              </section>

              {/* Interventions */}
              <section className="space-y-4">
                <h2 className="text-base font-bold border-b pb-2" style={{ color: "var(--text)", borderColor: "var(--border)" }}>
                  4. Interventions (ACT)
                </h2>
                {result.intervention_plan?.active_uncertainty_reduction && (
                  <ActiveUncertaintyReduction
                    recommendation={result.intervention_plan.active_uncertainty_reduction}
                  />
                )}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                  {result.intervention_plan && (
                    <InterventionPlanDisplay plan={result.intervention_plan} />
                  )}
                  {result.intervention_plan?.pareto_options && (
                    <ParetoChart options={result.intervention_plan.pareto_options} />
                  )}
                </div>
              </section>
            </div>
          </div>
        )}

        {/* Compare Tab */}
        {activeTab === "compare" && patient && (
          <SessionComparison patientId={patient.id} />
        )}
        {activeTab === "compare" && !patient && (
          <div className="glass-card p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            Patient data unavailable for comparison.
          </div>
        )}
      </div>
    </div>
  );
}
