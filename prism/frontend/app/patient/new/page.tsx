"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import ABHAVerification from "@/components/abdm/ABHAVerification";
import HealthHistoryTimeline from "@/components/abdm/HealthHistoryTimeline";
import type { ABHAProfile, HealthRecord } from "@/lib/types";
import { createPatient } from "@/lib/api";

export default function NewPatientPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<ABHAProfile | null>(null);
  const [records, setRecords] = useState<HealthRecord[]>([]);
  const [loading, setLoading] = useState(false);

  const handleVerified = (verifiedProfile: ABHAProfile) => {
    setProfile(verifiedProfile);
    // Mock fetching records upon successful ABHA verification
    setRecords([
      { type: "DiagnosticReport", date: "2023-11-15", findings: "Sputum AFB positive. Started Category I DOTS.", codes: ["LOINC: 11528-7"] },
      { type: "Prescription", date: "2023-11-15", parameter: "Isoniazid", value: 300, unit: "mg", codes: [] },
      { type: "Discharge", date: "2022-04-10", findings: "Recovered from acute pneumonia.", codes: ["SNOMED: 233604007"] }
    ]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData(e.target as HTMLFormElement);
    const abhaRaw = formData.get("abha_id");
    const abha_id =
      typeof abhaRaw === "string" && abhaRaw.trim().length > 0 ? abhaRaw.trim() : undefined;
    const age = parseInt(String(formData.get("age")), 10);
    const sexRaw = String(formData.get("sex") || "M");
    const sex = sexRaw === "F" || sexRaw === "O" ? sexRaw : "M";
    const name = String(profile?.name || formData.get("name") || "").trim() || "Unknown";
    const location = String(formData.get("location") || "");

    const payload: Record<string, unknown> = {
      consent_given: true,
      consent_purpose: "diagnostic_screening",
      demographics: {
        name,
        age: Number.isFinite(age) ? age : profile?.age ?? 0,
        sex,
        location,
      },
    };
    if (abha_id) payload.abha_id = abha_id;

    try {
      const created = await createPatient(payload);
      setTimeout(() => router.push(`/scan?patientId=${encodeURIComponent(created.id)}`), 1000);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen gradient-bg p-6 md:p-10 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">

        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold" style={{ color: "var(--text)" }}>Register Patient</h1>
            <p style={{ color: "var(--text-secondary)" }}>Link ABHA ID or enter demographics manually</p>
          </div>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 rounded-lg border transition"
            style={{ color: "var(--text-secondary)", borderColor: "var(--border)" }}
            onMouseEnter={e => (e.currentTarget.style.color = "var(--text)")}
            onMouseLeave={e => (e.currentTarget.style.color = "var(--text-secondary)")}
          >
            Cancel
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="space-y-8">
            <ABHAVerification onVerified={handleVerified} />

            <form onSubmit={handleSubmit} className="glass-card p-6">
              <h3 className="text-lg font-semibold mb-4" style={{ color: "var(--text)" }}>Patient Demographics</h3>

              <div className="space-y-4">
                {profile?.verified && (
                  <div className="bg-green-500/10 border border-green-500/30 p-3 rounded-lg text-sm text-green-400 mb-4 flex items-start gap-2">
                    <span>✓</span>
                    <div>Profile data populated from ABHA. Verify and complete missing fields.</div>
                  </div>
                )}

                <input type="hidden" name="abha_id" value={profile?.verified ? "91-1234-5678-9012" : ""} />

                <div>
                  <label className="block text-xs mb-1 uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>Full Name</label>
                  <input
                    name="name"
                    defaultValue={profile?.name || ""}
                    required
                    className="w-full rounded-lg px-4 py-2 border focus:outline-none focus:border-blue-500"
                    style={{ background: "var(--surface)", color: "var(--text)", borderColor: "var(--border)" }}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs mb-1 uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>Age</label>
                    <input
                      name="age"
                      type="number"
                      defaultValue={profile?.age || ""}
                      required
                      className="w-full rounded-lg px-4 py-2 border focus:outline-none focus:border-blue-500"
                      style={{ background: "var(--surface)", color: "var(--text)", borderColor: "var(--border)" }}
                    />
                  </div>
                  <div>
                    <label className="block text-xs mb-1 uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>Sex</label>
                    <select
                      name="sex"
                      defaultValue={profile?.gender || "M"}
                      required
                      className="w-full rounded-lg px-4 py-2 border focus:outline-none focus:border-blue-500"
                      style={{ background: "var(--surface)", color: "var(--text)", borderColor: "var(--border)" }}
                    >
                      <option value="M">Male</option>
                      <option value="F">Female</option>
                      <option value="O">Other</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs mb-1 uppercase tracking-wide" style={{ color: "var(--text-secondary)" }}>Location / PIN</label>
                  <input
                    name="location"
                    placeholder="e.g., Rural District, 400001"
                    required
                    className="w-full rounded-lg px-4 py-2 border focus:outline-none focus:border-blue-500"
                    style={{ background: "var(--surface)", color: "var(--text)", borderColor: "var(--border)" }}
                  />
                </div>

                <div className="pt-4 border-t" style={{ borderColor: "var(--border)" }}>
                  <label className="flex items-start gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      required
                      className="mt-1 w-4 h-4 rounded text-blue-600 focus:ring-blue-500"
                      style={{ borderColor: "var(--border)", background: "var(--surface)" }}
                    />
                    <span className="text-sm" style={{ color: "var(--text-secondary)" }}>I confirm patient consent obtained for multimodal screening and demographic encryption as per DPDP Act 2023.</span>
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold transition-colors disabled:opacity-50 mt-6"
                >
                  {loading ? "Saving..." : "Save & Proceed to Scan →"}
                </button>
              </div>
            </form>
          </div>

          <div className="space-y-8">
            <HealthHistoryTimeline records={records} />
          </div>
        </div>

      </div>
    </div>
  );
}
