"use client";

import { useEffect, useState, useCallback } from "react";
import { healthCheck, getFLStatus } from "@/lib/api";

interface SubsystemStatus {
    name: string;
    description: string;
    status: "online" | "degraded" | "offline" | "checking";
    latencyMs?: number;
}

const STATUS = {
    online: { dot: "#16a34a", label: "Online", pulse: true },
    degraded: { dot: "#d97706", label: "Standby", pulse: true },
    offline: { dot: "#dc2626", label: "Offline", pulse: false },
    checking: { dot: "#94a3b8", label: "Checking…", pulse: true },
};

export default function SubsystemHealth() {
    const [systems, setSystems] = useState<SubsystemStatus[]>([
        { name: "FastAPI Backend", description: "Diagnostics & Core API", status: "checking" },
        { name: "Federated Learning Node", description: "Local differential privacy worker", status: "checking" },
        { name: "ABDM Sandbox", description: "NDHM API integration", status: "checking" },
    ]);

    const check = useCallback(async () => {
        const updated: SubsystemStatus[] = [...systems.map(s => ({ ...s, status: "checking" as SubsystemStatus["status"] }))];

        try {
            const h = await healthCheck();
            updated[0] = { ...updated[0], status: h.status === "ok" ? "online" : h.status === "degraded" ? "degraded" : "offline", latencyMs: h.latency_ms };
        } catch { updated[0] = { ...updated[0], status: "offline" }; }
        setSystems([...updated]);

        await new Promise(r => setTimeout(r, 500));
        try {
            const fl = await getFLStatus();
            updated[1] = { ...updated[1], status: fl.active_nodes > 0 ? "online" : "degraded" };
        } catch { updated[1] = { ...updated[1], status: "offline" }; }
        setSystems([...updated]);

        await new Promise(r => setTimeout(r, 500));
        updated[2] = { ...updated[2], status: "degraded" };
        setSystems([...updated]);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        setTimeout(() => check(), 0);
        const t = setInterval(check, 30000);
        return () => clearInterval(t);
    }, [check]);

    return (
        <div className="glass-card p-5 flex flex-col h-full">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-base font-bold" style={{ color: "var(--text)" }}>Subsystem Status</h3>
                <button
                    onClick={check}
                    className="text-xs px-2 py-1 rounded-lg border transition-all"
                    style={{ borderColor: "var(--border)", color: "var(--text-secondary)", background: "var(--surface-hover)" }}
                >
                    ↻ Refresh
                </button>
            </div>

            <div className="space-y-3 flex-1">
                {systems.map(sys => {
                    const cfg = STATUS[sys.status];
                    return (
                        <div
                            key={sys.name}
                            className="p-4 rounded-xl border flex justify-between items-center"
                            style={{ background: "var(--surface-hover)", borderColor: "var(--border)" }}
                        >
                            <div>
                                <div className="text-sm font-medium" style={{ color: "var(--text)" }}>{sys.name}</div>
                                <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{sys.description}</div>
                            </div>
                            <div className="flex items-center gap-2">
                                {sys.latencyMs != null && (
                                    <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{sys.latencyMs}ms</span>
                                )}
                                <span className="text-sm font-medium" style={{ color: cfg.dot }}>{cfg.label}</span>
                                <div
                                    className={`w-2 h-2 rounded-full ${cfg.pulse ? "animate-pulse" : ""}`}
                                    style={{ background: cfg.dot }}
                                />
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
