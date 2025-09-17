#!/usr/bin/env python3
"""Wrapper for ebook_pipeline.enrich.enrich_talks."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ebook_pipeline.config import load_config
from ebook_pipeline.enrich import enrich_talks


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean transcripts and optionally enrich metadata via yt-dlp.")
    parser.add_argument(
        "--series",
        default="yc-ai-startup-school",
        help="Series slug configured in config/series.json.",
    )
    parser.add_argument(
        "--in",
        dest="input_path",
        default="",
        help="Input talks.json path (defaults to series data dir).",
    )
    parser.add_argument(
        "--out",
        dest="output_path",
        default="",
        help="Output talks.json path (defaults to same as input).",
    )
    parser.add_argument(
        "--videos-json",
        default="",
        help="Unused placeholder for backwards compatibility.",
    )
    parser.add_argument(
        "--use-yt-dlp",
        action="store_true",
        help="Use yt-dlp to fetch missing metadata (upload date).",
    )
    parser.add_argument("--cookies", default="", help="Path to cookies.txt for yt-dlp.")
    parser.add_argument(
        "--browser",
        default="",
        help="Browser name for yt-dlp --cookies-from-browser.",
    )
    args = parser.parse_args()

    series = load_config().get(args.series)
    paths = series.to_paths()

    input_path = Path(args.input_path) if args.input_path else paths.talks_path
    output_path = Path(args.output_path) if args.output_path else None
    cookies_path = Path(args.cookies) if args.cookies else None

    changed = enrich_talks(
        paths,
        input_path=input_path,
        output_path=output_path,
        use_yt_dlp=args.use_yt_dlp,
        cookies=cookies_path,
        browser=args.browser,
    )
    if changed:
        print(f"Updated talks: {changed} changes written to {(output_path or input_path)}")
    else:
        print("No changes required (transcripts clean and metadata present).")


if __name__ == "__main__":
    main()
