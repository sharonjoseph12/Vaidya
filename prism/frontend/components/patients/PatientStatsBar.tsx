"use client";

interface PatientStats { total: number; highRisk: number; scannedToday: number; avgSessions: number; }

const cards = [
    { key: "total", label: "Total Patients", accent: "#2563eb", sub: "Registered in system" },
    { key: "highRisk", label: "High Risk", accent: "#dc2626", sub: "≥10 sessions" },
    { key: "scannedToday", label: "Scanned Today", accent: "#16a34a", sub: "Active today" },
    { key: "avgSessions", label: "Avg Sessions", accent: "#7c3aed", sub: "Per patient" },
];

export default function PatientStatsBar({ stats, loading }: { stats: PatientStats; loading: boolean }) {
    if (loading) {
        return (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="glass-card p-5 animate-pulse h-20" style={{ background: "var(--surface-hover)" }} />
                ))}
            </div>
        );
    }

    return (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {cards.map(({ key, label, accent, sub }) => {
                const val = stats[key as keyof PatientStats];
                const display = key === "avgSessions" ? (val as number).toFixed(1) : val;
                return (
                    <div key={key} className="glass-card p-5" style={{ borderLeft: `4px solid ${accent}` }}>
                        <div className="text-xs uppercase tracking-wide mb-1" style={{ color: "var(--text-secondary)" }}>{label}</div>
                        <div className="text-3xl font-bold" style={{ color: key === "highRisk" ? accent : "var(--text)" }}>{display}</div>
                        <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{sub}</div>
                    </div>
                );
            })}
        </div>
    );
}
