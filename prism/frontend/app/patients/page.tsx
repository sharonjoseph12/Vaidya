"use client";

import { useState } from "react";
import PatientStatsBar from "@/components/patients/PatientStatsBar";
import PatientManagementTable from "@/components/patients/PatientManagementTable";

interface PatientStats { total: number; highRisk: number; scannedToday: number; avgSessions: number; }

export default function PatientsPage() {
  const [stats, setStats] = useState<PatientStats>({ total: 0, highRisk: 0, scannedToday: 0, avgSessions: 0 });
  const [statsLoading, setStatsLoading] = useState(true);

  return (
    <div className="p-6 md:p-10 space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text)" }}>Patient Management</h1>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Search, filter, and manage all registered patients</p>
      </div>
      <PatientStatsBar stats={stats} loading={statsLoading} />
      <PatientManagementTable onStatsChange={s => { setStats(s); setStatsLoading(false); }} />
    </div>
  );
}
