#!/usr/bin/env python3
"""Wrapper for ebook_pipeline.polish.polish_series."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ebook_pipeline.config import load_config
from ebook_pipeline.polish import polish_series


def main() -> None:
    parser = argparse.ArgumentParser(description="Polish chapter Markdown files for readability.")
    parser.add_argument(
        "--series",
        default="yc-ai-startup-school",
        help="Series slug configured in config/series.json.",
    )
    parser.add_argument(
        "--file",
        default="",
        help="Process a single file (relative to the series content dir).",
    )
    args = parser.parse_args()

    series = load_config().get(args.series)
    paths = series.to_paths()

    file_path = Path(args.file) if args.file else None
    polish_series(paths, file=file_path)


if __name__ == "__main__":
    main()
