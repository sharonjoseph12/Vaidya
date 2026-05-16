"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import { pickVideoMimeType } from "@/lib/mediaRecorder";

type ScanState = "IDLE" | "DETECTING_FACE" | "SCANNING" | "COMPLETE" | "ERROR";

interface CameraCaptureProps {
  onComplete: (videoBlob: Blob) => void;
  onStartRecording?: () => void;
  onScanningStart?: () => void;
  duration?: number;
  videoRef?: React.RefObject<HTMLVideoElement | null>;
}

const RECORDER_SLICE_MS = 250;

export default function CameraCapture({ onComplete, onScanningStart, onStartRecording, duration = 30, videoRef: externalVideoRef }: CameraCaptureProps) {
  const internalVideoRef = useRef<HTMLVideoElement>(null);
  const videoRef = externalVideoRef || internalVideoRef;
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [state, setState] = useState<ScanState>("IDLE");
  const [countdown, setCountdown] = useState(duration);
  const [faceDetected, setFaceDetected] = useState(false);
  const [progress, setProgress] = useState(0);
  const [errorDetail, setErrorDetail] = useState<string | null>(null);

  const startCamera = useCallback(async () => {
    setErrorDetail(null);
    try {
      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
          audio: false,
        });
      } catch {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      }
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setState("DETECTING_FACE");
      // Passive flow: treat "camera preview ready" as go-ahead (no separate face ML in this build).
      setFaceDetected(true);
    } catch (e) {
      setErrorDetail(e instanceof Error ? e.message : "Camera error");
      setState("ERROR");
    }
  }, []);

  const startRecording = useCallback(() => {
    const stream = videoRef.current?.srcObject as MediaStream | undefined;
    if (!stream) return;

    chunksRef.current = [];
    const mime = pickVideoMimeType();
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
      const outType = recorder.mimeType && recorder.mimeType.length > 0 ? recorder.mimeType : "video/webm";
      const blob = new Blob(chunksRef.current, { type: outType });
      stream.getTracks().forEach((t) => t.stop());
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      onComplete(blob);
      setState("COMPLETE");
    };

    setCountdown(duration);
    setProgress(0);
    onScanningStart?.();
    recorder.start(RECORDER_SLICE_MS);
    mediaRecorderRef.current = recorder;
    setState("SCANNING");
    onScanningStart?.();
    if (onStartRecording) onStartRecording();
  }, [duration, onComplete, onScanningStart, onStartRecording]);

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

  useEffect(() => {
    if (faceDetected && state === "DETECTING_FACE") startRecording();
  }, [faceDetected, state, startRecording]);

  useEffect(() => {
    const video = videoRef.current;
    return () => {
      const stream = video?.srcObject as MediaStream | undefined;
      stream?.getTracks().forEach((t) => t.stop());
      if (video) video.srcObject = null;
    };
  }, []);

  const ringColor =
    state === "IDLE"
      ? "ring-gray-700"
      : faceDetected
        ? "ring-green-500 shadow-[0_0_30px_rgba(34,197,94,0.4)]"
        : "ring-red-500 shadow-[0_0_30px_rgba(239,68,68,0.4)]";

  return (
    <div className="flex flex-col items-center gap-6">
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

      <div className="text-center max-w-sm">
        {state === "IDLE" && (
          <button
            type="button"
            onClick={startCamera}
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold transition-all shadow-md hover:shadow-lg"
          >
            Start camera
          </button>
        )}
        {state === "DETECTING_FACE" && (
          <p className="text-amber-400 animate-pulse font-medium">Preparing capture...</p>
        )}
        {state === "SCANNING" && (
          <p className="text-blue-400 font-medium">Recording video — hold still for {countdown}s</p>
        )}
        {state === "COMPLETE" && (
          <p className="text-green-400 font-semibold">Video capture complete ✓</p>
        )}
        {state === "ERROR" && (
          <div className="text-red-400 text-sm space-y-1">
            <p>Camera could not start. Allow camera access and use HTTPS or localhost.</p>
            {errorDetail && <p className="text-gray-500 font-mono text-xs">{errorDetail}</p>}
          </div>
        )}
      </div>
    </div>
  );
}
