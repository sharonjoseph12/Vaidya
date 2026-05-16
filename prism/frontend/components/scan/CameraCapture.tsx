"use client";

import { useRef, useState, useEffect, useCallback } from "react";

type ScanState = "IDLE" | "DETECTING_FACE" | "SCANNING" | "COMPLETE" | "ERROR";

interface CameraCaptureProps {
  onComplete: (videoBlob: Blob) => void;
  onStartRecording?: () => void;
  duration?: number;
  videoRef?: React.RefObject<HTMLVideoElement | null>;
}

export default function CameraCapture({ onComplete, onStartRecording, duration = 30, videoRef: externalVideoRef }: CameraCaptureProps) {
  const internalVideoRef = useRef<HTMLVideoElement>(null);
  const videoRef = externalVideoRef || internalVideoRef;
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [state, setState] = useState<ScanState>("IDLE");
  const [countdown, setCountdown] = useState(duration);
  const [faceDetected, setFaceDetected] = useState(false);
  const [progress, setProgress] = useState(0);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: 1280, height: 720 },
        audio: false,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setState("DETECTING_FACE");
      // Simulate face detection (replace with MediaPipe in production)
      setTimeout(() => setFaceDetected(true), 1500);
    } catch {
      setState("ERROR");
    }
  }, []);

  const startRecording = useCallback(() => {
    const stream = videoRef.current?.srcObject as MediaStream;
    if (!stream) return;

    chunksRef.current = [];
    const recorder = new MediaRecorder(stream, { mimeType: "video/webm" });
    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: "video/webm" });
      onComplete(blob);
      setState("COMPLETE");
    };
    recorder.start();
    mediaRecorderRef.current = recorder;
    setState("SCANNING");
    if (onStartRecording) onStartRecording();
  }, [onComplete, onStartRecording]);

  // Countdown timer
  useEffect(() => {
    if (state !== "SCANNING") return;
    const interval = setInterval(() => {
      setCountdown((prev) => {
        const next = prev - 1;
        setProgress(((duration - next) / duration) * 100);
        if (next <= 0) {
          mediaRecorderRef.current?.stop();
          clearInterval(interval);
        }
        return Math.max(0, next);
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [state, duration]);

  // Auto-start recording when face detected
  useEffect(() => {
    if (faceDetected && state === "DETECTING_FACE") startRecording();
  }, [faceDetected, state, startRecording]);

  // Cleanup
  useEffect(() => {
    return () => {
      const stream = videoRef.current?.srcObject as MediaStream;
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const ringColor = faceDetected
    ? "ring-green-500 shadow-[0_0_20px_rgba(22,163,74,0.3)]"
    : "ring-blue-400 shadow-[0_0_20px_rgba(37,99,235,0.2)]";

  return (
    <div className="flex flex-col items-center gap-6">
      {/* Camera viewport */}
      <div className={`relative w-80 h-80 rounded-full overflow-hidden ring-4 ${ringColor} transition-all duration-500`}>
        <video ref={videoRef} className="w-full h-full object-cover scale-x-[-1]" playsInline muted />
        {state === "SCANNING" && (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-6xl font-bold text-white drop-shadow-lg">{countdown}</span>
          </div>
        )}
        {state === "COMPLETE" && (
          <div className="absolute inset-0 bg-green-500/30 flex items-center justify-center">
            <span className="text-4xl">✓</span>
          </div>
        )}
      </div>

      {state === "SCANNING" && (
        <div className="w-80 h-2 bg-slate-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 transition-all duration-1000 ease-linear"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Status */}
      <div className="text-center">
        {state === "IDLE" && (
          <button
            onClick={startCamera}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold transition-all shadow-md hover:shadow-lg"
          >
            Start Scan
          </button>
        )}
        {state === "DETECTING_FACE" && (
          <p className="text-amber-600 animate-pulse font-medium">Detecting face...</p>
        )}
        {state === "SCANNING" && (
          <p className="text-blue-600 font-medium">Recording — hold still for {countdown}s</p>
        )}
        {state === "COMPLETE" && (
          <p className="text-green-600 font-semibold">Capture complete ✓</p>
        )}
        {state === "ERROR" && (
          <p className="text-red-600">Camera access denied. Please enable permissions.</p>
        )}
      </div>
    </div>
  );
}
