#!/usr/bin/env python3
"""CLI wrapper to assemble the Markdown book."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ebook_pipeline import PROJECT_ROOT
from ebook_pipeline.config import load_config
from ebook_pipeline.build import build_book


def main() -> None:
    parser = argparse.ArgumentParser(description="Concatenate Markdown chapters into build/book.md.")
    parser.add_argument(
        "--series",
        default="yc-ai-startup-school",
        help="Series slug declared in config/series.json.",
    )
    parser.add_argument(
        "--metadata",
        default="",
        help="Optional override for metadata file (YAML key:value pairs).",
    )
    args = parser.parse_args()

    config = load_config()
    series = config.get(args.series)
    paths = series.to_paths()
    if args.metadata:
        md_path = Path(args.metadata)
        if not md_path.is_absolute():
            md_path = (PROJECT_ROOT / args.metadata).resolve()
        metadata_path = md_path
    else:
        metadata_path = paths.metadata_path

    build_book(paths, metadata_path=metadata_path)


if __name__ == "__main__":
    main()
