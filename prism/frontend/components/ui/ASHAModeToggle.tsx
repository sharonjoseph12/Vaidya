"use client";

import { useEffect, useState } from "react";

interface ASHAModeToggleProps {
    className?: string;
}

export default function ASHAModeToggle({ className = "" }: ASHAModeToggleProps) {
    const [enabled, setEnabled] = useState(false);

    useEffect(() => {
        if (typeof window === "undefined") return;
        const stored = localStorage.getItem("prism_asha_mode");
        const isEnabled = stored === "true";
        setEnabled(isEnabled);
        document.body.setAttribute("data-asha", isEnabled ? "true" : "false");
    }, []);

    const toggle = () => {
        const next = !enabled;
        setEnabled(next);
        localStorage.setItem("prism_asha_mode", next ? "true" : "false");
        document.body.setAttribute("data-asha", next ? "true" : "false");
        window.dispatchEvent(new CustomEvent("ashamode", { detail: { enabled: next } }));
    };

    return (
        <button
            onClick={toggle}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all w-full border ${enabled
                ? "bg-green-50 text-green-700 border-green-200"
                : ""
                } ${className}`}
            style={!enabled ? { background: "var(--surface-hover)", color: "var(--text-secondary)", borderColor: "var(--border)" } : undefined}
            title="Toggle ASHA Worker Mode — larger text, simplified navigation"
        >
            <span>{enabled ? "🟢" : "⚪"}</span>
            <span>ASHA Mode {enabled ? "ON" : "OFF"}</span>
        </button>
    );
}
