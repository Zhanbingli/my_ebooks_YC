#!/usr/bin/env python3
"""Remove generated chapter Markdown files for a series."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ebook_pipeline.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete generated chapter Markdown files (keeps introduction).")
    parser.add_argument(
        "--series",
        default="yc-ai-startup-school",
        help="Series slug declared in config/series.json.",
    )
    args = parser.parse_args()

    series = load_config().get(args.series)
    content_dir = series.to_paths().content_dir
    if not content_dir.exists():
        print(f"No content directory found for {args.series}.")
        return
    removed = 0
    for path in content_dir.glob("*.md"):
        if path.name.startswith("000-introduction"):
            continue
        path.unlink()
        removed += 1
    print(f"Removed {removed} chapter files (kept introduction if present).")


if __name__ == "__main__":
    main()
