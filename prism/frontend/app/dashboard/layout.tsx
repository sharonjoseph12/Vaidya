"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const navItems = [
    { name: "Overview", path: "/dashboard", icon: "📊" },
    { name: "New Scan", path: "/scan", icon: "📷" },
    { name: "Patients", path: "/patients", icon: "👥" },
    { name: "Federated Learning", path: "/dashboard/fl", icon: "🌐" },
  ];

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-[#0a0f1e] text-gray-100">
      
      {/* Sidebar */}
      <aside className="w-full md:w-64 border-b md:border-b-0 md:border-r border-gray-800 bg-[#0a0f1e]/80 backdrop-blur-xl flex flex-col">
        <div className="p-6">
          <Link href="/dashboard" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-400 flex items-center justify-center text-white font-bold shadow-[0_0_15px_rgba(59,130,246,0.5)] group-hover:shadow-[0_0_25px_rgba(59,130,246,0.6)] transition-all">
              P
            </div>
            <div>
              <h1 className="font-bold text-xl tracking-tight bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">PRISM</h1>
              <p className="text-[10px] text-gray-500 uppercase tracking-widest">Diagnostic Platform</p>
            </div>
          </Link>
        </div>

        <nav className="flex-1 px-4 py-2 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.path || (item.path !== "/dashboard" && pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                href={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                  isActive 
                    ? "bg-blue-600/10 text-blue-400 border border-blue-500/20 shadow-[inset_0_0_10px_rgba(59,130,246,0.1)]" 
                    : "text-gray-400 hover:bg-gray-800/50 hover:text-white"
                }`}
              >
                <span>{item.icon}</span>
                <span className="font-medium text-sm">{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center gap-3 px-4 py-2">
            <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center text-xs">
              Dr
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-medium">Dr. User</span>
              <span className="text-xs text-gray-500">Cardiology</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
