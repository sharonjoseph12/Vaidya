"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { getPatient } from "@/lib/api";
import type { Patient } from "@/lib/types";

function PatientRecordBody({ patientId }: { patientId: string }) {
  const router = useRouter();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    getPatient(patientId)
      .then((data) => {
        if (cancelled) return;
        setPatient(data);
        setError(null);
        setLoading(false);
      })
      .catch((e) => {
        if (cancelled) return;
        setPatient(null);
        setError(e instanceof Error ? e.message : "Failed to load patient");
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [patientId]);

  if (loading) {
    return (
      <div className="p-6 md:p-10 max-w-3xl mx-auto">
        <div className="h-48 rounded-xl bg-gray-800/50 animate-pulse" />
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="p-6 md:p-10 max-w-3xl mx-auto space-y-4">
        <p className="text-red-300 text-sm">{error || "Patient not found"}</p>
        <button
          type="button"
          onClick={() => router.push("/dashboard/patients")}
          className="text-blue-400 text-sm hover:underline"
        >
          ← Back to patients
        </button>
      </div>
    );
  }

  const d = patient.demographics;

  return (
    <div className="p-6 md:p-10 max-w-3xl mx-auto space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <button
            type="button"
            onClick={() => router.push("/dashboard/patients")}
            className="text-xs text-gray-500 hover:text-gray-300 mb-2"
          >
            ← Patients
          </button>
          <h1 className="text-2xl font-bold text-white">Patient record</h1>
          <p className="text-gray-500 text-xs font-mono mt-1">{patient.id}</p>
        </div>
        <Link
          href={`/scan?patientId=${encodeURIComponent(patient.id)}`}
          className="inline-flex items-center justify-center px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-xl text-sm font-medium text-white transition w-fit"
        >
          New scan
        </Link>
      </div>

      <div className="glass-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wide">Demographics</h2>
        {d ? (
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-gray-500">Name</dt>
              <dd className="text-white">{d.name}</dd>
            </div>
            <div>
              <dt className="text-gray-500">Age / Sex</dt>
              <dd className="text-white">
                {d.age} · {d.sex}
              </dd>
            </div>
            <div className="sm:col-span-2">
              <dt className="text-gray-500">Location</dt>
              <dd className="text-white">{d.location || "—"}</dd>
            </div>
            {patient.abha_id && (
              <div className="sm:col-span-2">
                <dt className="text-gray-500">ABHA</dt>
                <dd className="text-blue-400">{patient.abha_id}</dd>
              </div>
            )}
          </dl>
        ) : (
          <p className="text-gray-500 text-sm">Demographics are not available for this record.</p>
        )}
        <div className="pt-4 border-t border-gray-800 text-xs text-gray-500">
          Sessions recorded: {patient.sessions_count ?? 0}
          {patient.last_session_date && (
            <span className="ml-2">· Last: {new Date(patient.last_session_date).toLocaleString()}</span>
          )}
        </div>
      </div>
    </div>
  );
}

export default function DashboardPatientDetailPage() {
  const params = useParams();
  const router = useRouter();
  const patientId = typeof params.patientId === "string" ? params.patientId.trim() : "";

  if (!patientId) {
    return (
      <div className="p-6 md:p-10 max-w-3xl mx-auto space-y-4">
        <p className="text-red-300 text-sm">Missing patient id</p>
        <button
          type="button"
          onClick={() => router.push("/dashboard/patients")}
          className="text-blue-400 text-sm hover:underline"
        >
          ← Back to patients
        </button>
      </div>
    );
  }

  return <PatientRecordBody key={patientId} patientId={patientId} />;
}
