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
