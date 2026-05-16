"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getRecentSessions } from "@/lib/api";
import type { RecentSession } from "@/lib/types";
import { getRiskColor, formatDate } from "@/lib/utils";

export default function RecentScans({ limit = 5 }: { limit?: number }) {
    const router = useRouter();
    const [sessions, setSessions] = useState<RecentSession[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => {
        getRecentSessions(limit).then(setSessions).catch(() => setError(true)).finally(() => setLoading(false));
    }, [limit]);

    return (
        <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-bold" style={{ color: "var(--text)" }}>Recent Scans</h3>
                <button
                    onClick={() => router.push("/patients")}
                    className="text-xs font-medium transition-colors"
                    style={{ color: "var(--blue)" }}
                >
                    View all →
                </button>
            </div>

            {loading && (
                <div className="space-y-2">
                    {[...Array(3)].map((_, i) => (
                        <div key={i} className="h-12 rounded-lg animate-pulse" style={{ background: "var(--surface-hover)" }} />
                    ))}
                </div>
            )}

            {!loading && (error || sessions.length === 0) && (
                <div className="text-center py-6" style={{ color: "var(--text-muted)" }}>
                    <div className="text-3xl mb-2">📋</div>
                    <p className="text-sm">{error ? "Could not load recent scans" : "No scans yet"}</p>
                </div>
            )}

            {!loading && !error && sessions.length > 0 && (
                <div className="space-y-2">
                    {sessions.map(session => {
                        const confidence = session.confidence_score ?? 0;
                        const dotColor = getRiskColor(confidence);
                        return (
                            <div
                                key={session.session_id}
                                onClick={() => router.push(`/patient/${session.session_id}`)}
                                className="flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-all group"
                                style={{ background: "var(--surface-hover)", borderColor: "var(--border)" }}
                                onMouseEnter={e => (e.currentTarget.style.borderColor = "var(--blue)")}
                                onMouseLeave={e => (e.currentTarget.style.borderColor = "var(--border)")}
                            >
                                <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: dotColor }} />
                                <div className="flex-1 min-w-0">
                                    <div className="text-sm font-medium truncate" style={{ color: "var(--text)" }}>
                                        {session.patient_name || `Patient ${session.patient_id.split("-")[0]}`}
                                    </div>
                                    <div className="text-xs truncate" style={{ color: "var(--text-muted)" }}>
                                        {session.primary_diagnosis?.replace(/_/g, " ") || "Pending analysis"}
                                    </div>
                                </div>
                                {session.confidence_score != null && (
                                    <div className="text-xs font-mono flex-shrink-0" style={{ color: "var(--text-secondary)" }}>
                                        {(session.confidence_score * 100).toFixed(0)}%
                                    </div>
                                )}
                                <div className="text-xs flex-shrink-0 hidden md:block" style={{ color: "var(--text-muted)" }}>
                                    {formatDate(session.created_at)}
                                </div>
                                <span className="text-xs transition-colors" style={{ color: "var(--text-muted)" }}>→</span>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
