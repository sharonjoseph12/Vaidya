"use client";

import { useRef, useState, useEffect, useCallback } from "react";

interface AudioCaptureProps {
  onComplete: (audioBlob: Blob) => void;
  isRecording: boolean;
  onAnalyserReady?: (analyser: AnalyserNode) => void;
}

export default function AudioCapture({ onComplete, isRecording, onAnalyserReady }: AudioCaptureProps) {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chunksRef = useRef<Blob[]>([]);
  const animFrameRef = useRef<number>(0);
  const [level, setLevel] = useState(0);
  const [started, setStarted] = useState(false);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const ctx = new window.AudioContext();
      if (ctx.state === "suspended") await ctx.resume();
      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 2048; // larger = better time-domain resolution for cough detection
      source.connect(analyser);
      analyserRef.current = analyser;
      if (onAnalyserReady) onAnalyserReady(analyser); // fire immediately so CoughDetectionPanel starts

      chunksRef.current = [];
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        onComplete(blob);
        stream.getTracks().forEach((t) => t.stop());
      };
      recorder.start();
      mediaRecorderRef.current = recorder;
      setStarted(true);
    } catch {
      console.error("Microphone access denied");
    }
  }, [onComplete, onAnalyserReady]);

  useEffect(() => {
    if (isRecording && !started) startRecording();
    if (!isRecording && started) {
      mediaRecorderRef.current?.stop();
      cancelAnimationFrame(animFrameRef.current);
      setStarted(false);
    }
  }, [isRecording, started, startRecording]);

  useEffect(() => {
    if (!started || !analyserRef.current || !canvasRef.current) return;
    const analyser = analyserRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d")!;
    const data = new Uint8Array(analyser.frequencyBinCount);

    function draw() {
      analyser.getByteFrequencyData(data);
      const avg = data.reduce((a, b) => a + b, 0) / data.length;
      setLevel(avg / 255);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const isDark = document.documentElement.classList.contains("dark");
      ctx.fillStyle = isDark ? "#0f172a" : "#f8fafc";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const barWidth = canvas.width / data.length;
      for (let i = 0; i < data.length; i++) {
        const barHeight = (data[i] / 255) * canvas.height;
        const intensity = data[i] / 255;
        ctx.fillStyle = `hsl(${210 + intensity * 30}, 70%, ${45 + intensity * 15}%)`;
        ctx.fillRect(i * barWidth, canvas.height - barHeight, barWidth - 1, barHeight);
      }
      animFrameRef.current = requestAnimationFrame(draw);
    }
    draw();
    return () => cancelAnimationFrame(animFrameRef.current);
  }, [started]);

  return (
    <div className="glass-card p-4 w-80">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-3 h-3 rounded-full ${started ? "bg-red-500 animate-pulse" : "bg-slate-300"}`} />
        <span className="text-sm text-slate-600 font-medium">
          {started ? "Recording audio..." : "Microphone ready"}
        </span>
      </div>

      <canvas
        ref={canvasRef}
        width={280}
        height={60}
        className="w-full rounded-lg border border-slate-200"
      />

      <div className="mt-2 h-1.5 bg-slate-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-100"
          style={{ width: `${level * 100}%` }}
        />
      </div>
    </div>
  );
}
