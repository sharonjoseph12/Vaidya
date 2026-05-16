"use client";

import { useEffect, useRef, useState } from "react";
import { RPPGProcessor, type RPPGVitals } from "@/lib/rppg";

interface LiveVitalsPanelProps {
    videoRef: React.RefObject<HTMLVideoElement | null>;
    isRecording: boolean;
    onVitalsUpdate?: (vitals: RPPGVitals) => void;
}

interface VitalCardProps {
    label: string;
    value: number | null;
    unit: string;
    normalRange: string;
    color: string;
    loading: boolean;
}

function VitalCard({ label, value, unit, normalRange, color, loading }: VitalCardProps) {
    return (
        <div
            className="rounded-xl p-3 border flex-1 min-w-0"
            style={{ background: "var(--surface-hover)", borderColor: "var(--border)" }}
        >
            <div className="text-xs uppercase tracking-wide mb-1" style={{ color: "var(--text-muted)" }}>{label}</div>
            {loading || value === null ? (
                <div className="flex items-center gap-1.5">
                    <div className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: color, borderTopColor: "transparent" }} />
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>Measuring…</span>
                </div>
            ) : (
                <>
                    <div className="text-xl font-bold tabular-nums" style={{ color }}>
                        {value}<span className="text-xs font-normal ml-0.5" style={{ color: "var(--text-muted)" }}>{unit}</span>
                    </div>
                    <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>Normal: {normalRange}</div>
                </>
            )}
        </div>
    );
}

export default function LiveVitalsPanel({ videoRef, isRecording, onVitalsUpdate }: LiveVitalsPanelProps) {
    const processorRef = useRef<RPPGProcessor | null>(null);
    const frameTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const computeTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const [vitals, setVitals] = useState<RPPGVitals | null>(null);
    const [framesCollected, setFramesCollected] = useState(0);

    useEffect(() => {
        if (!isRecording) {
            // Stop and clean up
            if (frameTimerRef.current) clearInterval(frameTimerRef.current);
            if (computeTimerRef.current) clearInterval(computeTimerRef.current);
            processorRef.current?.reset();
            setVitals(null);
            setFramesCollected(0);
            return;
        }

        // Initialize processor
        if (!processorRef.current) {
            processorRef.current = new RPPGProcessor();
        }

        // Capture frames at ~30fps
        frameTimerRef.current = setInterval(() => {
            const video = videoRef.current;
            if (video && video.readyState >= 2) {
                processorRef.current!.addFrame(video);
                setFramesCollected(c => c + 1);
            }
        }, 33); // ~30fps

        // Compute vitals every 2 seconds
        computeTimerRef.current = setInterval(() => {
            const result = processorRef.current!.compute();
            setVitals(result);
            onVitalsUpdate?.(result);
        }, 2000);

        return () => {
            if (frameTimerRef.current) clearInterval(frameTimerRef.current);
            if (computeTimerRef.current) clearInterval(computeTimerRef.current);
        };
    }, [isRecording, videoRef, onVitalsUpdate]);

    const secondsCollected = Math.floor(framesCollected / 30);
    const isWarmingUp = secondsCollected < 3;

    return (
        <div className="glass-card p-4 w-full space-y-3">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div
                        className={`w-2.5 h-2.5 rounded-full ${isRecording ? "animate-pulse" : ""}`}
                        style={{ background: isRecording ? "#2563eb" : "var(--text-muted)" }}
                    />
                    <span className="text-sm font-semibold" style={{ color: "var(--text)" }}>
                        Live rPPG Vitals
                    </span>
                </div>
                {isRecording && (
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                        {isWarmingUp
                            ? `Warming up… ${3 - secondsCollected}s`
                            : vitals?.signalQuality === "good"
                                ? "✓ Good signal"
                                : vitals?.signalQuality === "fair"
                                    ? "~ Fair signal"
                                    : "⚠ Weak signal"}
                    </span>
                )}
            </div>

            {/* Vitals grid */}
            <div className="flex gap-2">
                <VitalCard
                    label="Heart Rate"
                    value={vitals?.hr ?? null}
                    unit=" bpm"
                    normalRange="60–100"
                    color="#ef4444"
                    loading={isWarmingUp || !isRecording}
                />
                <VitalCard
                    label="SpO₂"
                    value={vitals?.spo2 ?? null}
                    unit="%"
                    normalRange="≥95%"
                    color="#2563eb"
                    loading={isWarmingUp || !isRecording}
                />
                <VitalCard
                    label="HRV"
                    value={vitals?.hrv_rmssd ?? null}
                    unit=" ms"
                    normalRange="20–80"
                    color="#7c3aed"
                    loading={isWarmingUp || !isRecording}
                />
                <VitalCard
                    label="Resp. Rate"
                    value={vitals?.rr ?? null}
                    unit=" br/m"
                    normalRange="12–20"
                    color="#16a34a"
                    loading={isWarmingUp || !isRecording}
                />
            </div>

            {/* Confidence bar */}
            {vitals && !isWarmingUp && (
                <div>
                    <div className="flex justify-between text-xs mb-1" style={{ color: "var(--text-muted)" }}>
                        <span>Signal confidence</span>
                        <span>{Math.round((vitals.confidence ?? 0) * 100)}%</span>
                    </div>
                    <div className="h-1.5 rounded-full overflow-hidden" style={{ background: "var(--border)" }}>
                        <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{
                                width: `${(vitals.confidence ?? 0) * 100}%`,
                                background: vitals.confidence > 0.6 ? "#16a34a" : vitals.confidence > 0.3 ? "#d97706" : "#ef4444",
                            }}
                        />
                    </div>
                </div>
            )}

            {!isRecording && (
                <p className="text-xs text-center" style={{ color: "var(--text-muted)" }}>
                    Vitals appear once face scan starts
                </p>
            )}
        </div>
    );
}
