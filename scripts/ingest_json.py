#!/usr/bin/env python3
"""CLI wrapper around ebook_pipeline.ingest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ebook_pipeline.config import load_config
from ebook_pipeline.ingest import ingest_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert talks.json into Markdown chapters.")
    parser.add_argument(
        "--series",
        default="yc-ai-startup-school",
        help="Series slug configured in config/series.json.",
    )
    parser.add_argument(
        "--input",
        default="",
        help="Talks JSON path (defaults to the series data directory).",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=1,
        help="Starting chapter number (default: 1).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing chapter files.",
    )
    args = parser.parse_args()

    config = load_config()
    series = config.get(args.series)
    paths = series.to_paths()

    input_path = Path(args.input) if args.input else paths.talks_path
    ingest_file(paths, input_path, start_index=args.start_index, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
