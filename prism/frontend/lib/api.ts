import type { AnalysisProgressEvent, AnalysisStartResponse, AuditLogResponse, DiagnosticResult, FLNode, FLRound, FLStatus, HealthStatus, ModelVersion, Patient, PatientList, PendingReview, RecentSession, SessionSummary } from "./types";
import { offlineStore } from "./offline-store";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

function getAuthHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("prism_token") || "DEMO_TOKEN";
  return { Authorization: `Bearer ${token}` };
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
        ...options.headers,
      },
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: res.statusText }));
      throw new ApiError(res.status, body.detail || res.statusText);
    }

    offlineStore.setOffline(false); // Backend reachable
    return res.json();
  } catch (err) {
    if (err instanceof TypeError && err.message.includes("fetch")) {
      // Network failure — backend unreachable
      offlineStore.setOffline(true);
    }
    throw err;
  }
}


// ============================================================
// Patient APIs
// ============================================================

export async function getPatients(
  page = 1,
  perPage = 20,
  search?: string,
  riskLevel?: string,
  sortField?: string,
  sortDir?: "asc" | "desc",
): Promise<PatientList> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  });
  if (search) params.set("search", search);
  if (riskLevel) params.set("risk_level", riskLevel);
  if (sortField) params.set("sort_field", sortField);
  if (sortDir) params.set("sort_dir", sortDir);
  return request(`/patients?${params.toString()}`);
}

export async function getPatient(id: string): Promise<Patient> {
  return request(`/patients/${id}`);
}

export async function createPatient(data: Record<string, unknown>): Promise<Patient> {
  return request("/patients", { method: "POST", body: JSON.stringify(data) });
}

// ============================================================
// Diagnostics APIs
// ============================================================

export async function startAnalysis(
  patientId: string,
  audioFile?: File,
  videoFile?: File,
  features?: Record<string, unknown>,
): Promise<AnalysisStartResponse> {
  const formData = new FormData();
  formData.append("patient_id", patientId);
  formData.append("patient_features", JSON.stringify(features || {}));
  if (audioFile) formData.append("audio_file", audioFile);
  if (videoFile) formData.append("video_file", videoFile);

  const res = await fetch(`${API_BASE}/diagnostics/analyze`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: formData,
  });

  if (!res.ok) throw new ApiError(res.status, "Failed to start analysis");
  return res.json();
}

export async function getResults(sessionId: string): Promise<DiagnosticResult> {
  return request(`/diagnostics/results/${sessionId}`);
}

export function subscribeToProgress(
  sessionId: string,
  onEvent: (event: AnalysisProgressEvent) => void,
  onError?: (error: Event) => void,
): EventSource {
  const es = new EventSource(`${API_BASE}/diagnostics/stream/${sessionId}`);
  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data) as AnalysisProgressEvent;
      onEvent(data);
      if (data.stage === "complete" || data.stage === "error") es.close();
    } catch { /* ignore parse errors */ }
  };
  es.onerror = (e) => {
    onError?.(e);
    es.close();
  };
  return es;
}

// ============================================================
// ABDM APIs
// ============================================================

export async function verifyABHA(abhaId: string) {
  return request(`/abdm/verify/${abhaId}`, { method: "POST" });
}

export async function fetchHealthHistory(abhaId: string, dateFrom: string, dateTo: string) {
  return request("/abdm/fetch-history", {
    method: "POST",
    body: JSON.stringify({ abha_id: abhaId, date_from: dateFrom, date_to: dateTo }),
  });
}

export async function pushReportToABDM(sessionId: string, abhaId: string) {
  return request("/abdm/push-report", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, abha_id: abhaId }),
  });
}

// ============================================================
// FL APIs
// ============================================================

export async function getFLStatus(): Promise<FLStatus> {
  return request<FLStatus>("/federated/status");
}

export async function getFLRounds(limit = 20): Promise<FLRound[] | { rounds: FLRound[] }> {
  return request<FLRound[] | { rounds: FLRound[] }>(`/federated/rounds?limit=${limit}`);
}

export async function getFLNodes(): Promise<FLNode[]> {
  return request<FLNode[]>("/federated/nodes");
}

export async function getModelVersionHistory(): Promise<ModelVersion[]> {
  return request<ModelVersion[]>("/federated/model-versions");
}

export async function triggerFLRound(minNodes: number): Promise<{ round_number: number; status: string }> {
  return request<{ round_number: number; status: string }>("/federated/trigger-round", {
    method: "POST",
    body: JSON.stringify({ min_nodes: minNodes }),
  });
}

// ============================================================
// Session / Health APIs
// ============================================================

export async function getRecentSessions(limit = 5): Promise<RecentSession[]> {
  return request<RecentSession[]>(`/diagnostics/recent-sessions?limit=${limit}`);
}

export async function healthCheck(): Promise<HealthStatus> {
  const start = Date.now();
  const result = await request<HealthStatus>("/health");
  return { ...result, latency_ms: Date.now() - start };
}

export async function getPatientSessions(patientId: string): Promise<SessionSummary[]> {
  return request<SessionSummary[]>(`/patients/${patientId}/sessions`);
}

export async function getPendingReviews(): Promise<PendingReview[]> {
  return request<PendingReview[]>("/diagnostics/pending-review");
}

export async function submitReview(
  sessionId: string,
  approved: boolean,
  overrideDiagnosis?: string,
  notes?: string,
): Promise<{ status: string }> {
  return request<{ status: string }>(`/diagnostics/review/${sessionId}`, {
    method: "POST",
    body: JSON.stringify({ approved, override_diagnosis: overrideDiagnosis, notes }),
  });
}

export async function getAuditLog(page = 1, limit = 20): Promise<AuditLogResponse> {
  return request<AuditLogResponse>(`/audit/log?page=${page}&limit=${limit}`);
}
