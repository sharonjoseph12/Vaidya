/**
 * PRISM Platform — TypeScript Type Definitions
 * Mirrors all backend Pydantic schemas for type-safe frontend development.
 */

// ============================================================
// Patient Types
// ============================================================

export interface Demographics {
  name: string;
  age: number;
  sex: "M" | "F" | "O";
  location: string;
  socioeconomic_tier?: string;
}

export interface PatientCreate {
  abha_id?: string;
  demographics: Demographics;
  consent_given: boolean;
  consent_purpose?: string;
  device_info?: Record<string, unknown>;
}

export interface Patient {
  id: string;
  abha_id?: string;
  created_at: string;
  consent_given: boolean;
  demographics?: Demographics;
  /** Omitted on some list responses; treat as 0 when missing. */
  sessions_count?: number;
  last_session_date?: string;
}

export interface PatientList {
  patients: Patient[];
  total: number;
  page: number;
  per_page: number;
}

// ============================================================
// Layer 1: SENSE
// ============================================================

export interface RPPGResult {
  hr: number;
  spo2: number;
  hrv_rmssd: number;
  hrv_sdnn?: number;
  lf_hf_ratio?: number;
  rr: number;
  confidence?: Record<string, number>;
}

export interface AudioResult {
  cough_detected: boolean;
  cough_count: number;
  disease_probs: Record<string, number>;
  breathing_rate?: number;
  wheeze_detected: boolean;
  crackle_detected: boolean;
}

export interface VisualResult {
  jaundice_score: number;
  anemia_score: number;
  cyanosis_score: number;
  dengue_flush_score: number;
  pallor_score: number;
}

export interface SenseResult {
  disease_probabilities: Record<string, number>;
  rppg?: RPPGResult;
  audio?: AudioResult;
  visual?: VisualResult;
  uncertainty: Record<string, [number, number]>;
  modalities_available: string[];
  processing_time_ms: number;
}

// ============================================================
// Layer 2: REASON
// ============================================================

export interface CounterfactualExplanation {
  changes: Record<string, [number, number]>;
  new_probability: number;
  feasibility_score: number;
  n_features_changed: number;
}

export interface CausalResult {
  attributions: Record<string, number>;
  top_intervention?: string;
  intervention_effects: Record<string, number>;
  patient_risk_factors: Record<string, number>;
  counterfactuals: CounterfactualExplanation[];
  narrative: string;
  causal_graph_dot: string;
}

// ============================================================
// Layer 3: PROJECT (Digital Twin)
// ============================================================

export interface TrajectoryPoint {
  month: number;
  values: Record<string, number>;
}

export interface TwinTrajectory {
  without_intervention: TrajectoryPoint[];
  with_best_intervention: TrajectoryPoint[];
  confidence_bands: Record<string, [number, number]>;
  months_to_critical?: number;
  months_to_critical_with_intervention?: number;
  intervention_applied?: string;
  twin_model_version?: string;
}

// ============================================================
// Layer 4: ACT (Intervention)
// ============================================================

export interface InterventionRecommendation {
  rank: number;
  intervention: string;
  description: string;
  rationale: string;
  cost_govt: number;
  cost_private: number;
  qaly_gain: number;
  cost_per_qaly: number;
  time_to_effect_days: number;
  side_effect_risk: number;
  nearest_facility?: { name: string; distance_km: number; address: string };
  scheme?: string;
}

export interface ParetoOption {
  label: string;
  cost: number;
  qaly_gain: number;
  risk: number;
}

export interface TestRecommendation {
  recommended_test: string;
  cost: number;
  expected_uncertainty_reduction: number;
  rationale: string;
}

export interface InterventionPlan {
  recommendations: InterventionRecommendation[];
  pareto_options: ParetoOption[];
  active_uncertainty_reduction?: TestRecommendation;
}

// ============================================================
// Full Diagnostic Result
// ============================================================

/** In-flight session payload from GET /diagnostics/results/{id} (before FullDiagnosticResult is ready). */
export interface DiagnosticSessionPending {
  session_id: string;
  status: string;
  message: string;
}

export interface DiagnosticResult {
  session_id: string;
  status: string;
  primary_diagnosis?: string;
  confidence_score?: number;
  disease_probabilities: Record<string, number>;
  sense_results?: SenseResult;
  causal_results?: CausalResult;
  twin_trajectory?: TwinTrajectory;
  intervention_plan?: InterventionPlan;
  uncertainty_bounds: Record<string, [number, number]>;
  processing_time_ms: number;
  model_version?: string;
  offline_mode: boolean;
}

export function isCompleteDiagnosticPayload(
  data: DiagnosticResult | DiagnosticSessionPending,
): data is DiagnosticResult {
  return typeof data === "object" && data !== null && "disease_probabilities" in data;
}

export interface AnalysisStartResponse {
  session_id: string;
  task_id: string;
  status: string;
  estimated_time_seconds: number;
}

export interface AnalysisProgressEvent {
  stage: string;
  progress: number;
  message: string;
  session_id?: string;
}

// ============================================================
// ABDM Types
// ============================================================

export interface ABHAProfile {
  verified: boolean;
  name: string;
  age: number;
  gender: string;
  abha_address?: string;
}

export interface HealthRecord {
  type: string;
  date: string;
  findings?: string;
  parameter?: string;
  value?: number;
  unit?: string;
  codes: string[];
}

// ============================================================
// Federated Learning Types
// ============================================================

export interface FLStatus {
  server_status: string;
  current_round: number;
  total_nodes: number;
  active_nodes: number;
  global_model_version: string;
  cumulative_dp_epsilon: number;
  last_round_metrics?: Record<string, number>;
}

export interface FLRound {
  round_number: number;
  participating_nodes: number;
  rejected_nodes: number;
  metrics?: Record<string, number>;
  dp_epsilon_spent: number;
  completed_at?: string;
}
