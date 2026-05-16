"use client";

import { useEffect, useState, useCallback } from "react";
import { getAuditLog } from "@/lib/api";
import type { AuditEntry } from "@/lib/types";
import { formatDate } from "@/lib/utils";

interface AuditLogProps {
    pageSize?: number;
}

const ACTION_CONFIG: Record<string, { color: string; label: string }> = {
    create: { color: "bg-green-100 text-green-700 border-green-200", label: "CREATE" },
    read: { color: "bg-blue-100 text-blue-700 border-blue-200", label: "READ" },
    update: { color: "bg-amber-100 text-amber-700 border-amber-200", label: "UPDATE" },
    delete: { color: "bg-red-100 text-red-700 border-red-200", label: "DELETE" },
    export: { color: "bg-purple-100 text-purple-700 border-purple-200", label: "EXPORT" },
};

export default function AuditLog({ pageSize = 20 }: AuditLogProps) {
    const [entries, setEntries] = useState<AuditEntry[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchLog = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await getAuditLog(page, pageSize);
            setEntries(data.entries || []);
            setTotal(data.total || 0);
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Failed to load audit log");
        } finally {
            setLoading(false);
        }
    }, [page, pageSize]);

    useEffect(() => {
        fetchLog();
    }, [fetchLog]);

    const totalPages = Math.ceil(total / pageSize);

    return (
        <div className="space-y-4">
            {error && (
                <div className="glass-card p-4 bg-red-50 border-red-200 flex items-center justify-between">
                    <span className="text-red-700 text-sm">{error}</span>
                    <button onClick={fetchLog} className="text-xs px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 rounded transition">
                        Retry
                    </button>
                </div>
            )}

            <div className="glass-card overflow-hidden">
                <div
                    className="p-4 border-b flex items-center justify-between"
                    style={{ borderColor: "var(--border)", background: "var(--surface-hover)" }}
                >
                    <div>
                        <h3 className="text-sm font-semibold" style={{ color: "var(--text)" }}>PHI Access Log</h3>
                        <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{total.toLocaleString()} total entries</p>
                    </div>
                    <button
                        onClick={fetchLog}
                        className="text-xs px-3 py-1.5 rounded-lg transition border"
                        style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                        onMouseEnter={e => (e.currentTarget.style.background = "var(--surface)")}
                        onMouseLeave={e => (e.currentTarget.style.background = "")}
                    >
                        ↻ Refresh
                    </button>
                </div>

                {loading ? (
                    <div className="p-8 text-center text-sm animate-pulse" style={{ color: "var(--text-muted)" }}>Loading audit log...</div>
                ) : entries.length === 0 ? (
                    <div className="p-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>No audit entries found</div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead
                                className="text-xs uppercase border-b"
                                style={{ background: "var(--surface-hover)", color: "var(--text-secondary)", borderColor: "var(--border)" }}
                            >
                                <tr>
                                    <th className="px-4 py-3">Timestamp</th>
                                    <th className="px-4 py-3">User</th>
                                    <th className="px-4 py-3">Action</th>
                                    <th className="px-4 py-3">Resource</th>
                                    <th className="px-4 py-3">Resource ID</th>
                                </tr>
                            </thead>
                            <tbody>
                                {entries.map((entry) => {
                                    const actionCfg = ACTION_CONFIG[entry.action] || ACTION_CONFIG.read;
                                    return (
                                        <tr
                                            key={entry.id}
                                            className="border-b transition-colors"
                                            style={{ borderColor: "var(--border)" }}
                                            onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                                            onMouseLeave={e => (e.currentTarget.style.background = "")}
                                        >
                                            <td className="px-4 py-3 text-xs font-mono whitespace-nowrap" style={{ color: "var(--text-muted)" }}>
                                                {formatDate(entry.timestamp)}
                                            </td>
                                            <td className="px-4 py-3">
                                                <div className="font-medium text-xs" style={{ color: "var(--text)" }}>
                                                    {entry.user_name || entry.user_id.split("-")[0]}
                                                </div>
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${actionCfg.color}`}>
                                                    {actionCfg.label}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-xs capitalize" style={{ color: "var(--text-secondary)" }}>
                                                {entry.resource_type.replace(/_/g, " ")}
                                            </td>
                                            <td className="px-4 py-3 text-xs font-mono" style={{ color: "var(--text-muted)" }}>
                                                {entry.resource_id.split("-")[0]}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Pagination */}
                {totalPages > 1 && (
                    <div
                        className="p-3 border-t flex items-center justify-between text-xs"
                        style={{ borderColor: "var(--border)", background: "var(--surface-hover)" }}
                    >
                        <span style={{ color: "var(--text-muted)" }}>
                            Page {page} of {totalPages} ({total} entries)
                        </span>
                        <div className="flex gap-2">
                            <button
                                onClick={() => setPage((p) => Math.max(1, p - 1))}
                                disabled={page === 1}
                                className="px-3 py-1 rounded disabled:opacity-40 disabled:cursor-not-allowed transition border"
                                style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                                onMouseEnter={e => (e.currentTarget.style.background = "var(--surface)")}
                                onMouseLeave={e => (e.currentTarget.style.background = "")}
                            >
                                ← Prev
                            </button>
                            <button
                                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                                disabled={page === totalPages}
                                className="px-3 py-1 rounded disabled:opacity-40 disabled:cursor-not-allowed transition border"
                                style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                                onMouseEnter={e => (e.currentTarget.style.background = "var(--surface)")}
                                onMouseLeave={e => (e.currentTarget.style.background = "")}
                            >
                                Next →
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
