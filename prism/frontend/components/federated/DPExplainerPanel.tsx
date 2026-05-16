"use client";

interface DPExplainerPanelProps {
    epsilon: number;
    delta: number;
    noiseMultiplier: number;
    mechanism?: string;
}

export default function DPExplainerPanel({
    epsilon,
    delta,
    noiseMultiplier,
    mechanism = "Gaussian",
}: DPExplainerPanelProps) {
    const privacyLevel =
        epsilon < 1 ? { label: "Strong", color: "text-green-400" } :
            epsilon < 5 ? { label: "Good", color: "text-blue-400" } :
                epsilon < 8 ? { label: "Moderate", color: "text-amber-400" } :
                    { label: "Weak", color: "text-red-400" };

    return (
        <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold" style={{ color: "var(--text)" }}>🛡 Differential Privacy Explainer</h3>
                <span
                    className={`text-xs font-bold px-2 py-0.5 rounded-full border ${privacyLevel.color}`}
                    style={{ background: "var(--surface-hover)", borderColor: "var(--border)" }}
                >
                    {privacyLevel.label} Privacy
                </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                {[
                    { label: "ε (epsilon)", value: epsilon.toFixed(3), sub: "Privacy loss" },
                    { label: "δ (delta)", value: delta.toExponential(0), sub: "Failure prob." },
                    { label: "Noise σ", value: noiseMultiplier.toFixed(2), sub: "Multiplier" },
                    { label: "Mechanism", value: mechanism, sub: "Noise type" },
                ].map(({ label, value, sub }) => (
                    <div
                        key={label}
                        className="rounded-xl p-3 border"
                        style={{ background: "var(--surface-hover)", borderColor: "var(--border)" }}
                    >
                        <div className="text-xs mb-1" style={{ color: "var(--text-secondary)" }}>{label}</div>
                        <div className="text-xl font-bold font-mono" style={{ color: "var(--text)" }}>{value}</div>
                        <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{sub}</div>
                    </div>
                ))}
            </div>

            <div className="bg-blue-500/5 border border-blue-500/20 rounded-xl p-4 text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                <p className="font-medium text-blue-400 mb-2">What does this mean?</p>
                <p>
                    With <span className="font-mono" style={{ color: "var(--text)" }}>ε={epsilon.toFixed(2)}</span> and{" "}
                    <span className="font-mono" style={{ color: "var(--text)" }}>δ={delta.toExponential(0)}</span>, an adversary who sees the
                    aggregated model weights cannot determine with high confidence whether any individual patient&apos;s data
                    was included in training. The {mechanism} mechanism adds calibrated random noise (σ={noiseMultiplier.toFixed(2)})
                    to gradient updates before aggregation — <strong style={{ color: "var(--text)" }}>no raw patient data ever leaves the hospital</strong>.
                </p>
                {epsilon >= 8 && (
                    <p className="mt-2 text-amber-400 text-xs">
                        ⚠ Privacy budget is nearly exhausted. Consider pausing training or increasing noise multiplier.
                    </p>
                )}
            </div>
        </div>
    );
}
