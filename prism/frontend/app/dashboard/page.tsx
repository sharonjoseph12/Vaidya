"use client";

import Link from "next/link";
import StatsOverview from "@/components/dashboard/StatsOverview";
import PatientQueue from "@/components/dashboard/PatientQueue";
import FederatedDashboard from "@/components/federated/FederatedDashboard";

export default function DashboardPage() {
  return (
    <div className="p-6 md:p-10 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white mb-2">Platform Overview</h1>
        <p className="text-gray-400">Welcome back. Here is the current system status.</p>
      </div>

      <StatsOverview />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="lg:col-span-1">
          <PatientQueue />
        </div>
        <div className="lg:col-span-1">
          <div className="glass-card p-5 h-full flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-bold text-white mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <Link href="/scan" className="block p-4 bg-blue-600/10 border border-blue-500/30 rounded-xl hover:bg-blue-600/20 transition group">
                  <div className="font-semibold text-blue-400 flex justify-between items-center">
                    <span>New Passive Scan 📷</span>
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                  <div className="text-sm text-gray-400 mt-1">Start a 30s multimodal assessment</div>
                </Link>
                <Link href="/patient/new" className="block p-4 bg-purple-600/10 border border-purple-500/30 rounded-xl hover:bg-purple-600/20 transition group">
                  <div className="font-semibold text-purple-400 flex justify-between items-center">
                    <span>Register Patient 👥</span>
                    <span className="group-hover:translate-x-1 transition-transform">→</span>
                  </div>
                  <div className="text-sm text-gray-400 mt-1">Verify ABHA ID & fetch history</div>
                </Link>
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
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  <span className="text-xs text-gray-300">Celery Worker</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500"></div>
                  <span className="text-xs text-gray-300">FL Server</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-bold text-white mb-4 border-b border-gray-800 pb-2">Federated Learning Activity</h2>
        <FederatedDashboard />
      </div>
    </div>
  );
}
