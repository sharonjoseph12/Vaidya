"use client";

import StatsOverview from "@/components/dashboard/StatsOverview";
import RecentScans from "@/components/dashboard/RecentScans";
import SubsystemHealth from "@/components/dashboard/SubsystemHealth";

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

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Quick Actions */}
        <div className="glass-card p-5 flex flex-col">
          <h3 className="text-base font-bold mb-4" style={{ color: "var(--text)" }}>Quick Actions</h3>
          <div className="space-y-2 flex-1">
            {quickActions.map(({ href, icon, label, desc, accent }) => (
              <a
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
              </a>
            ))}
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
