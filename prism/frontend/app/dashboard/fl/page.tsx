"use client";

import FederatedDashboard from "@/components/federated/FederatedDashboard";

export default function FederatedLearningPage() {
  return (
    <div className="p-6 md:p-10 space-y-8 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-white mb-2">Federated learning</h1>
        <p className="text-gray-400">Server status, privacy budget, and training rounds.</p>
      </div>
      <FederatedDashboard />
    </div>
  );
}
