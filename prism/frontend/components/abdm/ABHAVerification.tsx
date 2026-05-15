"use client";

import { useState } from "react";
import { verifyABHA } from "@/lib/api";
import type { ABHAProfile } from "@/lib/types";

interface ABHAVerificationProps {
  onVerified: (profile: ABHAProfile) => void;
}

export default function ABHAVerification({ onVerified }: ABHAVerificationProps) {
  const [abhaId, setAbhaId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState<"idle" | "verifying" | "success" | "error">("idle");

  const handleVerify = async () => {
    if (!abhaId) return;
    setLoading(true);
    setError("");
    setStatus("verifying");

    try {
      const profile = await verifyABHA(abhaId);
      if (profile.verified) {
        setStatus("success");
        onVerified(profile);
      } else {
        setStatus("error");
        setError("Invalid ABHA ID");
      }
    } catch (err) {
      setStatus("error");
      setError(err instanceof Error ? err.message : "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-5">
      <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
        <span className="text-blue-500">🛡️</span> ABHA Verification
      </h3>
      <p className="text-sm text-gray-400 mb-4">
        Enter Ayushman Bharat Health Account (ABHA) ID to fetch medical history.
      </p>

      <div className="flex gap-3">
        <input
          type="text"
          placeholder="14-digit ABHA ID (e.g., 91-0000-0000-0000)"
          value={abhaId}
          onChange={(e) => setAbhaId(e.target.value)}
          className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-blue-500 transition-colors"
        />
        <button
          onClick={handleVerify}
          disabled={loading || !abhaId}
          className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "Verifying..." : "Verify"}
        </button>
      </div>

      {status === "error" && (
        <p className="text-sm text-red-400 mt-2">{error}</p>
      )}

      {status === "success" && (
        <p className="text-sm text-green-400 mt-2 flex items-center gap-1">
          ✓ ABHA ID verified successfully
        </p>
      )}
    </div>
  );
}
