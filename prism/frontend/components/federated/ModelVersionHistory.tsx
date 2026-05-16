"use client";

import type { ModelVersion } from "@/lib/types";
import { formatDate, formatPercent } from "@/lib/utils";

interface ModelVersionHistoryProps {
    versions: ModelVersion[];
    loading: boolean;
}

export default function ModelVersionHistory({ versions, loading }: ModelVersionHistoryProps) {
    if (loading) {
        return <div className="glass-card p-6 animate-pulse h-40" style={{ background: "var(--surface-hover)" }} />;
    }

    const sorted = [...versions].sort((a, b) => b.trained_at.localeCompare(a.trained_at));

    return (
        <div className="glass-card overflow-hidden">
            <div
                className="p-4 border-b"
                style={{ borderColor: "var(--border)", background: "var(--surface-hover)" }}
            >
                <h3 className="text-sm font-semibold" style={{ color: "var(--text)" }}>🗂 Model Version History</h3>
            </div>

            {sorted.length === 0 ? (
                <div className="p-6 text-center text-sm" style={{ color: "var(--text-muted)" }}>No model versions recorded</div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead
                            className="text-xs uppercase"
                            style={{ background: "var(--surface-hover)", color: "var(--text-secondary)" }}
                        >
                            <tr>
                                <th className="px-4 py-3">Version</th>
                                <th className="px-4 py-3">Accuracy</th>
                                <th className="px-4 py-3">Loss</th>
                                <th className="px-4 py-3">Nodes</th>
                                <th className="px-4 py-3">Trained At</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sorted.map((v, i) => (
                                <tr
                                    key={v.version}
                                    className="border-b transition-colors"
                                    style={{
                                        borderColor: "var(--border)",
                                        background: i === 0 ? "rgba(59,130,246,0.05)" : undefined,
                                    }}
                                    onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                                    onMouseLeave={e => (e.currentTarget.style.background = i === 0 ? "rgba(59,130,246,0.05)" : "")}
                                >
                                    <td className="px-4 py-3">
                                        <span className="font-mono text-blue-400 text-xs">{v.version}</span>
                                        {i === 0 && <span className="ml-2 text-xs bg-blue-500/20 text-blue-400 border border-blue-500/30 px-1.5 py-0.5 rounded">Latest</span>}
                                    </td>
                                    <td className="px-4 py-3 text-green-400 font-mono">{formatPercent(v.accuracy, 2)}</td>
                                    <td className="px-4 py-3 font-mono" style={{ color: "var(--text-secondary)" }}>{v.loss.toFixed(4)}</td>
                                    <td className="px-4 py-3" style={{ color: "var(--text-secondary)" }}>{v.participating_nodes}</td>
                                    <td className="px-4 py-3 text-xs" style={{ color: "var(--text-muted)" }}>{formatDate(v.trained_at)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
