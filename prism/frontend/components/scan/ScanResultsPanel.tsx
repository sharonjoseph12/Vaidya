"use client";

import { useRouter } from "next/navigation";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import type { DiagnosticResult } from "@/lib/types";
import { getVitalStatus, getRiskColor, DISEASE_LABELS } from "@/lib/utils";

interface ScanResultsPanelProps {
    result: DiagnosticResult | null;
    sessionId: string;
    onScanAgain: () => void;
    error?: string;
}

function StatusChip({ status }: { status: "normal" | "warning" | "critical" | "unreliable" }) {
    const config = {
        normal: "bg-green-500/20 text-green-400 border-green-500/40",
        warning: "bg-amber-500/20 text-amber-400 border-amber-500/40",
        critical: "bg-red-500/20 text-red-400 border-red-500/40",
        unreliable: "bg-gray-500/20 text-gray-400 border-gray-500/40",
    };
    const labels = {
        normal: "Normal",
        warning: "Warning",
        critical: "Critical",
        unreliable: "⚠ Unreliable",
    };
    return (
        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${config[status]}`}>
            {labels[status]}
        </span>
    );
}

function VitalCard({
    label,
    value,
    unit,
    metric,
}: {
    label: string;
    value: number | undefined;
    unit: string;
    metric: "hr" | "spo2" | "hrv" | "rr";
}) {
    if (value === undefined || value === null) {
        return (
            <div
                className="rounded-xl p-3 border"
                style={{ background: "var(--surface-hover)", borderColor: "var(--border)" }}
            >
                <div className="text-xs mb-1" style={{ color: "var(--text-muted)" }}>{label}</div>
                <div className="text-lg font-bold" style={{ color: "var(--text-muted)" }}>—</div>
            </div>
        );
    }
    const status = getVitalStatus(metric, value);
    return (
        <div
            className="rounded-xl p-3 border"
            style={{ background: "var(--surface-hover)", borderColor: "var(--border)" }}
        >
            <div className="text-xs mb-1" style={{ color: "var(--text-secondary)" }}>{label}</div>
            <div className="text-xl font-bold" style={{ color: "var(--text)" }}>
                {value.toFixed(metric === "spo2" ? 1 : 0)}
                <span className="text-xs ml-1" style={{ color: "var(--text-muted)" }}>{unit}</span>
            </div>
            <div className="mt-1">
                <StatusChip status={status} />
            </div>
        </div>
    );
}

export default function ScanResultsPanel({ result, sessionId, onScanAgain, error }: ScanResultsPanelProps) {
    const router = useRouter();

    if (error || !result) {
        return (
            <div className="w-full max-w-2xl glass-card p-6 text-center space-y-4">
                <div className="text-4xl">⚠️</div>
                <h3 className="text-lg font-bold text-red-400">Results Unavailable</h3>
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>{error || "Could not load analysis results."}</p>
                <div className="flex gap-3 justify-center">
                    <button
                        onClick={() => router.push(`/patient/${sessionId}`)}
                        className="px-5 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition text-white"
                    >
                        View Full Report →
                    </button>
                    <button
                        onClick={onScanAgain}
                        className="px-5 py-2 rounded-lg text-sm font-medium transition border"
                        style={{ background: "var(--surface-hover)", borderColor: "var(--border)", color: "var(--text)" }}
                    >
                        Scan Again
                    </button>
                </div>
            </div>
        );
    }

    const rppg = result.sense_results?.rppg;
    const audio = result.sense_results?.audio;
    const visual = result.sense_results?.visual;

    // Top 5 disease probabilities
    const diseaseData = Object.entries(result.disease_probabilities || {})
        .sort(([, a], [, b]) => b - a)
        .slice(0, 5)
        .map(([key, prob]) => ({
            name: DISEASE_LABELS[key] || key,
            probability: Math.round(prob * 100),
            color: getRiskColor(prob),
        }));

    return (
        <div className="w-full max-w-2xl space-y-5">
            {/* Header */}
            <div className="glass-card p-4 border-l-4 border-green-500">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="text-lg font-bold" style={{ color: "var(--text)" }}>Analysis Complete</h3>
                        <p className="text-sm mt-0.5" style={{ color: "var(--text-secondary)" }}>
                            Primary: <span className="text-blue-400 font-semibold">
                                {result.primary_diagnosis?.replace(/_/g, " ") || "—"}
                            </span>
                            {result.confidence_score && (
                                <span className="ml-2" style={{ color: "var(--text-muted)" }}>
                                    ({(result.confidence_score * 100).toFixed(0)}% confidence)
                                </span>
                            )}
                        </p>
                    </div>
                    <div className="text-3xl">✅</div>
                </div>
            </div>

            {/* rPPG Vitals */}
            {rppg && (
                <div className="glass-card p-4">
                    <h4 className="text-sm font-semibold uppercase tracking-wide mb-3" style={{ color: "var(--text-secondary)" }}>
                        📡 rPPG Vitals
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <VitalCard label="Heart Rate" value={rppg.hr} unit="bpm" metric="hr" />
                        <VitalCard label="SpO₂" value={rppg.spo2} unit="%" metric="spo2" />
                        <VitalCard label="HRV (RMSSD)" value={rppg.hrv_rmssd} unit="ms" metric="hrv" />
                        <VitalCard label="Resp. Rate" value={rppg.rr} unit="br/min" metric="rr" />
                    </div>
                </div>
            )}

            {/* Audio Results */}
            {audio && (
                <div className="glass-card p-4">
                    <h4 className="text-sm font-semibold uppercase tracking-wide mb-3" style={{ color: "var(--text-secondary)" }}>
                        🎤 Acoustic Analysis
                    </h4>
                    <div className="flex flex-wrap gap-3">
                        <div
                            className="rounded-xl px-4 py-2 border"
                            style={{ background: "var(--surface-hover)", borderColor: "var(--border)" }}
                        >
                            <div className="text-xs" style={{ color: "var(--text-secondary)" }}>Coughs Detected</div>
                            <div className="text-2xl font-bold" style={{ color: "var(--text)" }}>{audio.cough_count}</div>
                        </div>
                        <div className={`rounded-xl px-4 py-2 border ${audio.wheeze_detected ? "bg-amber-500/10 border-amber-500/30" : ""}`}
                            style={!audio.wheeze_detected ? { background: "var(--surface-hover)", borderColor: "var(--border)" } : undefined}
                        >
                            <div className="text-xs" style={{ color: "var(--text-secondary)" }}>Wheeze</div>
                            <div className={`text-sm font-bold ${audio.wheeze_detected ? "text-amber-400" : ""}`}
                                style={!audio.wheeze_detected ? { color: "var(--text-muted)" } : undefined}
                            >
                                {audio.wheeze_detected ? "Detected ⚠" : "Not detected"}
                            </div>
                        </div>
                        <div className={`rounded-xl px-4 py-2 border ${audio.crackle_detected ? "bg-amber-500/10 border-amber-500/30" : ""}`}
                            style={!audio.crackle_detected ? { background: "var(--surface-hover)", borderColor: "var(--border)" } : undefined}
                        >
                            <div className="text-xs" style={{ color: "var(--text-secondary)" }}>Crackle</div>
                            <div className={`text-sm font-bold ${audio.crackle_detected ? "text-amber-400" : ""}`}
                                style={!audio.crackle_detected ? { color: "var(--text-muted)" } : undefined}
                            >
                                {audio.crackle_detected ? "Detected ⚠" : "Not detected"}
                            </div>
                        </div>
                        {audio.breathing_rate && (
                            <div
                                className="rounded-xl px-4 py-2 border"
                                style={{ background: "var(--surface-hover)", borderColor: "var(--border)" }}
                            >
                                <div className="text-xs" style={{ color: "var(--text-secondary)" }}>Breathing Rate</div>
                                <div className="text-sm font-bold" style={{ color: "var(--text)" }}>{audio.breathing_rate.toFixed(0)} br/min</div>
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Visual Scores */}
            {visual && (
                <div className="glass-card p-4">
                    <h4 className="text-sm font-semibold uppercase tracking-wide mb-3" style={{ color: "var(--text-secondary)" }}>
                        👁 Visual Biomarkers
                    </h4>
                    <div className="space-y-2">
                        {[
                            { label: "Jaundice Score", value: visual.jaundice_score, color: "bg-yellow-500" },
                            { label: "Anemia Score", value: visual.anemia_score, color: "bg-red-400" },
                            { label: "Cyanosis Score", value: visual.cyanosis_score, color: "bg-blue-400" },
                            { label: "Dengue Flush", value: visual.dengue_flush_score, color: "bg-orange-400" },
                        ].map(({ label, value, color }) => (
                            <div key={label}>
                                <div className="flex justify-between text-xs mb-1">
                                    <span style={{ color: "var(--text-secondary)" }}>{label}</span>
                                    <span className="font-medium" style={{ color: "var(--text)" }}>{(value * 100).toFixed(0)}%</span>
                                </div>
                                <div className="h-2 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
                                    <div
                                        className={`h-full ${color} rounded-full transition-all duration-500`}
                                        style={{ width: `${value * 100}%` }}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Disease Probabilities Chart */}
            {diseaseData.length > 0 && (
                <div className="glass-card p-4">
                    <h4 className="text-sm font-semibold uppercase tracking-wide mb-3" style={{ color: "var(--text-secondary)" }}>
                        🧬 Disease Probabilities
                    </h4>
                    <div className="h-40">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={diseaseData} layout="vertical" margin={{ left: 10, right: 30, top: 0, bottom: 0 }}>
                                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: "var(--text-secondary)" }} tickFormatter={(v) => `${v}%`} />
                                <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: "var(--text-secondary)" }} width={110} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: "var(--surface)", borderColor: "var(--border)", borderRadius: "8px", fontSize: "12px" }}
                                    formatter={(v) => [`${v}%`, "Probability"]}
                                />
                                <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
                                    {diseaseData.map((entry, i) => (
                                        <Cell key={i} fill={entry.color} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
                <button
                    onClick={() => router.push(`/patient/${sessionId}`)}
                    className="flex-1 py-3 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-xl font-semibold text-white hover:shadow-lg hover:shadow-blue-500/25 transition-all"
                >
                    View Full Report →
                </button>
                <button
                    onClick={onScanAgain}
                    className="px-6 py-3 rounded-xl font-medium transition border"
                    style={{ background: "var(--surface-hover)", borderColor: "var(--border)", color: "var(--text)" }}
                >
                    Scan Again
                </button>
            </div>
        </div>
    );
}
