"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { getPatients } from "@/lib/api";
import { deriveRiskLevel, generatePatientCSV, formatDate } from "@/lib/utils";
import type { Patient, PatientList } from "@/lib/types";

interface PatientStats {
    total: number;
    highRisk: number;
    scannedToday: number;
    avgSessions: number;
}

interface PatientManagementTableProps {
    onStatsChange: (stats: PatientStats) => void;
}

type SortField = "name" | "last_scan" | "sessions_count" | "created_at";
type SortDir = "asc" | "desc";
type RiskFilter = "all" | "high" | "medium" | "low";

const VALID_RISK_FILTERS: RiskFilter[] = ["all", "high", "medium", "low"];
const PAGE_SIZE = 20;

const RISK_BADGE: Record<string, string> = {
    high: "bg-red-500/20 text-red-400 border-red-500/40",
    medium: "bg-amber-500/20 text-amber-400 border-amber-500/40",
    low: "bg-green-500/20 text-green-400 border-green-500/40",
};

export default function PatientManagementTable({ onStatsChange }: PatientManagementTableProps) {
    const router = useRouter();
    const [data, setData] = useState<PatientList | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Filters & sort
    const [search, setSearch] = useState("");
    const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");
    const [sortField, setSortField] = useState<SortField>("created_at");
    const [sortDir, setSortDir] = useState<SortDir>("desc");
    const [page, setPage] = useState(1);

    // Selection
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

    // Debounce ref
    const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const [debouncedSearch, setDebouncedSearch] = useState("");

    useEffect(() => {
        if (debounceRef.current) clearTimeout(debounceRef.current);
        debounceRef.current = setTimeout(() => setDebouncedSearch(search), 300);
        return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
    }, [search]);

    const fetchPatients = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const validRisk = VALID_RISK_FILTERS.includes(riskFilter) ? riskFilter : "all";
            const result = await getPatients(
                page,
                PAGE_SIZE,
                debouncedSearch || undefined,
                validRisk !== "all" ? validRisk : undefined,
                sortField,
                sortDir,
            );
            setData(result);

            // Compute stats
            const patients = result.patients;
            const highRisk = patients.filter((p) => deriveRiskLevel(p) === "high").length;
            const today = new Date().toDateString();
            const scannedToday = patients.filter(
                (p) => p.last_session_date && new Date(p.last_session_date).toDateString() === today,
            ).length;
            const avgSessions = patients.length > 0
                ? patients.reduce((sum, p) => sum + (p.sessions_count ?? 0), 0) / patients.length
                : 0;

            onStatsChange({ total: result.total, highRisk, scannedToday, avgSessions });
        } catch (err: unknown) {
            setError(err instanceof Error ? err.message : "Failed to load patients");
        } finally {
            setLoading(false);
        }
    }, [page, debouncedSearch, riskFilter, sortField, sortDir, onStatsChange]);

    useEffect(() => {
        fetchPatients();
    }, [fetchPatients]);

    const handleSort = (field: SortField) => {
        if (sortField === field) {
            setSortDir((d) => (d === "asc" ? "desc" : "asc"));
        } else {
            setSortField(field);
            setSortDir("asc");
        }
        setPage(1);
    };

    const toggleSelectAll = () => {
        if (!data) return;
        if (selectedIds.size === data.patients.length) {
            setSelectedIds(new Set());
        } else {
            setSelectedIds(new Set(data.patients.map((p) => p.id)));
        }
    };

    const toggleSelect = (id: string) => {
        setSelectedIds((prev) => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    };

    const handleExportCSV = () => {
        if (!data) return;
        const selected = data.patients.filter((p) => selectedIds.has(p.id));
        const csv = generatePatientCSV(selected);
        const blob = new Blob([csv], { type: "text/csv" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "patients_export.csv";
        a.click();
        URL.revokeObjectURL(url);
    };

    const SortIcon = ({ field }: { field: SortField }) => {
        if (sortField !== field) return <span className="ml-1" style={{ color: "var(--text-muted)" }}>↕</span>;
        return <span className="text-blue-400 ml-1">{sortDir === "asc" ? "↑" : "↓"}</span>;
    };

    const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

    return (
        <div className="glass-card overflow-hidden flex flex-col">
            {/* Toolbar */}
            <div
                className="p-4 border-b flex flex-col md:flex-row gap-3 items-start md:items-center justify-between"
                style={{ borderColor: "var(--border)", background: "var(--surface-hover)" }}
            >
                <div className="flex gap-3 flex-1 flex-wrap">
                    {/* Search */}
                    <input
                        type="text"
                        placeholder="Search by name or ABHA ID..."
                        value={search}
                        onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                        className="rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 w-64 border"
                        style={{ background: "var(--surface)", color: "var(--text)", borderColor: "var(--border)" }}
                    />

                    {/* Risk filter */}
                    <select
                        value={riskFilter}
                        onChange={(e) => {
                            const val = e.target.value as RiskFilter;
                            if (VALID_RISK_FILTERS.includes(val)) {
                                setRiskFilter(val);
                                setPage(1);
                            }
                        }}
                        className="rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500 border"
                        style={{ background: "var(--surface)", color: "var(--text)", borderColor: "var(--border)" }}
                    >
                        <option value="all">All Risk Levels</option>
                        <option value="high">High Risk</option>
                        <option value="medium">Medium Risk</option>
                        <option value="low">Low Risk</option>
                    </select>
                </div>

                <div className="flex gap-2">
                    {selectedIds.size > 0 && (
                        <button
                            onClick={handleExportCSV}
                            className="px-3 py-2 bg-green-600/20 text-green-400 border border-green-500/30 hover:bg-green-600/30 rounded-lg text-sm font-medium transition"
                        >
                            Export CSV ({selectedIds.size})
                        </button>
                    )}
                    <button
                        onClick={() => router.push("/patient/new")}
                        className="px-3 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-sm font-medium transition text-white"
                    >
                        + New Patient
                    </button>
                </div>
            </div>

            {/* Error state */}
            {error && (
                <div className="p-4 bg-red-500/10 border-b border-red-500/20 flex items-center justify-between">
                    <span className="text-red-400 text-sm">{error}</span>
                    <button onClick={fetchPatients} className="text-xs px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-300 rounded transition">
                        Retry
                    </button>
                </div>
            )}

            {/* Table */}
            <div className="flex-1 overflow-x-auto">
                {loading ? (
                    <div className="p-8 text-center animate-pulse" style={{ color: "var(--text-muted)" }}>Loading patients...</div>
                ) : (
                    <table className="w-full text-sm text-left">
                        <thead
                            className="text-xs uppercase sticky top-0"
                            style={{ background: "var(--surface-hover)", color: "var(--text-secondary)" }}
                        >
                            <tr>
                                <th className="px-4 py-3 w-10">
                                    <input
                                        type="checkbox"
                                        checked={data ? selectedIds.size === data.patients.length && data.patients.length > 0 : false}
                                        onChange={toggleSelectAll}
                                        className="rounded text-blue-600"
                                        style={{ borderColor: "var(--border)", background: "var(--surface)" }}
                                    />
                                </th>
                                <th
                                    className="px-4 py-3 cursor-pointer transition-colors"
                                    onClick={() => handleSort("name")}
                                    onMouseEnter={e => (e.currentTarget.style.color = "var(--text)")}
                                    onMouseLeave={e => (e.currentTarget.style.color = "var(--text-secondary)")}
                                >
                                    Name <SortIcon field="name" />
                                </th>
                                <th className="px-4 py-3">ABHA / Location</th>
                                <th className="px-4 py-3">Risk</th>
                                <th
                                    className="px-4 py-3 cursor-pointer transition-colors"
                                    onClick={() => handleSort("sessions_count")}
                                    onMouseEnter={e => (e.currentTarget.style.color = "var(--text)")}
                                    onMouseLeave={e => (e.currentTarget.style.color = "var(--text-secondary)")}
                                >
                                    Sessions <SortIcon field="sessions_count" />
                                </th>
                                <th
                                    className="px-4 py-3 cursor-pointer transition-colors"
                                    onClick={() => handleSort("last_scan")}
                                    onMouseEnter={e => (e.currentTarget.style.color = "var(--text)")}
                                    onMouseLeave={e => (e.currentTarget.style.color = "var(--text-secondary)")}
                                >
                                    Last Scan <SortIcon field="last_scan" />
                                </th>
                                <th className="px-4 py-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {data?.patients.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="px-4 py-12 text-center" style={{ color: "var(--text-muted)" }}>
                                        <div className="text-4xl mb-2">📋</div>
                                        <p>No patients found</p>
                                    </td>
                                </tr>
                            ) : (
                                data?.patients.map((p: Patient) => {
                                    const risk = deriveRiskLevel(p);
                                    return (
                                        <tr
                                            key={p.id}
                                            className="border-b cursor-pointer group transition-colors"
                                            style={{ borderColor: "var(--border)" }}
                                            onClick={() => router.push(`/patient/${p.id}`)}
                                            onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                                            onMouseLeave={e => (e.currentTarget.style.background = "")}
                                        >
                                            <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedIds.has(p.id)}
                                                    onChange={() => toggleSelect(p.id)}
                                                    className="rounded text-blue-600"
                                                    style={{ borderColor: "var(--border)", background: "var(--surface)" }}
                                                />
                                            </td>
                                            <td className="px-4 py-3">
                                                <div className="font-medium" style={{ color: "var(--text)" }}>
                                                    {p.demographics?.name || <span className="italic" style={{ color: "var(--text-muted)" }}>No name</span>}
                                                </div>
                                                <div className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{p.id.split("-")[0]}</div>
                                            </td>
                                            <td className="px-4 py-3">
                                                {p.abha_id ? (
                                                    <div className="text-blue-400 text-xs font-medium">{p.abha_id}</div>
                                                ) : (
                                                    <div className="text-xs italic" style={{ color: "var(--text-muted)" }}>No ABHA</div>
                                                )}
                                                {p.demographics?.location && (
                                                    <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{p.demographics.location}</div>
                                                )}
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className={`text-xs px-2 py-0.5 rounded-full border font-medium capitalize ${RISK_BADGE[risk]}`}>
                                                    {risk}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3" style={{ color: "var(--text-secondary)" }}>{p.sessions_count}</td>
                                            <td className="px-4 py-3 text-xs" style={{ color: "var(--text-muted)" }}>
                                                {p.last_session_date ? formatDate(p.last_session_date) : "Never"}
                                            </td>
                                            <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                                                <div className="flex justify-end gap-2">
                                                    <button
                                                        onClick={() => router.push(`/scan?patientId=${p.id}`)}
                                                        className="px-2 py-1 bg-green-600/20 text-green-400 hover:bg-green-600/30 rounded text-xs transition"
                                                    >
                                                        Scan 📷
                                                    </button>
                                                    <button
                                                        onClick={() => router.push(`/patient/${p.id}`)}
                                                        className="text-blue-500 group-hover:text-blue-400 font-medium text-xs"
                                                    >
                                                        View →
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Pagination */}
            {data && data.total > PAGE_SIZE && (
                <div
                    className="p-3 border-t flex items-center justify-between text-sm"
                    style={{ borderColor: "var(--border)", background: "var(--surface-hover)" }}
                >
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                        Showing {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, data.total)} of {data.total} patients
                    </span>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setPage((p) => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-3 py-1 rounded text-xs disabled:opacity-40 disabled:cursor-not-allowed transition border"
                            style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-secondary)" }}
                            onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                            onMouseLeave={e => (e.currentTarget.style.background = "var(--surface)")}
                        >
                            ← Previous
                        </button>
                        <span className="text-xs" style={{ color: "var(--text-muted)" }}>Page {page} of {totalPages}</span>
                        <button
                            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                            disabled={page === totalPages}
                            className="px-3 py-1 rounded text-xs disabled:opacity-40 disabled:cursor-not-allowed transition border"
                            style={{ background: "var(--surface)", borderColor: "var(--border)", color: "var(--text-secondary)" }}
                            onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                            onMouseLeave={e => (e.currentTarget.style.background = "var(--surface)")}
                        >
                            Next →
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
