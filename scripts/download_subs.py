#!/usr/bin/env python3
"""Wrapper for ebook_pipeline.subtitles.download_subtitles."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ebook_pipeline.config import load_config
from ebook_pipeline.subtitles import download_subtitles


def main() -> None:
    parser = argparse.ArgumentParser(description="Download subtitles with yt-dlp and update talks.json.")
    parser.add_argument(
        "--series",
        default="yc-ai-startup-school",
        help="Series slug declared in config/series.json.",
    )
    parser.add_argument(
        "--videos-json",
        default="",
        help="Path to videos.json (defaults to the series data directory).",
    )
    parser.add_argument(
        "--browser",
        default="",
        help="Browser to use with yt-dlp --cookies-from-browser (chrome, safari, edge, firefox).",
    )
    parser.add_argument(
        "--cookies",
        default="",
        help="Path to cookies.txt in Netscape format.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of videos processed (0 = all).",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Optional override for talks output path.",
    )
    args = parser.parse_args()

    config = load_config()
    series = config.get(args.series)
    paths = series.to_paths()

    videos_path = Path(args.videos_json) if args.videos_json else None
    cookies_path = Path(args.cookies) if args.cookies else None
    out_path = Path(args.out) if args.out else None

    download_subtitles(
        paths,
        videos_path=videos_path,
        cookies=cookies_path,
        browser=args.browser,
        limit=args.limit,
        export_talks_path=out_path,
    )


if __name__ == "__main__":
    main()
