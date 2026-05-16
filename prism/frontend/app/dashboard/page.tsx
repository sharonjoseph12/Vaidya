"use client";

import Link from "next/link";
import StatsOverview from "@/components/dashboard/StatsOverview";
import RecentScans from "@/components/dashboard/RecentScans";
import SubsystemHealth from "@/components/dashboard/SubsystemHealth";
import PatientQueue from "@/components/dashboard/PatientQueue";

const quickActions = [
  { href: "/scan", icon: "📷", label: "New Passive Scan", desc: "Start a 30s multimodal assessment", accent: "#2563eb" },
  { href: "/patients", icon: "👥", label: "Patient Management", desc: "Search, filter, and manage patients", accent: "#16a34a" },
  { href: "/federated", icon: "🌐", label: "FL Operations", desc: "Monitor nodes, privacy budget, trigger rounds", accent: "#d97706" },
  { href: "/review", icon: "🩺", label: "Review Queue", desc: "Approve or override AI diagnoses", accent: "#7c3aed" },
  { href: "/patient/new", icon: "🆕", label: "Register Patient", desc: "Verify ABHA ID & fetch history", accent: "#0891b2" },
];

export default function DashboardPage() {
  return (
    <div className="p-6 md:p-10 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text)" }}>Dashboard</h1>
        <p className="text-sm" style={{ color: "var(--text-secondary)" }}>Welcome back. Here is the current system status.</p>
      </div>

      <StatsOverview />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="lg:col-span-1">
          <PatientQueue />
        </div>
        <div className="lg:col-span-1">
          <div className="glass-card p-5 flex flex-col h-full justify-between">
            <div>
              <h3 className="text-base font-bold mb-4" style={{ color: "var(--text)" }}>Quick Actions</h3>
              <div className="space-y-2 flex-1">
                {quickActions.map(({ href, icon, label, desc, accent }) => (
                  <Link
                    key={href}
                    href={href}
                    className="block p-3 rounded-xl transition-all group hover:scale-[1.01]"
                    style={{
                      background: `${accent}12`,
                      border: `1px solid ${accent}30`,
                    }}
                    onMouseEnter={e => (e.currentTarget.style.background = `${accent}20`)}
                    onMouseLeave={e => (e.currentTarget.style.background = `${accent}12`)}
                  >
                    <div className="flex justify-between items-center font-semibold text-sm" style={{ color: accent }}>
                      <span>{icon} {label}</span>
                      <span className="group-hover:translate-x-1 transition-transform text-xs">→</span>
                    </div>
                    <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{desc}</div>
                  </Link>
                ))}
              </div>
            </div>
            {/* FL Status snippet */}
            <div className="mt-6 pt-6 border-t border-gray-800">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wide mb-3">Subsystem Status</h3>
              <div className="flex gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  <span className="text-xs text-gray-300">FastAPI Backend</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Live Subsystem Health */}
        <SubsystemHealth />
      </div>

      {/* Recent Scans */}
      <RecentScans limit={5} />
    </div>
  );
}
