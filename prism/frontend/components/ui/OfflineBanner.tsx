"use client";

import { useEffect, useState } from "react";
import { offlineStore } from "@/lib/offline-store";

export default function OfflineBanner() {
  const [isOffline, setIsOffline] = useState(offlineStore.isOffline);

  useEffect(() => {
    const unsubscribe = offlineStore.subscribe(setIsOffline);
    return () => { unsubscribe(); };
  }, []);

  if (!isOffline) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-amber-500/20 border-b border-amber-500/40 backdrop-blur-sm py-2 px-4 flex items-center justify-between">
      <div className="flex items-center gap-2 text-sm font-medium text-amber-300">
        <span className="inline-block w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
        Offline Mode — Backend unreachable. Running on local cached models.
      </div>
      <button
        onClick={() => window.location.reload()}
        className="text-xs px-3 py-1 rounded-md bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 transition border border-amber-500/30"
      >
        Retry Connection
      </button>
    </div>
  );
}
