"use client";

import { useEffect, useRef, useState, useCallback } from "react";

interface ScanQualityIndicatorProps {
    videoRef: React.RefObject<HTMLVideoElement | null>;
    analyserNode: AnalyserNode | null;
    onQualityChange?: (score: number) => void;
}

interface QualityMetrics {
    faceDetected: boolean;
    brightness: number;
    audioNoiseLevel: number;
}

function computeQualityScore(metrics: QualityMetrics): { score: number; tips: string[] } {
    let score = 0;
    const tips: string[] = [];

    if (metrics.faceDetected) {
        score += 40;
    } else {
        tips.push("Position face in frame");
    }

    if (metrics.brightness >= 60 && metrics.brightness <= 200) {
        score += 40;
    } else if (metrics.brightness < 60) {
        tips.push("Move to better lighting");
    } else {
        tips.push("Reduce bright background light");
    }

    if (metrics.audioNoiseLevel < 0.3) {
        score += 20;
    } else {
        tips.push("Reduce background noise");
    }

    return { score, tips };
}

function sampleBrightness(video: HTMLVideoElement): number {
    try {
        const canvas = document.createElement("canvas");
        canvas.width = 64;
        canvas.height = 64;
        const ctx = canvas.getContext("2d");
        if (!ctx) return 128;
        ctx.drawImage(video, 0, 0, 64, 64);
        const data = ctx.getImageData(0, 0, 64, 64).data;
        let sum = 0;
        for (let i = 0; i < data.length; i += 4) {
            sum += (data[i] + data[i + 1] + data[i + 2]) / 3;
        }
        return sum / (data.length / 4);
    } catch {
        return 128;
    }
}

function detectFacePresence(video: HTMLVideoElement): boolean {
    // Heuristic: check if center region has skin-tone pixels
    try {
        const canvas = document.createElement("canvas");
        canvas.width = 32;
        canvas.height = 32;
        const ctx = canvas.getContext("2d");
        if (!ctx) return false;
        ctx.drawImage(video, 0, 0, 32, 32);
        const data = ctx.getImageData(8, 4, 16, 24).data; // center crop
        let skinPixels = 0;
        for (let i = 0; i < data.length; i += 4) {
            const r = data[i], g = data[i + 1], b = data[i + 2];
            // Rough skin tone detection
            if (r > 60 && g > 40 && b > 20 && r > g && r > b && r - b > 15) {
                skinPixels++;
            }
        }
        return skinPixels > 20; // at least 20 skin-tone pixels in center
    } catch {
        return false;
    }
}

const SCORE_CONFIG = {
    good: { color: "text-green-600", barColor: "bg-green-500", label: "Good" },
    fair: { color: "text-amber-600", barColor: "bg-amber-500", label: "Fair" },
    poor: { color: "text-red-600", barColor: "bg-red-500", label: "Poor" },
};

export default function ScanQualityIndicator({
    videoRef,
    analyserNode,
    onQualityChange,
}: ScanQualityIndicatorProps) {
    const [score, setScore] = useState(0);
    const [tips, setTips] = useState<string[]>([]);
    const frameRef = useRef<number>(0);
    const lastSampleRef = useRef<number>(0);

    const sample = useCallback(() => {
        const now = Date.now();
        // Sample at ~5fps to avoid blocking
        if (now - lastSampleRef.current < 200) {
            frameRef.current = requestAnimationFrame(sample);
            return;
        }
        lastSampleRef.current = now;

        const video = videoRef.current;
        if (!video || video.readyState < 2) {
            frameRef.current = requestAnimationFrame(sample);
            return;
        }

        const brightness = sampleBrightness(video);
        const faceDetected = detectFacePresence(video);

        let audioNoiseLevel = 0;
        if (analyserNode) {
            const buf = new Float32Array(analyserNode.fftSize);
            analyserNode.getFloatTimeDomainData(buf);
            let sumSq = 0;
            for (let i = 0; i < buf.length; i++) sumSq += buf[i] ** 2;
            audioNoiseLevel = Math.sqrt(sumSq / buf.length);
        }

        const { score: s, tips: t } = computeQualityScore({ faceDetected, brightness, audioNoiseLevel });
        setScore(s);
        setTips(t);
        onQualityChange?.(s);

        frameRef.current = requestAnimationFrame(sample);
    }, [videoRef, analyserNode, onQualityChange]);

    useEffect(() => {
        frameRef.current = requestAnimationFrame(sample);
        return () => cancelAnimationFrame(frameRef.current);
    }, [sample]);

    const tier = score >= 70 ? "good" : score >= 40 ? "fair" : "poor";
    const cfg = SCORE_CONFIG[tier];

    return (
        <div className="glass-card p-3 border w-72" style={{ borderColor: "var(--border)" }}>
            <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold" style={{ color: "var(--text-secondary)" }}>Scan Quality</span>
                <span className={`text-sm font-bold ${cfg.color}`}>
                    {score}/100 — {cfg.label}
                </span>
            </div>

            {/* Score bar */}
            <div className="h-2 rounded-full overflow-hidden mb-2" style={{ background: "var(--border)" }}>
                <div
                    className={`h-full rounded-full transition-all duration-300 ${cfg.barColor}`}
                    style={{ width: `${score}%` }}
                />
            </div>

            {/* Tips */}
            {tips.length > 0 && (
                <div className="space-y-1">
                    {tips.map((tip, i) => (
                        <div key={i} className="flex items-center gap-1.5 text-xs" style={{ color: "var(--text-secondary)" }}>
                            <span className="text-amber-500">⚠</span>
                            <span>{tip}</span>
                        </div>
                    ))}
                </div>
            )}

            {tips.length === 0 && (
                <div className="flex items-center gap-1.5 text-xs text-green-600">
                    <span>✓</span>
                    <span>Scan conditions are optimal</span>
                </div>
            )}
        </div>
    );
}
