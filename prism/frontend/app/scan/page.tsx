"use client";

import { useState, useCallback, useRef, Suspense, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import CameraCapture from "@/components/scan/CameraCapture";
import AudioCapture from "@/components/scan/AudioCapture";
import ScanProgress from "@/components/scan/ScanProgress";
import CoughDetectionPanel from "@/components/scan/CoughDetectionPanel";
import ScanResultsPanel from "@/components/scan/ScanResultsPanel";
import LiveVitalsPanel from "@/components/scan/LiveVitalsPanel";
import SymptomQuestionnaire, { type SymptomAnswer } from "@/components/scan/SymptomQuestionnaire";
import ScanQualityIndicator from "@/components/scan/ScanQualityIndicator";
import { startAnalysis, subscribeToProgress, getResults } from "@/lib/api";
import type { AnalysisProgressEvent, DiagnosticResult } from "@/lib/types";
import type { RPPGVitals } from "@/lib/rppg";
import { isUuid } from "@/lib/utils";

type PageState = "questionnaire" | "capture" | "processing" | "results" | "error";

function ScanPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const patientIdRaw = searchParams.get("patientId")?.trim() ?? "demo-patient-id";
  const patientId = useMemo(
    () => (patientIdRaw === "demo-patient-id" || isUuid(patientIdRaw) ? patientIdRaw : ""),
    [patientIdRaw],
  );

  const [pageState, setPageState] = useState<PageState>("questionnaire");
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isRecordingAudio, setIsRecordingAudio] = useState(false);
  const [isCameraRecording, setIsCameraRecording] = useState(false);
  const [captureKey, setCaptureKey] = useState(0);
  const [stage, setStage] = useState("queued");
  const [progress, setProgress] = useState(0);
  const [message, setMessage] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [scanResult, setScanResult] = useState<DiagnosticResult | null>(null);
  const [resultsError, setResultsError] = useState<string | undefined>();
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null);
  const [patientFeatures, setPatientFeatures] = useState<Record<string, unknown>>({});
  const [liveVitals, setLiveVitals] = useState<RPPGVitals | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const handleQuestionnaireComplete = useCallback((answers: SymptomAnswer) => {
    setPatientFeatures(answers as unknown as Record<string, unknown>);
    setPageState("capture");
  }, []);

  const handleScanningStart = useCallback(() => {
    setIsRecordingAudio(true);
    setIsCameraRecording(true);
  }, []);

  const handleVideoComplete = useCallback((blob: Blob) => {
    setVideoBlob(blob);
    setIsRecordingAudio(false);
    setIsCameraRecording(false);
  }, []);

  const handleAudioComplete = useCallback((blob: Blob) => {
    setAudioBlob(blob);
  }, []);

  const handleAnalyserReady = useCallback((analyser: AnalyserNode) => {
    setAnalyserNode(analyser);
  }, []);

  const handleVitalsUpdate = useCallback((vitals: RPPGVitals) => {
    setLiveVitals(vitals);
  }, []);

  const handleSubmit = async () => {
    if (!videoBlob || !patientId) return;
    setPageState("processing");

    // Merge live rPPG vitals into patient features so backend can use them
    const enrichedFeatures = {
      ...patientFeatures,
      ...(liveVitals?.hr != null ? { measured_hr: liveVitals.hr } : {}),
      ...(liveVitals?.spo2 != null ? { measured_spo2: liveVitals.spo2 } : {}),
      ...(liveVitals?.hrv_rmssd != null ? { measured_hrv: liveVitals.hrv_rmssd } : {}),
      ...(liveVitals?.rr != null ? { measured_rr: liveVitals.rr } : {}),
    };

    try {
      const videoFile = new File([videoBlob], "scan.webm", { type: "video/webm" });
      const audioFile = audioBlob ? new File([audioBlob], "audio.webm", { type: "audio/webm" }) : undefined;

      const response = await startAnalysis(patientId, audioFile, videoFile, enrichedFeatures);
      setSessionId(response.session_id);

      subscribeToProgress(
        response.session_id,
        async (event: AnalysisProgressEvent) => {
          setStage(event.stage);
          setProgress(event.progress);
          setMessage(event.message);

          if (event.stage === "complete") {
            try {
              const responseData = await getResults(response.session_id);
              let result: DiagnosticResult | null = null;
              if ("status" in responseData && responseData.status === "completed") {
                result = responseData as DiagnosticResult;
              } else if (!("status" in responseData)) {
                result = responseData as DiagnosticResult;
              }

              // Inject real rPPG vitals into the result so ScanResultsPanel shows them
              if (result && liveVitals && result.sense_results) {
                result.sense_results.rppg = {
                  hr: liveVitals.hr ?? result.sense_results.rppg?.hr ?? 0,
                  spo2: liveVitals.spo2 ?? result.sense_results.rppg?.spo2 ?? 0,
                  hrv_rmssd: liveVitals.hrv_rmssd ?? result.sense_results.rppg?.hrv_rmssd ?? 0,
                  rr: liveVitals.rr ?? result.sense_results.rppg?.rr ?? 0,
                  confidence: { overall: liveVitals.confidence },
                };
              }

              setScanResult(result);
            } catch (err: unknown) {
              setResultsError(err instanceof Error ? err.message : "Failed to load results");
            }
            setPageState("results");
          }
          if (event.stage === "error") setPageState("error");
        },
        () => setPageState("error"),
      );
    } catch {
      setPageState("error");
    }
  };

  const handleScanAgain = useCallback(() => {
    setPageState("questionnaire");
    setVideoBlob(null);
    setAudioBlob(null);
    setScanResult(null);
    setResultsError(undefined);
    setSessionId("");
    setStage("queued");
    setProgress(0);
    setMessage("");
    setAnalyserNode(null);
    setPatientFeatures({});
    setLiveVitals(null);
    setIsCameraRecording(false);
    setCaptureKey((k) => k + 1);
  }, []);

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
    <div className="min-h-screen flex flex-col items-center justify-center p-6 gradient-bg">
      {/* Header */}
      <div className="text-center mb-6">
        <h1 className="text-3xl font-bold text-blue-600">Passive Health Scan</h1>
        <p className="mt-1 text-sm" style={{ color: "var(--text-secondary)" }}>
          {pageState === "questionnaire" && "Step 1 of 3 — Symptom check"}
          {pageState === "capture" && "Step 2 of 3 — Capture"}
          {pageState === "processing" && "Step 3 of 3 — Analysing"}
          {pageState === "results" && "Analysis complete"}
        </p>
      </div>

      {/* Step indicator */}
      {(pageState === "questionnaire" || pageState === "capture" || pageState === "processing") && (
        <div className="flex items-center gap-2 mb-6">
          {["questionnaire", "capture", "processing"].map((step, i) => {
            const steps = ["questionnaire", "capture", "processing"];
            const currentIdx = steps.indexOf(pageState);
            const isDone = i < currentIdx;
            const isCurrent = i === currentIdx;
            return (
              <div key={step} className="flex items-center gap-2">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${isDone ? "bg-green-500 text-white" : isCurrent ? "bg-blue-600 text-white" : ""
                    }`}
                  style={!isDone && !isCurrent ? { background: "var(--surface-hover)", color: "var(--text-muted)" } : undefined}
                >
                  {isDone ? "✓" : i + 1}
                </div>
                {i < 2 && (
                  <div
                    className={`w-8 h-0.5 ${isDone ? "bg-green-400" : ""}`}
                    style={!isDone ? { background: "var(--border)" } : undefined}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Questionnaire */}
      {pageState === "questionnaire" && (
        <SymptomQuestionnaire
          onComplete={handleQuestionnaireComplete}
          onSkip={() => setPageState("capture")}
        />
      )}

      {/* Capture */}
      {pageState === "capture" && (
        <div className="flex flex-col items-center gap-4 w-full max-w-2xl">
          <CameraCapture
            key={`camera-${captureKey}`}
            onComplete={handleVideoComplete}
            onScanningStart={handleScanningStart}
            videoRef={videoRef}
          />

          {/* Live rPPG vitals — shows real HR, SpO2, HRV, RR from camera */}
          <LiveVitalsPanel
            videoRef={videoRef}
            isRecording={isCameraRecording}
            onVitalsUpdate={handleVitalsUpdate}
          />

          {/* Scan quality */}
          <ScanQualityIndicator videoRef={videoRef} analyserNode={analyserNode} />

          {/* Audio + Cough Detection side by side */}
          <div className="flex flex-col md:flex-row gap-4 items-start justify-center w-full">
            <AudioCapture
              key={`audio-${captureKey}`}
              onComplete={handleAudioComplete}
              isRecording={isRecordingAudio}
              onAnalyserReady={handleAnalyserReady}
            />
            <CoughDetectionPanel
              isRecording={isRecordingAudio}
              audioAnalyser={analyserNode}
            />
          </div>

          {videoBlob && (
            <button
              type="button"
              onClick={handleSubmit}
              className="px-10 py-3 bg-blue-600 hover:bg-blue-700 rounded-xl font-semibold text-white shadow-md hover:shadow-lg transition-all"
            >
              Analyze Scan →
            </button>
          )}
        </div>
      )}

      {/* Processing */}
      {pageState === "processing" && (
        <ScanProgress stage={stage} progress={progress} message={message} />
      )}

      {/* Results */}
      {pageState === "results" && (
        <ScanResultsPanel
          result={scanResult}
          sessionId={sessionId}
          onScanAgain={handleScanAgain}
          error={resultsError}
        />
      )}

      {/* Error */}
      {pageState === "error" && (
        <div className="text-center glass-card p-8">
          <div className="text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-red-600">Analysis Failed</h2>
          <p className="mt-2 text-sm" style={{ color: "var(--text-secondary)" }}>Something went wrong during analysis.</p>
          <button
            onClick={handleScanAgain}
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
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center gradient-bg">
        <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
      </div>
    }>
      <ScanPageContent />
    </Suspense>
  );
}
