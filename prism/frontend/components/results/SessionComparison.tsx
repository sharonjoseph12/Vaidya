"use client";

import { useEffect, useState } from "react";
import { getPatientSessions } from "@/lib/api";
import type { SessionSummary } from "@/lib/types";
import { formatDate, formatPercent, DISEASE_LABELS } from "@/lib/utils";

interface SessionComparisonProps {
    patientId: string;
}

function DeltaBadge({ delta, unit = "%" }: { delta: number; unit?: string }) {
    if (Math.abs(delta) < 0.001) return <span className="text-xs" style={{ color: "var(--text-muted)" }}>→ no change</span>;
    const isPositive = delta > 0;
    return (
        <span className={`text-xs font-medium ${isPositive ? "text-red-600" : "text-green-600"}`}>
            {isPositive ? "▲" : "▼"} {Math.abs(delta).toFixed(1)}{unit}
        </span>
    );
}

function VitalRow({ label, a, b, unit, lowerIsBetter = false }: {
    label: string;
    a?: number | null;
    b?: number | null;
    unit: string;
    lowerIsBetter?: boolean;
}) {
    const delta = (a != null && b != null) ? b - a : null;
    return (
        <div className="flex items-center justify-between py-2 border-b last:border-0 text-sm" style={{ borderColor: "var(--border)" }}>
            <span className="w-28" style={{ color: "var(--text-muted)" }}>{label}</span>
            <span className="font-mono w-20 text-right" style={{ color: "var(--text)" }}>{a != null ? `${a.toFixed(1)} ${unit}` : "—"}</span>
            <span className="font-mono w-20 text-right" style={{ color: "var(--text)" }}>{b != null ? `${b.toFixed(1)} ${unit}` : "—"}</span>
            <div className="w-24 text-right">
                {delta !== null && (
                    <DeltaBadge
                        delta={lowerIsBetter ? -delta : delta}
                        unit={unit === "%" ? "%" : ` ${unit}`}
                    />
                )}
            </div>
        </div>
    );
}

