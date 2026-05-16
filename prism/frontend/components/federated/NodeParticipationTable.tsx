"use client";

import type { FLNode } from "@/lib/types";
import { formatDate } from "@/lib/utils";

interface NodeParticipationTableProps {
    nodes: FLNode[];
    loading: boolean;
}

const STATUS_CONFIG = {
    active: { dot: "bg-green-500 animate-pulse", text: "text-green-400", label: "Active" },
    idle: { dot: "bg-amber-500", text: "text-amber-400", label: "Idle" },
    offline: { dot: "bg-red-500", text: "text-red-400", label: "Offline" },
};

export default function NodeParticipationTable({ nodes, loading }: NodeParticipationTableProps) {
    if (loading) {
        return <div className="glass-card p-6 animate-pulse h-48" style={{ background: "var(--surface-hover)" }} />;
    }

    return (
        <div className="glass-card overflow-hidden">
            <div
                className="p-4 border-b"
                style={{ borderColor: "var(--border)", background: "var(--surface-hover)" }}
            >
                <h3 className="text-sm font-semibold" style={{ color: "var(--text)" }}>🏥 Hospital Node Participation</h3>
                <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{nodes.length} nodes registered</p>
            </div>

            {nodes.length === 0 ? (
                <div className="p-8 text-center" style={{ color: "var(--text-muted)" }}>
                    <div className="text-3xl mb-2">🌐</div>
                    <p className="text-sm">No nodes registered yet</p>
                </div>
            ) : (
                <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                        <thead
                            className="text-xs uppercase"
                            style={{ background: "var(--surface-hover)", color: "var(--text-secondary)" }}
                        >
                            <tr>
                                <th className="px-4 py-3">Node / Hospital</th>
                                <th className="px-4 py-3">Status</th>
                                <th className="px-4 py-3">Rounds</th>
                                <th className="px-4 py-3">Data Samples</th>
                                <th className="px-4 py-3">ε Spent</th>
                                <th className="px-4 py-3">Last Seen</th>
                            </tr>
                        </thead>
                        <tbody>
                            {nodes.map((node) => {
                                const cfg = STATUS_CONFIG[node.status] || STATUS_CONFIG.offline;
                                return (
                                    <tr
                                        key={node.node_id}
                                        className="border-b transition-colors"
                                        style={{ borderColor: "var(--border)" }}
                                        onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                                        onMouseLeave={e => (e.currentTarget.style.background = "")}
                                    >
                                        <td className="px-4 py-3">
                                            <div className="font-medium" style={{ color: "var(--text)" }}>{node.hospital_name}</div>
                                            <div className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{node.node_id}</div>
                                        </td>
                                        <td className="px-4 py-3">
                                            <div className="flex items-center gap-2">
                                                <div className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                                                <span className={`text-xs font-medium ${cfg.text}`}>{cfg.label}</span>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3" style={{ color: "var(--text-secondary)" }}>{node.rounds_participated}</td>
                                        <td className="px-4 py-3" style={{ color: "var(--text-secondary)" }}>{node.data_samples_contributed.toLocaleString()}</td>
                                        <td className="px-4 py-3">
                                            <span className={`text-xs font-mono ${node.dp_epsilon_spent > 8 ? "text-red-400" : node.dp_epsilon_spent > 5 ? "text-amber-400" : "text-green-400"}`}>
                                                ε={node.dp_epsilon_spent.toFixed(2)}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-xs" style={{ color: "var(--text-muted)" }}>
                                            {node.last_seen ? formatDate(node.last_seen) : "—"}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}
