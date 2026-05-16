"use client";

import { useTheme } from "@/lib/theme";

interface ThemeToggleProps {
    className?: string;
}

export default function ThemeToggle({ className = "" }: ThemeToggleProps) {
    const { theme, toggleTheme } = useTheme();
    const isDark = theme === "dark";

    return (
        <button
            onClick={toggleTheme}
            aria-label={`Switch to ${isDark ? "light" : "dark"} mode`}
            title={`Switch to ${isDark ? "light" : "dark"} mode`}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 border w-full ${className}`}
            style={{
                background: "var(--surface-hover)",
                borderColor: "var(--border)",
                color: "var(--text-secondary)",
            }}
        >
            {/* Toggle track */}
            <div
                className="relative w-9 h-5 rounded-full transition-colors duration-300 flex-shrink-0"
                style={{ background: isDark ? "var(--blue)" : "var(--text-muted)" }}
            >
                <div
                    className="absolute top-0.5 w-4 h-4 rounded-full bg-white shadow-sm transition-all duration-300"
                    style={{ left: isDark ? "1.1rem" : "0.125rem" }}
                />
            </div>
            <span>{isDark ? "🌙 Dark mode" : "☀️ Light mode"}</span>
        </button>
    );
}