export default function SessionComparison({ patientId }: SessionComparisonProps) {
    const [sessions, setSessions] = useState<SessionSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [sessionA, setSessionA] = useState<string>("");
    const [sessionB, setSessionB] = useState<string>("");

    useEffect(() => {
        getPatientSessions(patientId)
            .then((data) => {
                setSessions(data);
                if (data.length >= 2) {
                    setSessionA(data[1].session_id); // older
                    setSessionB(data[0].session_id); // newer
                } else if (data.length === 1) {
                    setSessionA(data[0].session_id);
                }
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    }, [patientId]);

    if (loading) {
        return <div className="glass-card p-6 animate-pulse h-40" style={{ background: "var(--surface-hover)" }} />;
    }

    if (sessions.length < 2) {
        return (
            <div className="glass-card p-8 text-center">
                <div className="text-3xl mb-2">📊</div>
                <p className="text-sm" style={{ color: "var(--text-muted)" }}>At least 2 completed scans are needed for comparison.</p>
                <p className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>This patient has {sessions.length} scan{sessions.length !== 1 ? "s" : ""}.</p>
            </div>
        );
    }

    const a = sessions.find((s) => s.session_id === sessionA);
    const b = sessions.find((s) => s.session_id === sessionB);

    // All disease keys across both sessions
    const allDiseases = Array.from(new Set([
        ...Object.keys(a?.disease_probabilities || {}),
        ...Object.keys(b?.disease_probabilities || {}),
    ])).sort((x, y) => {
        const bProb = (b?.disease_probabilities[y] || 0) + (a?.disease_probabilities[y] || 0);
        const aProb = (b?.disease_probabilities[x] || 0) + (a?.disease_probabilities[x] || 0);
        return bProb - aProb;
    }).slice(0, 6);

    return (
        <div className="space-y-4">
            {/* Session selectors */}
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <label className="block text-xs mb-1 uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Earlier Scan</label>
                    <select
                        value={sessionA}
                        onChange={(e) => setSessionA(e.target.value)}
                        className="w-full rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-400 border"
                        style={{ background: "var(--surface)", color: "var(--text)", borderColor: "var(--border)" }}
                    >
                        {sessions.map((s) => (
                            <option key={s.session_id} value={s.session_id} disabled={s.session_id === sessionB}>
                                {formatDate(s.created_at)} — {s.primary_diagnosis?.replace(/_/g, " ") || "No diagnosis"}
                            </option>
                        ))}
                    </select>
                </div>
                <div>
                    <label className="block text-xs mb-1 uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>Later Scan</label>
                    <select
                        value={sessionB}
                        onChange={(e) => setSessionB(e.target.value)}
                        className="w-full rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-400 border"
                        style={{ background: "var(--surface)", color: "var(--text)", borderColor: "var(--border)" }}
                    >
                        {sessions.map((s) => (
                            <option key={s.session_id} value={s.session_id} disabled={s.session_id === sessionA}>
                                {formatDate(s.created_at)} — {s.primary_diagnosis?.replace(/_/g, " ") || "No diagnosis"}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            {a && b && (
                <>
                    {/* Disease probabilities comparison */}
                    {allDiseases.length > 0 && (
                        <div className="glass-card p-5">
                            <h4 className="text-sm font-semibold mb-3" style={{ color: "var(--text)" }}>Disease Probabilities</h4>
                            <div className="flex items-center justify-between text-xs mb-2 px-1" style={{ color: "var(--text-muted)" }}>
                                <span className="w-28">Disease</span>
                                <span className="w-20 text-right">Earlier</span>
                                <span className="w-20 text-right">Later</span>
                                <span className="w-24 text-right">Change</span>
                            </div>
                            {allDiseases.map((disease) => {
                                const probA = a.disease_probabilities[disease] ?? 0;
                                const probB = b.disease_probabilities[disease] ?? 0;
                                const delta = probB - probA;
                                return (
                                    <div key={disease} className="flex items-center justify-between py-2 border-b last:border-0 text-sm" style={{ borderColor: "var(--border)" }}>
                                        <span className="w-28 text-xs" style={{ color: "var(--text-secondary)" }}>{DISEASE_LABELS[disease] || disease}</span>
                                        <span className="font-mono w-20 text-right text-xs" style={{ color: "var(--text)" }}>{formatPercent(probA)}</span>
                                        <span className="font-mono w-20 text-right text-xs" style={{ color: "var(--text)" }}>{formatPercent(probB)}</span>
                                        <div className="w-24 text-right">
                                            <DeltaBadge delta={delta} unit="%" />
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Vitals comparison */}
                    {(a.sense_results?.rppg || b.sense_results?.rppg) && (
                        <div className="glass-card p-5">
                            <h4 className="text-sm font-semibold mb-3" style={{ color: "var(--text)" }}>Vital Signs</h4>
                            <div className="flex items-center justify-between text-xs mb-2 px-1" style={{ color: "var(--text-muted)" }}>
                                <span className="w-28">Metric</span>
                                <span className="w-20 text-right">Earlier</span>
                                <span className="w-20 text-right">Later</span>
                                <span className="w-24 text-right">Change</span>
                            </div>
                            <VitalRow label="Heart Rate" a={a.sense_results?.rppg?.hr} b={b.sense_results?.rppg?.hr} unit="bpm" />
                            <VitalRow label="SpO₂" a={a.sense_results?.rppg?.spo2} b={b.sense_results?.rppg?.spo2} unit="%" />
                            <VitalRow label="HRV (RMSSD)" a={a.sense_results?.rppg?.hrv_rmssd} b={b.sense_results?.rppg?.hrv_rmssd} unit="ms" />
                            <VitalRow label="Resp. Rate" a={a.sense_results?.rppg?.rr} b={b.sense_results?.rppg?.rr} unit="br/min" />
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
