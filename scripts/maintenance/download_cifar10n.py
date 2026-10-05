#!/usr/bin/env python3
"""
Download CIFAR-10N noisy labels file.

This is a one-time setup step to get the noisy labels for CIFAR-10N experiments.
"""
import urllib.request
from pathlib import Path

# URL for CIFAR-10N noisy labels
CIFAR10N_URL = "https://github.com/UCSC-REAL/cifar-10-100n/raw/main/data/CIFAR-10_human.pt"

# Target directory
DATA_DIR = Path(__file__).parent.parent / "data" / "cifar10n" / "cifar-10-batches-py"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TARGET_FILE = DATA_DIR / "CIFAR-10_human.pt"

def download_with_progress(url: str, target: Path):
    """Download file with progress bar."""
    print(f"Downloading CIFAR-10N noisy labels...")
    print(f"From: {url}")
    print(f"To: {target}")
    
    def report_progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(100, (downloaded / total_size) * 100)
        print(f"\rProgress: {percent:.1f}% ({downloaded / 1024 / 1024:.1f} MB / {total_size / 1024 / 1024:.1f} MB)", end="")
    
    urllib.request.urlretrieve(url, target, reporthook=report_progress)
    print("\n✅ Download complete!")

if __name__ == "__main__":
    if TARGET_FILE.exists():
        print(f"✅ CIFAR-10N noisy labels already exist at: {TARGET_FILE}")
    else:
        download_with_progress(CIFAR10N_URL, TARGET_FILE)
        print(f"✅ CIFAR-10N noisy labels saved to: {TARGET_FILE}")

# Made with Bob
