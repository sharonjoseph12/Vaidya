"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Mock authentication for frontend flow
    setTimeout(() => {
      localStorage.setItem("prism_token", "mock-jwt-token");
      router.push("/dashboard");
    }, 1000);
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6 gradient-bg relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-600/20 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-600/20 rounded-full blur-[100px] pointer-events-none" />

      <div className="w-full max-w-md z-10">
        <div className="text-center mb-10">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-400 flex items-center justify-center text-white font-bold text-4xl shadow-[0_0_30px_rgba(59,130,246,0.5)] mb-6">
            P
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">PRISM Platform</h1>
          <p className="text-blue-400">Passive Readings → Intelligent Scalable Medicine</p>
        </div>

        <div className="glass-card p-8 shadow-2xl border-gray-700/50">
          <form onSubmit={handleLogin} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Health Provider ID</label>
              <input 
                type="text" 
                defaultValue="doctor@prism.app"
                className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-colors"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">Password</label>
              <input 
                type="password" 
                defaultValue="password123"
                className="w-full bg-gray-900 border border-gray-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-colors"
                required
              />
            </div>
            
            <button 
              type="submit" 
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white rounded-xl font-bold transition-all shadow-[0_0_15px_rgba(59,130,246,0.3)] disabled:opacity-50"
            >
              {loading ? "Authenticating..." : "Sign In"}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-gray-800 text-center text-xs text-gray-500">
            Secure connection • ABDM Compliant • DPDP Act 2023 Ready
          </div>
        </div>
      </div>
    </div>
  );
}
