/**
 * PRISM Platform — API Client
 * Fetch wrappers with auth, error handling, and SSE streaming support.
 */

import type {
  ABHAProfile,
  AnalysisProgressEvent,
  AnalysisStartResponse,
  DiagnosticResult,
  DiagnosticSessionPending,
  FLRound,
  FLStatus,
  Patient,
  PatientList,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

/** FastAPI returns `detail` as string, object, or validation error array. */
function formatApiDetail(detail: unknown): string {
  if (detail == null) return "Request failed";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        try {
          return JSON.stringify(item);
        } catch {
          return String(item);
        }
      })
      .join("; ");
  }
  if (typeof detail === "object") {
    try {
      return JSON.stringify(detail);
    } catch {
      return "Request failed";
    }
  }
  return String(detail);
}

function getAuthHeaders(): HeadersInit {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("prism_token") || "DEMO_TOKEN";
  return { Authorization: `Bearer ${token}` };
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
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
    throw new ApiError(res.status, formatApiDetail(body.detail ?? res.statusText));
  }

  return res.json();
}

// ============================================================
// Patient APIs
// ============================================================

export async function getPatients(page = 1, perPage = 20): Promise<PatientList> {
  return request(`/patients?page=${page}&per_page=${perPage}`);
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

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, formatApiDetail(body.detail ?? "Failed to start analysis"));
  }
  return res.json();
}

export async function getResults(
  sessionId: string,
): Promise<DiagnosticResult | DiagnosticSessionPending> {
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

export async function downloadReport(sessionId: string): Promise<Blob> {
  const token = localStorage.getItem("prism_token") || "DEMO_TOKEN";
  const res = await fetch(`${API_BASE}/diagnostics/report/${sessionId}/pdf`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new ApiError(res.status, "Failed to download report");
  return res.blob();
}

// ============================================================
// ABDM APIs
// ============================================================

export async function verifyABHA(abhaId: string): Promise<ABHAProfile> {
  return request(`/abdm/verify/${abhaId}`, { method: "POST" });
}

export async function fetchHealthHistory(abhaId: string, dateFrom: string, dateTo: string): Promise<unknown> {
  return request("/abdm/fetch-history", {
    method: "POST",
    body: JSON.stringify({ abha_id: abhaId, date_from: dateFrom, date_to: dateTo }),
  });
}

export async function pushReportToABDM(sessionId: string, abhaId: string): Promise<unknown> {
  return request("/abdm/push-report", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, abha_id: abhaId }),
  });
}

// ============================================================
// FL APIs
// ============================================================

export async function getFLStatus(): Promise<FLStatus> {
  return request("/federated/status");
}

export async function getFLRounds(limit = 20): Promise<{ rounds: FLRound[] }> {
  return request(`/federated/rounds?limit=${limit}`);
}
