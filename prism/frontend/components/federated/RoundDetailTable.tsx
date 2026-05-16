"use client";

import { useState } from "react";
import type { FLRound } from "@/lib/types";
import { formatDate, formatPercent } from "@/lib/utils";

interface RoundDetailTableProps {
    rounds: FLRound[];
    loading: boolean;
}

export default function RoundDetailTable({ rounds, loading }: RoundDetailTableProps) {
    const [expandedRound, setExpandedRound] = useState<number | null>(null);

    if (loading) {
        return <div className="glass-card p-6 animate-pulse h-48" style={{ background: "var(--surface-hover)" }} />;
    }

    // Sort descending by round number
    const sorted = [...rounds].sort((a, b) => b.round_number - a.round_number);

    return (
        <div className="glass-card overflow-hidden">
            <div
                className="p-4 border-b"
                style={{ borderColor: "var(--border)", background: "var(--surface-hover)" }}
            >
                <h3 className="text-sm font-semibold" style={{ color: "var(--text)" }}>📊 Round History</h3>
                <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>Click a row to expand details</p>
            </div>

            {sorted.length === 0 ? (
                <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>No rounds completed yet</div>
            ) : (
                <div className="divide-y" style={{ borderColor: "var(--border)" }}>
                    {sorted.map((round, idx) => {
                        const prev = sorted[idx + 1]; // previous round (lower number)
                        const accDelta = prev?.metrics?.accuracy != null && round.metrics?.accuracy != null
                            ? round.metrics.accuracy - prev.metrics.accuracy
                            : null;
                        const lossDelta = prev?.metrics?.loss != null && round.metrics?.loss != null
                            ? round.metrics.loss - prev.metrics.loss
                            : null;
                        const isExpanded = expandedRound === round.round_number;

                        return (
                            <div key={round.round_number} style={{ borderColor: "var(--border)" }}>
                                <div
                                    className="px-4 py-3 flex items-center gap-4 cursor-pointer transition-colors"
                                    onClick={() => setExpandedRound(isExpanded ? null : round.round_number)}
                                    onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                                    onMouseLeave={e => (e.currentTarget.style.background = "")}
                                >
                                    <span className="text-xs w-6" style={{ color: "var(--text-secondary)" }}>{isExpanded ? "▼" : "▶"}</span>
                                    <span className="font-mono font-medium w-16" style={{ color: "var(--text)" }}>R{round.round_number}</span>
                                    <span className="text-xs w-24" style={{ color: "var(--text-secondary)" }}>{round.participating_nodes} nodes</span>

                                    {/* Accuracy */}
                                    <div className="flex items-center gap-1 w-28">
                                        <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Acc:</span>
                                        <span className="text-xs font-mono" style={{ color: "var(--text)" }}>
                                            {round.metrics?.accuracy != null ? formatPercent(round.metrics.accuracy) : "—"}
                                        </span>
                                        {accDelta !== null && (
                                            <span className={`text-xs font-mono ${accDelta >= 0 ? "text-green-400" : "text-red-400"}`}>
                                                {accDelta >= 0 ? "+" : ""}{(accDelta * 100).toFixed(2)}%
                                            </span>
                                        )}
                                    </div>

                                    {/* Loss */}
                                    <div className="flex items-center gap-1 w-28">
                                        <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Loss:</span>
                                        <span className="text-xs font-mono" style={{ color: "var(--text)" }}>
                                            {round.metrics?.loss != null ? round.metrics.loss.toFixed(4) : "—"}
                                        </span>
                                        {lossDelta !== null && (
                                            <span className={`text-xs font-mono ${lossDelta <= 0 ? "text-green-400" : "text-red-400"}`}>
                                                {lossDelta >= 0 ? "+" : ""}{lossDelta.toFixed(4)}
                                            </span>
                                        )}
                                    </div>

                                    <span className="text-xs ml-auto" style={{ color: "var(--text-muted)" }}>
                                        ε+{round.dp_epsilon_spent.toFixed(3)}
                                    </span>
                                    {round.completed_at && (
                                        <span className="text-xs hidden md:block" style={{ color: "var(--text-muted)" }}>
                                            {formatDate(round.completed_at)}
                                        </span>
                                    )}
                                </div>

                                {/* Expanded detail */}
                                {isExpanded && (
                                    <div
                                        className="px-8 py-3 border-t text-xs space-y-2"
                                        style={{ background: "var(--surface-hover)", borderColor: "var(--border)" }}
                                    >
                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                            <div>
                                                <div className="mb-0.5" style={{ color: "var(--text-muted)" }}>Participating Nodes</div>
                                                <div className="font-medium" style={{ color: "var(--text)" }}>{round.participating_nodes}</div>
                                            </div>
                                            <div>
                                                <div className="mb-0.5" style={{ color: "var(--text-muted)" }}>Rejected Nodes</div>
                                                <div className="text-red-400 font-medium">{round.rejected_nodes}</div>
                                            </div>
                                            <div>
                                                <div className="mb-0.5" style={{ color: "var(--text-muted)" }}>ε Spent This Round</div>
                                                <div className="text-amber-400 font-mono">{round.dp_epsilon_spent.toFixed(4)}</div>
                                            </div>
                                            {round.metrics && Object.entries(round.metrics).map(([k, v]) => (
                                                <div key={k}>
                                                    <div className="mb-0.5 capitalize" style={{ color: "var(--text-muted)" }}>{k}</div>
                                                    <div className="font-mono" style={{ color: "var(--text)" }}>{typeof v === "number" ? v.toFixed(4) : v}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
