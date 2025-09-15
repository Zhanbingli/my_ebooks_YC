#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from typing import Dict, Any, List


def slugify(text: str, max_len: int = 80) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    if len(text) > max_len:
        text = text[:max_len].rstrip("-")
    return text


def ensure_dirs():
    os.makedirs("content", exist_ok=True)
    os.makedirs("build", exist_ok=True)


def format_chapter_md(entry: Dict[str, Any]) -> str:
    speaker = entry.get("speaker", "Unknown Speaker").strip()
    title = entry.get("title", "Untitled Talk").strip()
    date = (entry.get("date") or "").strip()
    source_url = (entry.get("source_url") or "").strip()
    transcript = (entry.get("transcript") or "").rstrip() + "\n"

    header = f"# {speaker}: {title}\n\n"
    meta_lines: List[str] = []
    if date:
        meta_lines.append(f"- Date: {date}")
    if source_url:
        meta_lines.append(f"- Source: {source_url}")
    meta = ("\n".join(meta_lines) + "\n\n") if meta_lines else ""

    return header + meta + transcript + "\n"


def main():
    parser = argparse.ArgumentParser(description="Ingest talks from JSON and write chapter Markdown files.")
    parser.add_argument("--input", default="talks.json", help="Path to JSON with talks.")
    parser.add_argument("--start-index", type=int, default=1, help="Starting chapter number (default: 1).")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing chapter files.")
    args = parser.parse_args()

    ensure_dirs()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
    except FileNotFoundError:
        print(f"Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    talks = data.get("talks") or []
    if not isinstance(talks, list) or not talks:
        print("No talks found in input JSON (expected key 'talks').", file=sys.stderr)
        sys.exit(1)

    idx = args.start_index
    written: List[str] = []

    for entry in talks:
        speaker = (entry.get("speaker") or "Unknown Speaker").strip()
        title = (entry.get("title") or "Untitled Talk").strip()
        slug = slugify(f"{speaker}-{title}")
        filename = os.path.join("content", f"{idx:02d}-{slug}.md")

        if os.path.exists(filename) and not args.overwrite:
            print(f"Skip existing: {filename}")
        else:
            md = format_chapter_md(entry)
            with open(filename, "w", encoding="utf-8") as out:
                out.write(md)
            print(f"Wrote: {filename}")
            written.append(filename)

        idx += 1

    if written:
        print(f"\nChapters written: {len(written)}")
    else:
        print("No chapters written (all existed). Use --overwrite to replace.")


if __name__ == "__main__":
    main()

