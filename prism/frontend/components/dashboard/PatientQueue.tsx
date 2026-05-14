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
    return <div className="glass-card p-6 h-96 animate-pulse bg-gray-800/50"></div>;
  }

  return (
    <div className="glass-card overflow-hidden flex flex-col h-[500px]">
      <div className="p-5 border-b border-gray-800 flex justify-between items-center bg-gray-900/50">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          👥 Patient Queue
        </h3>
        <button 
          onClick={() => router.push("/patient/new")}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm font-medium transition"
        >
          + New Patient
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {data?.patients.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-gray-500">
            <div className="text-4xl mb-2">📋</div>
            <p>No patients in queue</p>
          </div>
        ) : (
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-gray-400 uppercase bg-gray-800/30 sticky top-0">
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
                  className="border-b border-gray-800/50 hover:bg-gray-800/30 transition-colors group cursor-pointer"
                  onClick={() => router.push(`/patient/${p.id}`)}
                >
                  <td className="px-4 py-4 font-mono text-gray-400">
                    {p.id.split("-")[0]}
                  </td>
                  <td className="px-4 py-4">
                    {p.abha_id ? (
                      <div className="text-blue-400 font-medium">{p.abha_id}</div>
                    ) : (
                      <div className="text-gray-500 italic">No ABHA linked</div>
                    )}
                    {p.demographics && (
                      <div className="text-xs text-gray-400 mt-1">
                        {p.demographics.age} {p.demographics.sex} • {p.demographics.location}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-4 text-gray-400">
                    {p.last_session_date ? formatDate(p.last_session_date) : "No scans"}
                  </td>
                  <td className="px-4 py-4 text-right">
                    <button className="text-blue-500 group-hover:text-blue-400 font-medium">
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
        <div className="p-3 border-t border-gray-800 text-center text-xs text-gray-500 bg-gray-900/50">
          Showing 10 of {data.total} patients
        </div>
      )}
    </div>
  );
}
