"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import CameraCapture from "@/components/scan/CameraCapture";
import AudioCapture from "@/components/scan/AudioCapture";
import ScanProgress from "@/components/scan/ScanProgress";
import { startAnalysis, subscribeToProgress } from "@/lib/api";
import type { AnalysisProgressEvent } from "@/lib/types";

type PageState = "capture" | "processing" | "complete" | "error";

export default function ScanPage() {
  const router = useRouter();
  const [pageState, setPageState] = useState<PageState>("capture");
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isRecordingAudio, setIsRecordingAudio] = useState(false);
  const [stage, setStage] = useState("queued");
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");
  const [sessionId, setSessionId] = useState("");

  const handleVideoComplete = useCallback((blob: Blob) => {
    setVideoBlob(blob);
    setIsRecordingAudio(false);
  }, []);

  const handleAudioComplete = useCallback((blob: Blob) => {
    setAudioBlob(blob);
  }, []);

  const handleSubmit = async () => {
    if (!videoBlob) return;
    setPageState("processing");

    try {
      const videoFile = new File([videoBlob], "scan.webm", { type: "video/webm" });
      const audioFile = audioBlob ? new File([audioBlob], "audio.webm", { type: "audio/webm" }) : undefined;

      // TODO: Use actual patient ID from context
      const response = await startAnalysis("demo-patient-id", audioFile, videoFile);
      setSessionId(response.session_id);

      // Subscribe to SSE progress
      subscribeToProgress(
        response.session_id,
        (event: AnalysisProgressEvent) => {
          setStage(event.stage);
          setProgress(event.progress);
          setMessage(event.message);
          if (event.stage === "complete") {
            setPageState("complete");
            setTimeout(() => router.push(`/patient/${response.session_id}`), 1500);
          }
          if (event.stage === "error") setPageState("error");
        },
        () => setPageState("error"),
      );
    } catch {
      setPageState("error");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 gradient-bg">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          Passive Health Scan
        </h1>
        <p className="text-gray-400 mt-2">Hold the phone facing the patient for 30 seconds</p>
      </div>

      {/* Capture phase */}
      {pageState === "capture" && (
        <div className="flex flex-col items-center gap-8">
          <CameraCapture onComplete={handleVideoComplete} />
          <AudioCapture onComplete={handleAudioComplete} isRecording={isRecordingAudio} />

          {videoBlob && (
            <button
              onClick={handleSubmit}
              className="px-10 py-3 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-xl font-semibold text-white hover:shadow-lg hover:shadow-blue-500/25 transition-all"
            >
              Analyze Scan →
            </button>
          )}
        </div>
      )}

      {/* Processing phase */}
      {pageState === "processing" && (
        <ScanProgress stage={stage} progress={progress} message={message} />
      )}

      {/* Complete phase */}
      {pageState === "complete" && (
        <div className="text-center">
          <div className="text-6xl mb-4">✅</div>
          <h2 className="text-2xl font-bold text-green-400">Analysis Complete</h2>
          <p className="text-gray-400 mt-2">Redirecting to results...</p>
        </div>
      )}

      {/* Error phase */}
      {pageState === "error" && (
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-red-400">Analysis Failed</h2>
          <button
            onClick={() => { setPageState("capture"); setVideoBlob(null); }}
            className="mt-4 px-6 py-2 border border-gray-600 rounded-lg hover:bg-gray-800 transition-all"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}
