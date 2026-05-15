#!/usr/bin/env python3
"""
Evaluate Layer 1 audio (cough path) on real WAV files — no synthetic X/y.

Examples:
  python scripts/evaluate_model.py --audio-dir ./data/cough_samples
  python scripts/evaluate_model.py --audio-glob "samples/**/*.wav" --labels-csv ./data/labels.csv

labels.csv format: filename (or stem),label  e.g. cough_01.wav,1
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _collect_wavs(audio_dir: Optional[str], audio_glob: Optional[str]) -> List[Path]:
    root = _repo_root()
    paths: List[Path] = []
    if audio_dir:
        d = Path(audio_dir).expanduser()
        if not d.is_dir():
            raise SystemExit(f"Not a directory: {d}")
        paths.extend(sorted(d.rglob("*.wav")) + sorted(d.rglob("*.flac")))
    if audio_glob:
        paths.extend(sorted(root.glob(audio_glob)))
    # de-dupe
    seen = set()
    out: List[Path] = []
    for p in paths:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            out.append(rp)
    return out


def _load_labels(path: str) -> Dict[str, str]:
    labels: Dict[str, str] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return labels
        lower = {h.lower(): h for h in reader.fieldnames}
        file_key = lower.get("filename") or lower.get("file") or lower.get("path")
        label_key = lower.get("label") or lower.get("class") or lower.get("y")
        if not file_key or not label_key:
            raise SystemExit("labels CSV needs columns: filename, label (or file, class)")
        for row in reader:
            fn = (row.get(file_key) or "").strip()
            lab = (row.get(label_key) or "").strip()
            if fn:
                labels[fn] = lab
                labels[Path(fn).name] = lab
                labels[Path(fn).stem] = lab
    return labels


def main() -> None:
    parser = argparse.ArgumentParser(description="Run real PRISM audio pipeline on WAV/FLAC files.")
    parser.add_argument("--audio-dir", help="Directory tree to scan for .wav/.flac")
    parser.add_argument("--audio-glob", help="Glob relative to repo root (e.g. data/**/*.wav)")
    parser.add_argument(
        "--labels-csv",
        help="Optional CSV with filename,label for accuracy / report",
    )
    args = parser.parse_args()

    if not args.audio_dir and not args.audio_glob:
        parser.error("Provide --audio-dir and/or --audio-glob")

    root = _repo_root()
    sys.path.insert(0, str(root))

    wavs = _collect_wavs(args.audio_dir, args.audio_glob)
    if not wavs:
        raise SystemExit("No audio files found.")

    labels: Dict[str, str] = {}
    if args.labels_csv:
        labels = _load_labels(args.labels_csv)

    from layer1_sense.audio.audio_pipeline import PRISMAudioPipeline

    pipeline = PRISMAudioPipeline(sample_rate=16000)

    rows: List[Tuple[str, Dict[str, float], bool, float]] = []
    for wav in wavs:
        try:
            result = pipeline.full_analysis(str(wav))
            probs = result.disease_probs or {}
            rows.append(
                (
                    wav.name,
                    probs,
                    result.cough_detected,
                    float(result.breathing_rate or 0.0),
                )
            )
        except Exception as e:
            print(f"{wav.name}\tERROR\t{e}", file=sys.stderr)

    if not rows:
        raise SystemExit("All files failed analysis.")

    print(f"Processed {len(rows)} file(s).\n")
    print("file\tcough_detected\tbreathing_rate\tdisease_probs (top)")
    for name, probs, cough, br in rows:
        ranked = sorted(probs.items(), key=lambda kv: kv[1], reverse=True)[:6]
        prob_str = ", ".join(f"{k}={v:.3f}" for k, v in ranked)
        print(f"{name}\t{cough}\t{br:.1f}\t{prob_str}")

    if labels:
        correct = 0
        total = 0
        for name, probs, _, _ in rows:
            lab = labels.get(name) or labels.get(Path(name).stem)
            if lab is None:
                continue
            # Predict sick if Uncertain mass dominates or explicit sick_prob
            uncertain = float(probs.get("Uncertain", probs.get("sick_prob", 0.0)))
            healthy = float(probs.get("Healthy", probs.get("healthy_prob", 0.0)))
            pred = "1" if uncertain >= healthy else "0"
            if pred == str(lab).strip():
                correct += 1
            total += 1
        if total:
            print(f"\nAccuracy vs labels.csv (binary: 1=sick, 0=healthy): {correct}/{total} = {correct/total:.3f}")


if __name__ == "__main__":
    main()
