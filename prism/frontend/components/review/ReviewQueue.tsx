"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getPendingReviews, submitReview } from "@/lib/api";
import type { PendingReview } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export default function ReviewQueue() {
    const router = useRouter();
    const [reviews, setReviews] = useState<PendingReview[]>([]);
    const [loading, setLoading] = useState(true);
    const [overrideModal, setOverrideModal] = useState<string | null>(null);
    const [overrideDiagnosis, setOverrideDiagnosis] = useState("");
    const [submitting, setSubmitting] = useState<string | null>(null);
    const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

    const fetchReviews = useCallback(async () => {
        try {
            const data = await getPendingReviews();
            setReviews(data);
        } catch (err) {
            console.error("Failed to fetch reviews", err);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        setTimeout(() => fetchReviews(), 0);
        const interval = setInterval(fetchReviews, 30000);
        return () => clearInterval(interval);
    }, [fetchReviews]);

    const showToast = (type: "success" | "error", message: string) => {
        setToast({ type, message });
        setTimeout(() => setToast(null), 4000);
    };

    const handleApprove = async (sessionId: string) => {
        setSubmitting(sessionId);
        try {
            await submitReview(sessionId, true);
            setReviews((r) => r.filter((x) => x.session_id !== sessionId));
            showToast("success", "Diagnosis approved");
        } catch (err: unknown) {
            showToast("error", err instanceof Error ? err.message : "Failed to approve");
        } finally {
            setSubmitting(null);
        }
    };

    const handleOverride = async () => {
        if (!overrideModal || !overrideDiagnosis.trim()) return;
        setSubmitting(overrideModal);
        try {
            await submitReview(overrideModal, false, overrideDiagnosis.trim());
            setReviews((r) => r.filter((x) => x.session_id !== overrideModal));
            setOverrideModal(null);
            setOverrideDiagnosis("");
            showToast("success", "Diagnosis overridden");
        } catch (err: unknown) {
            showToast("error", err instanceof Error ? err.message : "Failed to override");
        } finally {
            setSubmitting(null);
        }
    };

    if (loading) {
        return (
            <div className="space-y-3">
                {[...Array(3)].map((_, i) => (
                    <div key={i} className="glass-card p-4 animate-pulse h-20" style={{ background: "var(--surface-hover)" }} />
                ))}
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {/* Toast */}
            {toast && (
                <div className={`px-4 py-3 rounded-xl text-sm font-medium border ${toast.type === "success"
                    ? "bg-green-50 border-green-200 text-green-700"
                    : "bg-red-50 border-red-200 text-red-700"
                    }`}>
                    {toast.type === "success" ? "✓" : "✗"} {toast.message}
                </div>
            )}

            {reviews.length === 0 ? (
                <div className="glass-card p-12 text-center">
                    <div className="text-4xl mb-3">✅</div>
                    <h3 className="text-lg font-semibold" style={{ color: "var(--text)" }}>All caught up</h3>
                    <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>No scans pending review</p>
                </div>
            ) : (
                reviews.map((review) => (
                    <div key={review.session_id} className="glass-card p-5">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                            <div className="flex-1">
                                <div className="flex items-center gap-3 mb-1">
                                    <span className="font-semibold" style={{ color: "var(--text)" }}>
                                        {review.patient_name || `Patient ${review.patient_id.split("-")[0]}`}
                                    </span>
                                    <span className="text-xs bg-red-100 text-red-700 border border-red-200 px-2 py-0.5 rounded-full font-medium">
                                        {(review.confidence_score * 100).toFixed(0)}% confidence
                                    </span>
                                </div>
                                <div className="text-sm" style={{ color: "var(--text-secondary)" }}>
                                    Diagnosis: <span className="font-medium text-blue-600">{review.primary_diagnosis?.replace(/_/g, " ")}</span>
                                </div>
                                <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{formatDate(review.created_at)}</div>
                            </div>

                            <div className="flex gap-2 flex-shrink-0">
                                <button
                                    onClick={() => router.push(`/patient/${review.session_id}`)}
                                    className="px-3 py-2 text-xs rounded-lg transition border"
                                    style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                                    onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                                    onMouseLeave={e => (e.currentTarget.style.background = "")}
                                >
                                    View Report
                                </button>
                                <button
                                    onClick={() => { setOverrideModal(review.session_id); setOverrideDiagnosis(""); }}
                                    className="px-3 py-2 text-xs border border-amber-200 bg-amber-50 text-amber-700 rounded-lg hover:bg-amber-100 transition"
                                >
                                    Override
                                </button>
                                <button
                                    onClick={() => handleApprove(review.session_id)}
                                    disabled={submitting === review.session_id}
                                    className="px-4 py-2 text-xs bg-green-600 hover:bg-green-700 text-white rounded-lg transition disabled:opacity-50 font-medium"
                                >
                                    {submitting === review.session_id ? "..." : "Approve ✓"}
                                </button>
                            </div>
                        </div>
                    </div>
                ))
            )}

            {/* Override Modal */}
            {overrideModal && (
                <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50 p-4">
                    <div className="glass-card p-6 w-full max-w-md shadow-xl">
                        <h3 className="text-lg font-bold mb-4" style={{ color: "var(--text)" }}>Override Diagnosis</h3>
                        <input
                            type="text"
                            placeholder="Enter correct diagnosis..."
                            value={overrideDiagnosis}
                            onChange={(e) => setOverrideDiagnosis(e.target.value)}
                            className="w-full rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500 mb-4 border"
                            style={{ background: "var(--surface)", color: "var(--text)", borderColor: "var(--border)" }}
                            autoFocus
                        />
                        <div className="flex gap-3">
                            <button
                                onClick={handleOverride}
                                disabled={!overrideDiagnosis.trim() || submitting !== null}
                                className="flex-1 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-sm font-medium transition disabled:opacity-50"
                            >
                                Confirm Override
                            </button>
                            <button
                                onClick={() => setOverrideModal(null)}
                                className="px-4 py-2 rounded-lg text-sm transition border"
                                style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                                onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                                onMouseLeave={e => (e.currentTarget.style.background = "")}
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
