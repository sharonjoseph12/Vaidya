"use client";

import { useState } from "react";

export interface SymptomAnswer {
    cough_duration: "none" | "<1week" | "1-4weeks" | ">4weeks";
    fever: boolean | null;
    night_sweats: boolean | null;
    weight_loss: boolean | null;
    shortness_of_breath: boolean | null;
}

interface SymptomQuestionnaireProps {
    onComplete: (answers: SymptomAnswer) => void;
    onSkip?: () => void;
}

const COUGH_OPTIONS = [
    { value: "none", label: "No cough" },
    { value: "<1week", label: "Less than 1 week" },
    { value: "1-4weeks", label: "1–4 weeks" },
    { value: ">4weeks", label: "More than 4 weeks" },
] as const;

function YesNoToggle({
    label,
    value,
    onChange,
}: {
    label: string;
    value: boolean | null;
    onChange: (v: boolean) => void;
}) {
    return (
        <div className="flex items-center justify-between py-3 border-b last:border-0" style={{ borderColor: "var(--border)" }}>
            <span className="text-sm font-medium" style={{ color: "var(--text)" }}>{label}</span>
            <div className="flex gap-2">
                <button
                    onClick={() => onChange(true)}
                    className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all border ${value === true
                        ? "bg-red-100 text-red-700 border-red-300"
                        : "border hover:opacity-80"
                        }`}
                    style={value !== true ? { background: "var(--surface-hover)", color: "var(--text-secondary)", borderColor: "var(--border)" } : undefined}
                >
                    Yes
                </button>
                <button
                    onClick={() => onChange(false)}
                    className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all border ${value === false
                        ? "bg-green-100 text-green-700 border-green-300"
                        : "border hover:opacity-80"
                        }`}
                    style={value !== false ? { background: "var(--surface-hover)", color: "var(--text-secondary)", borderColor: "var(--border)" } : undefined}
                >
                    No
                </button>
            </div>
        </div>
    );
}

export default function SymptomQuestionnaire({ onComplete, onSkip }: SymptomQuestionnaireProps) {
    const [answers, setAnswers] = useState<SymptomAnswer>({
        cough_duration: "none",
        fever: null,
        night_sweats: null,
        weight_loss: null,
        shortness_of_breath: null,
    });

    const isComplete =
        answers.cough_duration !== undefined &&
        answers.fever !== null &&
        answers.night_sweats !== null &&
        answers.weight_loss !== null &&
        answers.shortness_of_breath !== null;

    return (
        <div className="w-full max-w-lg">
            <div className="glass-card p-6 space-y-5">
                {/* Header */}
                <div>
                    <h2 className="text-xl font-bold" style={{ color: "var(--text)" }}>Pre-Scan Symptom Check</h2>
                    <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>
                        Answer 5 quick questions to improve diagnostic accuracy
                    </p>
                </div>

                {/* Q1: Cough duration */}
                <div>
                    <label className="block text-sm font-semibold mb-2" style={{ color: "var(--text)" }}>
                        1. How long have you had a cough?
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                        {COUGH_OPTIONS.map((opt) => (
                            <button
                                key={opt.value}
                                onClick={() => setAnswers((a) => ({ ...a, cough_duration: opt.value }))}
                                className={`px-3 py-2 rounded-lg text-sm font-medium text-left transition-all border ${answers.cough_duration === opt.value
                                    ? "bg-blue-50 text-blue-700 border-blue-300"
                                    : ""
                                    }`}
                                style={answers.cough_duration !== opt.value ? { background: "var(--surface-hover)", color: "var(--text-secondary)", borderColor: "var(--border)" } : undefined}
                            >
                                {opt.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Q2–Q5: Yes/No */}
                <div
                    className="glass-card p-4"
                    style={{ background: "var(--surface-hover)" }}
                >
                    <YesNoToggle
                        label="2. Do you have a fever?"
                        value={answers.fever}
                        onChange={(v) => setAnswers((a) => ({ ...a, fever: v }))}
                    />
                    <YesNoToggle
                        label="3. Night sweats?"
                        value={answers.night_sweats}
                        onChange={(v) => setAnswers((a) => ({ ...a, night_sweats: v }))}
                    />
                    <YesNoToggle
                        label="4. Unexplained weight loss?"
                        value={answers.weight_loss}
                        onChange={(v) => setAnswers((a) => ({ ...a, weight_loss: v }))}
                    />
                    <YesNoToggle
                        label="5. Shortness of breath?"
                        value={answers.shortness_of_breath}
                        onChange={(v) => setAnswers((a) => ({ ...a, shortness_of_breath: v }))}
                    />
                </div>

                {/* Actions */}
                <div className="flex gap-3">
                    <button
                        onClick={() => onComplete(answers)}
                        disabled={!isComplete}
                        className={`flex-1 py-3 rounded-xl font-semibold text-sm transition-all ${isComplete
                            ? "bg-blue-600 hover:bg-blue-700 text-white shadow-md hover:shadow-lg"
                            : "cursor-not-allowed"
                            }`}
                        style={!isComplete ? { background: "var(--surface-hover)", color: "var(--text-muted)" } : undefined}
                    >
                        Continue to Scan →
                    </button>
                    {onSkip && (
                        <button
                            onClick={onSkip}
                            className="px-4 py-3 rounded-xl text-sm transition-all border"
                            style={{ color: "var(--text-secondary)", borderColor: "var(--border)" }}
                            onMouseEnter={e => (e.currentTarget.style.background = "var(--surface-hover)")}
                            onMouseLeave={e => (e.currentTarget.style.background = "")}
                        >
                            Skip
                        </button>
                    )}
                </div>

                {!isComplete && (
                    <p className="text-xs text-center" style={{ color: "var(--text-muted)" }}>
                        Please answer all questions to continue
                    </p>
                )}
            </div>
        </div>
    );
}
