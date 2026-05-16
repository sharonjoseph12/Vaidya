"use client";

import AuditLog from "@/components/audit/AuditLog";

export default function AuditPage() {
    return (
        <div className="p-6 md:p-10 space-y-6 max-w-6xl mx-auto">
            <div>
                <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text)" }}>Audit Log</h1>
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                    Complete PHI access log — every diagnosis, read, and export recorded for DPDP Act 2023 compliance.
                </p>
            </div>
            <AuditLog pageSize={20} />
        </div>
    );
}
