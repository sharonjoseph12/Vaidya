"use client";

interface PrivacyBudgetGaugeProps {
    currentEpsilon: number;
    maxEpsilon?: number;
    delta?: number;
    noiseMultiplier?: number;
}

const CX = 80;
const CY = 80;
const RADIUS = 60;
const START_ANGLE = -225; // degrees
const END_ANGLE = 45;     // degrees (270° sweep)

function polarToCartesian(cx: number, cy: number, r: number, angleDeg: number) {
    const rad = (angleDeg * Math.PI) / 180;
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) };
}

function describeArc(cx: number, cy: number, r: number, startAngle: number, endAngle: number) {
    const start = polarToCartesian(cx, cy, r, startAngle);
    const end = polarToCartesian(cx, cy, r, endAngle);
    const sweep = endAngle - startAngle;
    const largeArc = sweep > 180 ? 1 : 0;
    return `M ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y}`;
}

export default function PrivacyBudgetGauge({
    currentEpsilon,
    maxEpsilon = 10,
    delta = 1e-5,
    noiseMultiplier = 1.1,
}: PrivacyBudgetGaugeProps) {
    const fraction = Math.min(Math.max(currentEpsilon / maxEpsilon, 0), 1);
    const totalSweep = END_ANGLE - START_ANGLE; // 270°
    const filledSweep = totalSweep * fraction;
    const filledEndAngle = START_ANGLE + filledSweep;

    const arcColor =
        currentEpsilon >= 8 ? "#ef4444" :
            currentEpsilon >= 5 ? "#f59e0b" :
                "#22c55e";

    const remaining = Math.max(0, maxEpsilon - currentEpsilon);
    const remainingPct = ((remaining / maxEpsilon) * 100).toFixed(0);

    const trackPath = describeArc(CX, CY, RADIUS, START_ANGLE, END_ANGLE);
    const filledPath = fraction > 0
        ? describeArc(CX, CY, RADIUS, START_ANGLE, filledEndAngle)
        : null;

    return (
        <div className="glass-card p-5">
            <h3 className="text-sm font-semibold mb-4" style={{ color: "var(--text)" }}>🔒 Privacy Budget (ε)</h3>
            <div className="flex items-center gap-6">
                {/* SVG Gauge */}
                <div className="flex-shrink-0">
                    <svg width={160} height={130} viewBox="0 0 160 130">
                        {/* Track */}
                        <path d={trackPath} fill="none" stroke="var(--border)" strokeWidth={12} strokeLinecap="round" />
                        {/* Filled arc */}
                        {filledPath && (
                            <path d={filledPath} fill="none" stroke={arcColor} strokeWidth={12} strokeLinecap="round" />
                        )}
                        {/* Center text */}
                        <text x={CX} y={CY - 6} textAnchor="middle" fill="var(--text)" fontSize={20} fontWeight="bold">
                            {currentEpsilon.toFixed(2)}
                        </text>
                        <text x={CX} y={CY + 12} textAnchor="middle" fill="var(--text-secondary)" fontSize={10}>
                            of ε={maxEpsilon}
                        </text>
                        <text x={CX} y={CY + 26} textAnchor="middle" fill={arcColor} fontSize={9} fontWeight="600">
                            {remainingPct}% remaining
                        </text>
                    </svg>
                </div>

                {/* Details */}
                <div className="space-y-3 flex-1">
                    <div className="flex justify-between text-sm">
                        <span style={{ color: "var(--text-secondary)" }}>Current ε</span>
                        <span className={`font-mono font-bold ${arcColor === "#ef4444" ? "text-red-400" : arcColor === "#f59e0b" ? "text-amber-400" : "text-green-400"}`}>
                            {currentEpsilon.toFixed(3)}
                        </span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span style={{ color: "var(--text-secondary)" }}>δ (delta)</span>
                        <span className="font-mono" style={{ color: "var(--text-secondary)" }}>{delta.toExponential(0)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span style={{ color: "var(--text-secondary)" }}>Noise σ</span>
                        <span className="font-mono" style={{ color: "var(--text-secondary)" }}>{noiseMultiplier.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                        <span style={{ color: "var(--text-secondary)" }}>Budget used</span>
                        <span className="font-mono" style={{ color: "var(--text-secondary)" }}>{(fraction * 100).toFixed(1)}%</span>
                    </div>

                    {/* Status bar */}
                    <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
                        <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{ width: `${fraction * 100}%`, backgroundColor: arcColor }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}
