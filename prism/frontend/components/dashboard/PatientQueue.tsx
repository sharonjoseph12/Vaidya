"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getPatients } from "@/lib/api";
import type { PatientList } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function PatientQueue() {
  const router = useRouter();
  const [data, setData] = useState<PatientList | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getPatients(1, 10)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="glass-card p-6 h-96 animate-pulse" style={{ background: "var(--surface-hover)" }}></div>;
  }

  return (
    <div className="glass-card overflow-hidden flex flex-col h-[500px]">
      <div
        className="p-5 border-b flex justify-between items-center"
        style={{ borderColor: "var(--border)", background: "var(--surface-hover)" }}
      >
        <h3 className="text-base font-bold flex items-center gap-2" style={{ color: "var(--text)" }}>
          👥 Patient Queue
        </h3>
        <button
          onClick={() => router.push("/patient/new")}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition"
        >
          + New Patient
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {data?.patients.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center" style={{ color: "var(--text-muted)" }}>
            <div className="text-4xl mb-2">📋</div>
            <p className="text-sm">No patients in queue</p>
          </div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead
              className="text-xs uppercase sticky top-0"
              style={{ background: "var(--surface-hover)", color: "var(--text-secondary)" }}
            >
              <tr>
                <th className="px-4 py-3 rounded-tl-lg">ID</th>
                <th className="px-4 py-3">ABHA / Demographics</th>
                <th className="px-4 py-3">Last Scan</th>
                <th className="px-4 py-3 text-right rounded-tr-lg">Action</th>
              </tr>
            </thead>
            <tbody>
              {data?.patients.map((p) => (
                <tr
                  key={p.id}
                  className="border-b transition-colors group cursor-pointer"
                  style={{ borderColor: "var(--border)" }}
                  onClick={() => router.push(`/patient/${p.id}`)}
                  onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                  onMouseLeave={e => (e.currentTarget.style.background = "")}
                >
                  <td className="px-4 py-4 font-mono text-xs" style={{ color: "var(--text-muted)" }}>
                    {p.id.split("-")[0]}
                  </td>
                  <td className="px-4 py-4">
                    {p.abha_id ? (
                      <div className="text-blue-600 font-medium text-sm">{p.abha_id}</div>
                    ) : (
                      <div className="italic text-sm" style={{ color: "var(--text-muted)" }}>No ABHA linked</div>
                    )}
                    {p.demographics && (
                      <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                        {p.demographics.age} {p.demographics.sex} • {p.demographics.location}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-4 text-sm" style={{ color: "var(--text-secondary)" }}>
                    {p.last_session_date ? formatDate(p.last_session_date) : "No scans"}
                  </td>
                  <td className="px-4 py-4 text-right flex justify-end gap-2">
                    <button
                      onClick={(e) => { e.stopPropagation(); router.push(`/scan?patientId=${p.id}`); }}
                      className="px-2 py-1 bg-green-50 text-green-700 border border-green-200 hover:bg-green-100 rounded text-xs transition"
                    >
                      Scan 📷
                    </button>
                    <button className="text-blue-600 group-hover:text-blue-700 font-medium text-xs">
                      View →
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {data && data.total > 10 && (
        <div
          className="p-3 border-t text-center text-xs"
          style={{ borderColor: "var(--border)", background: "var(--surface-hover)", color: "var(--text-muted)" }}
        >
          Showing 10 of {data.total} patients
        </div>
      )}
    </div>
  );
}
