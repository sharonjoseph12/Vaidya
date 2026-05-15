"use client";

import { useRef, useState, useEffect } from "react";
import { pickAudioMimeType } from "@/lib/mediaRecorder";

interface AudioCaptureProps {
  onComplete: (audioBlob: Blob) => void;
  isRecording: boolean;
}

const RECORDER_SLICE_MS = 250;

export default function AudioCapture({ onComplete, isRecording }: AudioCaptureProps) {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const chunksRef = useRef<Blob[]>([]);
  const animFrameRef = useRef<number>(0);
  const [level, setLevel] = useState(0);
  const [started, setStarted] = useState(false);
  const [micError, setMicError] = useState<string | null>(null);

  useEffect(() => {
    if (!isRecording) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        try {
          mediaRecorderRef.current.stop();
        } catch {
          /* already stopped */
        }
      }
      mediaRecorderRef.current = null;
      cancelAnimationFrame(animFrameRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      void audioContextRef.current?.close().catch(() => {});
      audioContextRef.current = null;
      analyserRef.current = null;
      queueMicrotask(() => setStarted(false));
      return;
    }

    let cancelled = false;
    queueMicrotask(() => setMicError(null));

    void (async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;

        const ctx = new AudioContext();
        audioContextRef.current = ctx;
        await ctx.resume().catch(() => {});

        const source = ctx.createMediaStreamSource(stream);
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 256;
        source.connect(analyser);
        analyserRef.current = analyser;

        chunksRef.current = [];
        const mime = pickAudioMimeType();
        let recorder: MediaRecorder;
        try {
          recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
        } catch {
          recorder = new MediaRecorder(stream);
        }

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };
        recorder.onstop = () => {
          const outType = recorder.mimeType && recorder.mimeType.length > 0 ? recorder.mimeType : "audio/webm";
          const blob = new Blob(chunksRef.current, { type: outType });
          stream.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
          void ctx.close().catch(() => {});
          audioContextRef.current = null;
          analyserRef.current = null;
          onComplete(blob);
        };

        recorder.start(RECORDER_SLICE_MS);
        mediaRecorderRef.current = recorder;
        setStarted(true);
      } catch (e) {
        if (!cancelled) {
          setMicError(e instanceof Error ? e.message : "Microphone error");
        }
      }
    })();

    return () => {
      cancelled = true;
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
        try {
          mediaRecorderRef.current.stop();
        } catch {
          /* noop */
        }
      }
      mediaRecorderRef.current = null;
      cancelAnimationFrame(animFrameRef.current);
      streamRef.current?.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
      void audioContextRef.current?.close().catch(() => {});
      audioContextRef.current = null;
      analyserRef.current = null;
      queueMicrotask(() => setStarted(false));
    };
  }, [isRecording, onComplete]);

  useEffect(() => {
    if (!started || !analyserRef.current || !canvasRef.current) return;

    const analyser = analyserRef.current;
    const canvas = canvasRef.current;
    const ctx2d = canvas.getContext("2d");
    if (!ctx2d) return;
    const graphics = ctx2d;

    const data = new Uint8Array(analyser.frequencyBinCount);

    function draw() {
      analyser.getByteFrequencyData(data);
      const avg = data.reduce((a, b) => a + b, 0) / data.length;
      setLevel(avg / 255);

      graphics.clearRect(0, 0, canvas.width, canvas.height);
      const barWidth = canvas.width / data.length;

      for (let i = 0; i < data.length; i++) {
        const barHeight = (data[i] / 255) * canvas.height;
        const hue = 210 + (data[i] / 255) * 30;
        graphics.fillStyle = `hsl(${hue}, 80%, 55%)`;
        graphics.fillRect(i * barWidth, canvas.height - barHeight, barWidth - 1, barHeight);
      }
      animFrameRef.current = requestAnimationFrame(draw);
    }
    draw();

    return () => cancelAnimationFrame(animFrameRef.current);
  }, [started]);

  return (
    <div className="glass-card p-4 w-80">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-3 h-3 rounded-full ${started ? "bg-red-500 animate-pulse" : "bg-gray-600"}`} />
        <span className="text-sm text-gray-400">
          {micError
            ? "Microphone blocked"
            : started
              ? "Recording audio…"
              : isRecording
                ? "Starting microphone…"
                : "Microphone idle (starts with video)"}
        </span>
      </div>

      {micError && <p className="text-xs text-red-400 mb-2">{micError}</p>}

      <canvas ref={canvasRef} width={280} height={60} className="w-full rounded-lg bg-gray-900/50" />

      <div className="mt-2 h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-100"
          style={{ width: `${level * 100}%` }}
        />
      </div>
    </div>
  );
}
