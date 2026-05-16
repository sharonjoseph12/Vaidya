"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import { detectCoughEvent, classifySoundType } from "@/lib/audio-utils";

interface CoughEvent {
    timestamp: number;
    confidence: number;
}

interface CoughDetectionPanelProps {
    isRecording: boolean;
    audioAnalyser: AnalyserNode | null;
}

const CANVAS_W = 320;
const CANVAS_H = 90;
const MAX_SAMPLES = CANVAS_W; // one pixel per sample
const COUGH_WINDOW_MS = 4000; // show last 4 seconds of cough markers

export default function CoughDetectionPanel({ isRecording, audioAnalyser }: CoughDetectionPanelProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const animFrameRef = useRef<number>(0);
    const startTimeRef = useRef<number>(0);
    const coughEventsRef = useRef<CoughEvent[]>([]);
    const waveformRef = useRef<number[]>([]); // rolling RMS values
    const lastCoughTimeRef = useRef<number>(0);

    const [coughCount, setCoughCount] = useState(0);
    const [soundType, setSoundType] = useState<"cough" | "breathing" | "silence">("silence");
    const [isActive, setIsActive] = useState(false);

    const stopDrawing = useCallback(() => {
        cancelAnimationFrame(animFrameRef.current);
        setIsActive(false);
        setCoughCount(0);
        setSoundType("silence");
        coughEventsRef.current = [];
        waveformRef.current = [];
        lastCoughTimeRef.current = 0;
    }, []);

    const startDrawing = useCallback((analyser: AnalyserNode) => {
        startTimeRef.current = Date.now();
        setIsActive(true);

        // Use a larger fftSize for better time-domain resolution
        analyser.fftSize = 2048;
        const timeDomainData = new Float32Array(analyser.fftSize);

        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext("2d")!;

        function draw() {
            analyser.getFloatTimeDomainData(timeDomainData);

            const now = Date.now() - startTimeRef.current;

            // Classify sound type
            const type = classifySoundType(timeDomainData);
            setSoundType(type);

            // Detect cough with debounce
            const isCough = detectCoughEvent(timeDomainData, 44100);
            if (isCough && now - lastCoughTimeRef.current > 600) {
                lastCoughTimeRef.current = now;
                coughEventsRef.current.push({ timestamp: now, confidence: 0.85 });
                setCoughCount(c => c + 1);
            }

            // Compute RMS amplitude for waveform
            let sumSq = 0;
            for (let i = 0; i < timeDomainData.length; i++) sumSq += timeDomainData[i] ** 2;
            const rms = Math.sqrt(sumSq / timeDomainData.length);
            waveformRef.current.push(rms);
            if (waveformRef.current.length > MAX_SAMPLES) {
                waveformRef.current = waveformRef.current.slice(-MAX_SAMPLES);
            }

            // ── Draw ──────────────────────────────────────────────
            ctx.clearRect(0, 0, CANVAS_W, CANVAS_H);

            // Background — theme-aware via CSS variable
            const isDark = document.documentElement.classList.contains("dark");
            ctx.fillStyle = isDark ? "#0f172a" : "#f8fafc";
            ctx.fillRect(0, 0, CANVAS_W, CANVAS_H);

            // Center baseline
            ctx.strokeStyle = isDark ? "rgba(100,116,139,0.25)" : "rgba(148,163,184,0.4)";
            ctx.lineWidth = 1;
            ctx.setLineDash([4, 4]);
            ctx.beginPath();
            ctx.moveTo(0, CANVAS_H / 2);
            ctx.lineTo(CANVAS_W, CANVAS_H / 2);
            ctx.stroke();
            ctx.setLineDash([]);

            // Waveform bars
            const history = waveformRef.current;
            const barColor = type === "cough" ? "#ef4444" : type === "breathing" ? "#22c55e" : (isDark ? "#475569" : "#94a3b8");

            for (let i = 0; i < history.length; i++) {
                const x = (i / MAX_SAMPLES) * CANVAS_W;
                const amp = Math.min(history[i] * CANVAS_H * 4, CANVAS_H * 0.9);
                const half = amp / 2;
                ctx.fillStyle = barColor;
                ctx.fillRect(x, CANVAS_H / 2 - half, 1.5, amp);
            }

            // Cough event markers (red vertical lines)
            const windowStart = now - COUGH_WINDOW_MS;
            for (const ev of coughEventsRef.current) {
                if (ev.timestamp < windowStart) continue;
                const frac = (ev.timestamp - windowStart) / COUGH_WINDOW_MS;
                const x = frac * CANVAS_W;

                ctx.strokeStyle = "#ef4444";
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, CANVAS_H);
                ctx.stroke();

                // "COUGH" label
                ctx.fillStyle = "#ef4444";
                ctx.font = "bold 8px monospace";
                ctx.fillText("COUGH", Math.min(x + 2, CANVAS_W - 36), 10);
            }

            animFrameRef.current = requestAnimationFrame(draw);
        }

        draw();
    }, []);

    // React to isRecording + analyserNode changes
    useEffect(() => {
        if (!isRecording) {
            stopDrawing();
            return;
        }
        if (isRecording && audioAnalyser) {
            cancelAnimationFrame(animFrameRef.current); // cancel any previous loop
            startDrawing(audioAnalyser);
        }
        return () => cancelAnimationFrame(animFrameRef.current);
    }, [isRecording, audioAnalyser, startDrawing, stopDrawing]);

    // Sound type badge config
    const typeConfig = {
        cough: { label: "🔴 Cough", color: "#ef4444", bg: "rgba(239,68,68,0.12)", border: "rgba(239,68,68,0.4)" },
        breathing: { label: "🟢 Breathing", color: "#22c55e", bg: "rgba(34,197,94,0.12)", border: "rgba(34,197,94,0.4)" },
        silence: { label: "⚪ Silence", color: "var(--text-muted)", bg: "var(--surface-hover)", border: "var(--border)" },
    };
    const tc = typeConfig[soundType];

    // Not recording yet — show idle state
    if (!isRecording && !isActive) {
        return (
            <div className="glass-card p-4 w-80 space-y-3">
                <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold" style={{ color: "var(--text)" }}>Cough Detection</span>
                    <span className="text-xs px-2 py-0.5 rounded-full border" style={{ color: "var(--text-muted)", borderColor: "var(--border)", background: "var(--surface-hover)" }}>
                        Waiting…
                    </span>
                </div>
                <div
                    className="w-full rounded-lg flex items-center justify-center"
                    style={{ height: CANVAS_H, background: "var(--surface-hover)", border: "1px dashed var(--border)" }}
                >
                    <span className="text-xs" style={{ color: "var(--text-muted)" }}>Waveform appears when recording starts</span>
                </div>
                <div className="flex items-center justify-between">
                    <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Coughs detected</span>
                    <span className="text-2xl font-bold" style={{ color: "var(--text-muted)" }}>0</span>
                </div>
            </div>
        );
    }

    // Mic denied
    if (isRecording && !audioAnalyser) {
        return (
            <div className="glass-card p-4 w-80 text-center space-y-2">
                <div className="text-amber-500 text-sm font-medium">🎤 Microphone access required</div>
                <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Enable microphone permissions for live cough detection.
                </p>
            </div>
        );
    }

    return (
        <div className="glass-card p-4 w-80 space-y-3">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className={`w-2.5 h-2.5 rounded-full ${isActive ? "animate-pulse" : ""}`}
                        style={{ background: isActive ? "#ef4444" : "var(--text-muted)" }} />
                    <span className="text-sm font-semibold" style={{ color: "var(--text)" }}>Cough Detection</span>
                </div>
                <span
                    className="text-xs px-2 py-0.5 rounded-full border font-medium"
                    style={{ color: tc.color, background: tc.bg, borderColor: tc.border }}
                >
                    {tc.label}
                </span>
            </div>

            {/* Live waveform canvas */}
            <div className="relative">
                <canvas
                    ref={canvasRef}
                    width={CANVAS_W}
                    height={CANVAS_H}
                    className="w-full rounded-lg"
                    style={{ display: "block" }}
                />
                {/* Live indicator */}
                {isActive && (
                    <div className="absolute top-1.5 right-2 flex items-center gap-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                        <span className="text-[9px] font-bold text-red-500">LIVE</span>
                    </div>
                )}
            </div>

            {/* Cough count */}
            <div className="flex items-center justify-between">
                <span className="text-xs" style={{ color: "var(--text-secondary)" }}>Coughs detected</span>
                <div className="flex items-center gap-2">
                    <span
                        className="text-2xl font-bold tabular-nums"
                        style={{ color: coughCount > 0 ? "#ef4444" : "var(--text-muted)" }}
                    >
                        {coughCount}
                    </span>
                    {coughCount > 0 && <span className="text-xs text-red-500 animate-pulse">●</span>}
                </div>
            </div>

            {/* Legend */}
            <div className="flex gap-4 text-xs" style={{ color: "var(--text-muted)" }}>
                <span className="flex items-center gap-1.5">
                    <span className="inline-block w-3 h-0.5 bg-red-500 rounded" />
                    Cough event
                </span>
                <span className="flex items-center gap-1.5">
                    <span className="inline-block w-3 h-0.5 bg-green-500 rounded" />
                    Breathing
                </span>
                <span className="flex items-center gap-1.5">
                    <span className="inline-block w-3 h-0.5 rounded" style={{ background: "var(--text-muted)" }} />
                    Silence
                </span>
            </div>
        </div>
    );
}
