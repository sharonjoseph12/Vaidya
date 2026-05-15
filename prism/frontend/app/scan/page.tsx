"use client";

import { Suspense, useState, useCallback, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import CameraCapture from "@/components/scan/CameraCapture";
import AudioCapture from "@/components/scan/AudioCapture";
import ScanProgress from "@/components/scan/ScanProgress";
import { startAnalysis, subscribeToProgress } from "@/lib/api";
import type { AnalysisProgressEvent } from "@/lib/types";
import { isUuid } from "@/lib/utils";

type PageState = "capture" | "processing" | "complete" | "error";

function ScanPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const patientIdRaw = searchParams.get("patientId")?.trim() ?? "";
  const patientId = useMemo(
    () => (patientIdRaw && isUuid(patientIdRaw) ? patientIdRaw : ""),
    [patientIdRaw],
  );

  const [pageState, setPageState] = useState<PageState>("capture");
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isRecordingAudio, setIsRecordingAudio] = useState(false);
  const [captureKey, setCaptureKey] = useState(0);
  const [stage, setStage] = useState("queued");
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");

  const handleScanningStart = useCallback(() => {
    setIsRecordingAudio(true);
  }, []);

  const handleVideoComplete = useCallback((blob: Blob) => {
    setVideoBlob(blob);
    setIsRecordingAudio(false);
  }, []);

  const handleAudioComplete = useCallback((blob: Blob) => {
    setAudioBlob(blob);
  }, []);

  const handleSubmit = async () => {
    if (!videoBlob || !patientId) return;
    setPageState("processing");

    try {
      const videoFile = new File([videoBlob], "scan.webm", { type: "video/webm" });
      const audioFile = audioBlob ? new File([audioBlob], "audio.webm", { type: "audio/webm" }) : undefined;

      const response = await startAnalysis(patientId, audioFile, videoFile);

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

  if (!patientId) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-8 gradient-bg">
        <div className="text-center max-w-md glass-card p-8 border border-gray-800 rounded-2xl">
          <h1 className="text-2xl font-bold text-white mb-2">Select a patient</h1>
          <p className="text-gray-400 text-sm mb-6">
            Each scan must be linked to a registered patient. Register someone new or pick a patient from your list,
            then open <span className="font-mono text-gray-300">/scan?patientId=…</span> from there.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/patient/new"
              className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 rounded-xl text-white text-sm font-medium text-center transition"
            >
              Register patient
            </Link>
            <Link
              href="/dashboard/patients"
              className="px-5 py-2.5 border border-gray-600 hover:bg-gray-800 rounded-xl text-gray-200 text-sm font-medium text-center transition"
            >
              Patient list
            </Link>
          </div>
          <Link href="/dashboard" className="inline-block mt-6 text-sm text-gray-500 hover:text-gray-300">
            ← Back to dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 gradient-bg">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
          Passive Health Scan
        </h1>
        <p className="text-gray-400 mt-2">Hold the phone facing the patient for 30 seconds</p>
        <p className="text-xs text-gray-500 mt-2 font-mono">Patient {patientId.slice(0, 8)}…</p>
      </div>

      {pageState === "capture" && (
        <div className="flex flex-col items-center gap-8">
          <CameraCapture
            key={captureKey}
            onComplete={handleVideoComplete}
            onScanningStart={handleScanningStart}
          />
          <AudioCapture key={captureKey} onComplete={handleAudioComplete} isRecording={isRecordingAudio} />

          {videoBlob && (
            <button
              type="button"
              onClick={handleSubmit}
              className="px-10 py-3 bg-gradient-to-r from-blue-600 to-cyan-500 rounded-xl font-semibold text-white hover:shadow-lg hover:shadow-blue-500/25 transition-all"
            >
              Analyze Scan →
            </button>
          )}
        </div>
      )}

      {pageState === "processing" && (
        <ScanProgress stage={stage} progress={progress} message={message} />
      )}

      {pageState === "complete" && (
        <div className="text-center">
          <div className="text-6xl mb-4">✅</div>
          <h2 className="text-2xl font-bold text-green-400">Analysis Complete</h2>
          <p className="text-gray-400 mt-2">Redirecting to results...</p>
        </div>
      )}

      {pageState === "error" && (
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-red-400">Analysis Failed</h2>
          <button
            type="button"
            onClick={() => {
              setPageState("capture");
              setVideoBlob(null);
              setAudioBlob(null);
              setIsRecordingAudio(false);
              setCaptureKey((k) => k + 1);
            }}
            className="mt-4 px-6 py-2 border border-gray-600 rounded-lg hover:bg-gray-800 transition-all"
          >
            Try Again
          </button>
        </div>
      )}
    </div>
  );
}

export default function ScanPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen flex items-center justify-center gradient-bg text-gray-400 text-sm">
          Loading scan…
        </div>
      }
    >
      <ScanPageContent />
    </Suspense>
  );
}
