"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import ASHAModeToggle from "@/components/ui/ASHAModeToggle";
import ThemeToggle from "@/components/ui/ThemeToggle";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const navItems = [
    { name: "Dashboard", path: "/dashboard", icon: "📊" },
    { name: "New Scan", path: "/scan", icon: "📷", ashaVisible: true },
    { name: "Patients", path: "/patients", icon: "👥", ashaVisible: true },
    { name: "Federated Learning", path: "/federated", icon: "🌐", ashaVisible: false },
    { name: "Review Queue", path: "/review", icon: "🩺", ashaVisible: false },
    { name: "Audit Log", path: "/audit", icon: "📋", ashaVisible: false },
  ];

  return (
    <div className="min-h-screen flex flex-col md:flex-row" style={{ background: "var(--bg)", color: "var(--text)" }}>

      {/* Sidebar */}
      <aside
        className="w-full md:w-64 flex flex-col border-b md:border-b-0 md:border-r"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        {/* Logo */}
        <div className="p-6 border-b" style={{ borderColor: "var(--border)" }}>
          <Link href="/dashboard" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center text-white font-bold shadow-md group-hover:shadow-lg transition-all">
              P
            </div>
            <div>
              <h1 className="font-bold text-xl tracking-tight text-blue-600 dark:text-blue-400">PRISM</h1>
              <p className="text-[10px] uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
                Diagnostic Platform
              </p>
            </div>
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => {
            const isActive =
              pathname === item.path ||
              (item.path !== "/dashboard" && pathname.startsWith(item.path));
            return (
              <Link
                key={item.path}
                href={item.path}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all text-sm font-medium ${item.ashaVisible === false ? "asha-hidden" : ""
                  }`}
                style={
                  isActive
                    ? {
                      background: "var(--blue-light)",
                      color: "var(--blue)",
                      border: "1px solid var(--blue)",
                      opacity: 1,
                    }
                    : {
                      color: "var(--text-secondary)",
                      border: "1px solid transparent",
                    }
                }
              >
                <span>{item.icon}</span>
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t space-y-2" style={{ borderColor: "var(--border)" }}>
          <ThemeToggle />
          <ASHAModeToggle />
          <div className="flex items-center gap-3 px-2 py-1 mt-1">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold"
              style={{ background: "var(--blue-light)", color: "var(--blue)" }}
            >
              Dr
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-medium" style={{ color: "var(--text)" }}>Dr. User</span>
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>Cardiology</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto" style={{ background: "var(--bg)" }}>
        {children}
      </main>
    </div>
  );
}
