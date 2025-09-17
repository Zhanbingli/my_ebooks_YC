#!/usr/bin/env python3
"""Create placeholder talks.json entries from a videos.json file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ebook_pipeline.config import load_config
from ebook_pipeline.youtube import split_title_and_speaker


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate placeholder talks from videos.json.")
    parser.add_argument(
        "--series",
        default="yc-ai-startup-school",
        help="Series slug defined in config/series.json.",
    )
    parser.add_argument(
        "--videos-json",
        default="",
        help="Path to videos.json (defaults to series data dir).",
    )
    parser.add_argument(
        "--out",
        default="",
        help="Output talks path (defaults to series data dir).",
    )
    args = parser.parse_args()

    series = load_config().get(args.series)
    paths = series.to_paths()

    videos_path = Path(args.videos_json) if args.videos_json else paths.videos_path
    if not videos_path.exists():
        raise SystemExit(f"Missing {videos_path}. Run fetch_yc_ai_startup_school.py --export-videos first.")
    out_path = Path(args.out) if args.out else paths.talks_path

    with videos_path.open("r", encoding="utf-8") as fh:
        videos_data = json.load(fh)
    talks = []
    for video in videos_data.get("videos", []):
        title = video.get("title") or "Untitled"
        url = video.get("url") or ""
        talk_title, speaker = split_title_and_speaker(title)
        transcript = (
            "This chapter is a placeholder for the full transcript.\n\n"
            f"Source video: {url}\n\n"
            "Once subtitles are fetched, this will be replaced by the full talk text."
        )
        talks.append(
            {
                "speaker": speaker or "Unknown Speaker",
                "title": talk_title or title,
                "date": "",
                "source_url": url,
                "transcript": transcript,
            }
        )
    data = {"series": series.title, "talks": talks}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    print(f"Wrote placeholders to {out_path} ({len(talks)} talks)")


if __name__ == "__main__":
    main()
