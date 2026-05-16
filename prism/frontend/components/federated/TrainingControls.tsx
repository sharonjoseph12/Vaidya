"use client";

import { useState } from "react";
import { triggerFLRound } from "@/lib/api";

interface TrainingControlsProps {
    currentRound: number;
    totalNodes: number;
    isRoundInProgress?: boolean;
    onRoundTriggered: (roundNumber: number) => void;
}

export default function TrainingControls({
    currentRound,
    totalNodes,
    isRoundInProgress = false,
    onRoundTriggered,
}: TrainingControlsProps) {
    const [minNodes, setMinNodes] = useState(Math.max(1, Math.floor(totalNodes / 2)));
    const [loading, setLoading] = useState(false);
    const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

    const showToast = (type: "success" | "error", message: string) => {
        setToast({ type, message });
        setTimeout(() => setToast(null), 4000);
    };

    const handleTrigger = async () => {
        setLoading(true);
        try {
            const result = await triggerFLRound(minNodes);
            onRoundTriggered(result.round_number);
            showToast("success", `Round ${result.round_number} started successfully`);
        } catch (err: unknown) {
            const msg = err instanceof Error ? err.message : "Failed to trigger round";
            showToast("error", msg);
        } finally {
            setLoading(false);
        }
    };

    const isDisabled = loading || isRoundInProgress;

    return (
        <div className="glass-card p-5">
            <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text)" }}>⚙️ Training Controls</h3>

            {/* Toast */}
            {toast && (
                <div className={`mb-4 px-4 py-2 rounded-lg text-sm font-medium border ${toast.type === "success"
                    ? "bg-green-500/10 border-green-500/30 text-green-400"
                    : "bg-red-500/10 border-red-500/30 text-red-400"
                    }`}>
                    {toast.type === "success" ? "✓" : "✗"} {toast.message}
                </div>
            )}

            <div className="space-y-4">
                {/* Current round info */}
                <div className="flex justify-between text-sm">
                    <span style={{ color: "var(--text-secondary)" }}>Current Round</span>
                    <span className="font-mono font-bold" style={{ color: "var(--text)" }}>R{currentRound}</span>
                </div>

                {/* Min nodes slider */}
                <div>
                    <div className="flex justify-between text-sm mb-2">
                        <label style={{ color: "var(--text-secondary)" }}>Min Nodes Required</label>
                        <span className="font-mono" style={{ color: "var(--text)" }}>{minNodes} / {totalNodes || "?"}</span>
                    </div>
                    <input
                        type="range"
                        min={1}
                        max={Math.max(1, totalNodes)}
                        value={minNodes}
                        onChange={(e) => setMinNodes(Number(e.target.value))}
                        disabled={isDisabled}
                        className="w-full accent-blue-500 disabled:opacity-50"
                    />
                    <div className="flex justify-between text-xs mt-1" style={{ color: "var(--text-muted)" }}>
                        <span>1</span>
                        <span>{Math.max(1, totalNodes)}</span>
                    </div>
                </div>

                {/* Status indicator */}
                {isRoundInProgress && (
                    <div className="flex items-center gap-2 text-sm text-amber-400">
                        <div className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                        Round in progress — please wait
                    </div>
                )}

                {/* Trigger button */}
                <button
                    onClick={handleTrigger}
                    disabled={isDisabled}
                    className={`w-full py-3 rounded-xl font-semibold text-sm transition-all ${isDisabled
                        ? "cursor-not-allowed"
                        : "bg-gradient-to-r from-blue-600 to-cyan-500 text-white hover:shadow-lg hover:shadow-blue-500/25"
                        }`}
                    style={isDisabled ? { background: "var(--surface-hover)", color: "var(--text-muted)" } : undefined}
                >
                    {loading ? (
                        <span className="flex items-center justify-center gap-2">
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            Triggering...
                        </span>
                    ) : isRoundInProgress ? (
                        "Round In Progress..."
                    ) : (
                        "🚀 Trigger New Round"
                    )}
                </button>

                <p className="text-xs text-center" style={{ color: "var(--text-muted)" }}>
                    Requires ≥{minNodes} active node{minNodes !== 1 ? "s" : ""} to start
                </p>
            </div>
        </div>
    );
}
