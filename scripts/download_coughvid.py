"""
Download CoughVid dataset for PRISM cough classifier training.
Source: https://zenodo.org/records/4048312
"""
import os
import sys
import requests
from tqdm import tqdm

COUGHVID_URL = "https://zenodo.org/records/4048312/files/public_dataset_v3.zip"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset", "coughvid")


def download_file(url: str, dest: str, chunk_size: int = 8192):
    """Stream-download a large file with progress bar."""
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    total = int(resp.headers.get("content-length", 0))

    with open(dest, "wb") as f, tqdm(total=total, unit="B", unit_scale=True, desc=os.path.basename(dest)) as bar:
        for chunk in resp.iter_content(chunk_size=chunk_size):
            f.write(chunk)
            bar.update(len(chunk))


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dest = os.path.join(OUTPUT_DIR, "public_dataset_v3.zip")

    if os.path.exists(dest):
        print(f"Already downloaded: {dest}")
        return

    print(f"Downloading CoughVid dataset to {dest} ...")
    print(f"URL: {COUGHVID_URL}")
    print("NOTE: This is a ~1.2 GB download. Ensure sufficient disk space.")

    try:
        download_file(COUGHVID_URL, dest)
        print(f"\nDownload complete: {dest}")
        print("Extract with: python -m zipfile -e public_dataset_v3.zip .")
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
