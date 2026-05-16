/**
 * PRISM Platform — Utility Functions
 * Color scales, formatting helpers, and shared utilities.
 */

/**
 * Get color for a disease probability value.
 * Green (low risk) → Amber (medium) → Red (high risk)
 */
export function getRiskColor(probability: number): string {
  if (probability >= 0.7) return "#ef4444"; // Red - high risk
  if (probability >= 0.4) return "#f59e0b"; // Amber - medium risk
  if (probability >= 0.2) return "#06b6d4"; // Cyan - low-medium
  return "#22c55e"; // Green - low risk
}

/**
 * Get risk level label from probability.
 */
export function getRiskLevel(probability: number): string {
  if (probability >= 0.8) return "Critical";
  if (probability >= 0.6) return "High";
  if (probability >= 0.4) return "Moderate";
  if (probability >= 0.2) return "Low";
  return "Minimal";
}

/**
 * Format a probability as a percentage string.
 */
export function formatPercent(value: number, decimals = 0): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format a date string to locale-friendly display.
 */
export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Format milliseconds to human-readable duration.
 */
export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${Math.floor(ms / 60000)}m ${Math.round((ms % 60000) / 1000)}s`;
}

/**
 * Format currency in Indian Rupees.
 */
export function formatCurrency(amount: number): string {
  if (amount === 0) return "₹0 FREE";
  return `₹${amount.toLocaleString("en-IN")}`;
}

/**
 * Interpolate between two colors based on a value [0, 1].
 */
export function interpolateColor(value: number): string {
  const r = Math.round(34 + (239 - 34) * value);
  const g = Math.round(197 - (197 - 68) * value);
  const b = Math.round(94 - (94 - 68) * value);
  return `rgb(${r}, ${g}, ${b})`;
}

/**
 * Truncate a string with ellipsis.
 */
export function truncate(str: string, maxLength: number): string {
  return str.length > maxLength ? str.slice(0, maxLength) + "..." : str;
}

/**
 * Disease display names (mapping from backend keys).
 */
export const DISEASE_LABELS: Record<string, string> = {
  TB: "Tuberculosis",
  Pneumonia: "Pneumonia",
  Anemia: "Anemia",
  Asthma: "Asthma",
  COPD: "COPD",
  Dengue: "Dengue",
  Cardiac_Risk: "Cardiac Risk",
  Jaundice: "Jaundice / Hepatitis",
};

/**
 * Government health scheme display names.
 */
export const SCHEME_LABELS: Record<string, string> = {
  RNTCP: "RNTCP (TB Control)",
  ICDS: "ICDS (Nutrition)",
  "AB-PMJAY": "Ayushman Bharat",
  DOTS: "DOTS (TB Treatment)",
  NRHM: "National Rural Health Mission",
};

/**
 * High if sessions_count >= 10, Medium if >= 4, Low otherwise.
 */
export function deriveRiskLevel(patient: { sessions_count?: number }): "high" | "medium" | "low" {
  const count = patient.sessions_count ?? 0;
  if (count >= 10) return "high";
  if (count >= 4) return "medium";
  return "low";
}

/**
 * Sanitize a field value to prevent CSV injection.
 * Strips leading =, +, -, @ characters from string fields.
 */
function sanitizeCsvField(value: string): string {
  return value.replace(/^[=+\-@]/, "");
}

/**
 * Wrap a CSV field in quotes if it contains commas, quotes, or newlines.
 */
function escapeCsvField(value: string): string {
  const sanitized = sanitizeCsvField(value);
  if (sanitized.includes(",") || sanitized.includes('"') || sanitized.includes("\n")) {
    return `"${sanitized.replace(/"/g, '""')}"`;
  }
  return sanitized;
}

/**
 * Generate a CSV string from a list of patients.
 * Includes a header row and sanitized data rows.
 */
export function generatePatientCSV(patients: import("./types").Patient[]): string {
  const header = ["ID", "ABHA ID", "Name", "Age", "Sex", "Location", "Sessions", "Last Scan", "Risk Level"];
  const rows = patients.map((p) => {
    const name = p.demographics?.name ?? "";
    const age = p.demographics?.age != null ? String(p.demographics.age) : "";
    const sex = p.demographics?.sex ?? "";
    const location = p.demographics?.location ?? "";
    const risk = deriveRiskLevel(p);
    return [
      escapeCsvField(p.id),
      escapeCsvField(p.abha_id ?? ""),
      escapeCsvField(name),
      age,
      sex,
      escapeCsvField(location),
      String(p.sessions_count),
      escapeCsvField(p.last_session_date ?? ""),
      risk,
    ].join(",");
  });
  return [header.join(","), ...rows].join("\n");
}

/**
 * Get vital sign status based on clinical thresholds and physiological validity ranges.
 */
export function getVitalStatus(
  metric: "hr" | "spo2" | "hrv" | "rr",
  value: number,
): "normal" | "warning" | "critical" | "unreliable" {
  // Physiological validity ranges — outside these, value is unreliable
  const physioRanges: Record<string, [number, number]> = {
    hr: [20, 300],
    spo2: [50, 100],
    hrv: [0, 300],
    rr: [4, 60],
  };

  const [physioMin, physioMax] = physioRanges[metric];
  if (value < physioMin || value > physioMax) return "unreliable";

  switch (metric) {
    case "hr":
      if (value >= 60 && value <= 100) return "normal";
      if ((value >= 50 && value < 60) || (value > 100 && value <= 120)) return "warning";
      return "critical";
    case "spo2":
      if (value >= 95) return "normal";
      if (value >= 90) return "warning";
      return "critical";
    case "hrv":
      if (value >= 20 && value <= 80) return "normal";
      if ((value >= 10 && value < 20) || (value > 80 && value <= 120)) return "warning";
      return "critical";
    case "rr":
      if (value >= 12 && value <= 20) return "normal";
      if ((value >= 8 && value < 12) || (value > 20 && value <= 25)) return "warning";
      return "critical";
    default:
      return "unreliable";
  }
}

/** Loose UUID check for routing (patient and session IDs from the API). */
export function isUuid(value: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value.trim());
}
