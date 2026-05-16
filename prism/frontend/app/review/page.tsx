"use client";

import ReviewQueue from "@/components/review/ReviewQueue";

export default function ReviewPage() {
    return (
        <div className="p-6 md:p-10 space-y-6 max-w-4xl mx-auto">
            <div>
                <h1 className="text-2xl font-bold mb-1" style={{ color: "var(--text)" }}>Doctor Review Queue</h1>
                <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                    Scans with ≥70% confidence awaiting clinical review. Approve or override AI diagnoses.
                </p>
            </div>
            <ReviewQueue />
        </div>
    );
}
