"""
Download Coswara dataset for PRISM respiratory analysis training.
Source: https://github.com/iiscleap/Coswara-Data
"""
import os
import sys
import subprocess

COSWARA_REPO = "https://github.com/iiscleap/Coswara-Data.git"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset", "coswara")


def main():
    if os.path.exists(os.path.join(OUTPUT_DIR, ".git")):
        print(f"Already cloned: {OUTPUT_DIR}")
        print("Pulling latest...")
        subprocess.run(["git", "-C", OUTPUT_DIR, "pull"], check=True)
        return

    os.makedirs(os.path.dirname(OUTPUT_DIR), exist_ok=True)
    print(f"Cloning Coswara dataset to {OUTPUT_DIR} ...")
    print(f"Repo: {COSWARA_REPO}")
    print("NOTE: This repository can be several GB. Use --depth 1 for a shallow clone.")

    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", COSWARA_REPO, OUTPUT_DIR],
            check=True,
        )
        print(f"\nClone complete: {OUTPUT_DIR}")
    except FileNotFoundError:
        print("ERROR: git not found. Install git and retry.", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Clone failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
