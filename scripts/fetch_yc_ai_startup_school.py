#!/usr/bin/env python3
"""CLI wrapper kept for backwards-compatibility with the original script."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ebook_pipeline.config import load_config
from ebook_pipeline.youtube import PlaylistDiscoveryError, fetch_and_store


def parse_languages(value: str) -> List[str]:
    langs = [item.strip() for item in value.split(",") if item.strip()]
    return langs or ["en"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch YC AI Startup School videos and transcripts into talks.json."
    )
    parser.add_argument(
        "--series",
        default="yc-ai-startup-school",
        help="Series slug defined in config/series.json (default: yc-ai-startup-school).",
    )
    parser.add_argument("--playlist-id", default="", help="Override playlist id.")
    parser.add_argument(
        "--query",
        default="",
        help="Search query to find the playlist (fallbacks to config value).",
    )
    parser.add_argument(
        "--langs",
        default="en,en-US,en-GB",
        help="Comma-separated language codes to try when fetching transcripts.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Maximum number of videos to process (0 = all).",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Optional override for the talks output path (default: series data dir).",
    )
    parser.add_argument(
        "--videos-out",
        default="",
        help="Optional override for the exported videos path (default: series data dir).",
    )
    parser.add_argument(
        "--export-videos",
        action="store_true",
        help="Write the video list to videos.json alongside talks.json.",
    )
    args = parser.parse_args()

    config = load_config()
    series = config.get(args.series)
    paths = series.to_paths()

    langs = parse_languages(args.langs)
    yt_cfg = series.youtube or {}
    playlist_id = args.playlist_id or yt_cfg.get("playlist_id")
    query = args.query or yt_cfg.get("playlist_query") or series.title

    talks_path = Path(args.out) if args.out else None
    videos_path = Path(args.videos_out) if args.videos_out else None

    try:
        fetch_and_store(
            paths,
            languages=langs,
            playlist_id=playlist_id,
            query=query,
            limit=args.limit,
            export_videos=args.export_videos,
            series_title=series.title,
            talks_path=talks_path,
            videos_path=videos_path,
        )
    except PlaylistDiscoveryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
