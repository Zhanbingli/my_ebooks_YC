"""Convert structured talk JSON into Markdown chapters."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from .paths import SeriesPaths


def slugify(text: str, max_len: int = 80) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    if len(text) > max_len:
        text = text[:max_len].rstrip("-")
    return text


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


def write_chapter(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def ingest_talks(
    paths: SeriesPaths,
    talks: Sequence[Dict[str, Any]],
    *,
    start_index: int = 1,
    overwrite: bool = False,
) -> List[Path]:
    """Write each talk into ``content`` as Markdown chapters."""

    if not talks:
        raise ValueError("Talk list is empty; nothing to ingest.")

    paths.ensure()
    written: List[Path] = []
    idx = start_index
    for entry in talks:
        speaker = (entry.get("speaker") or "Unknown Speaker").strip()
        title = (entry.get("title") or "Untitled Talk").strip()
        slug = slugify(f"{speaker}-{title}") or f"chapter-{idx:02d}"
        chapter_path = paths.content_dir / f"{idx:02d}-{slug}.md"

        if chapter_path.exists() and not overwrite:
            print(f"Skip existing: {chapter_path.relative_to(paths.content_dir.parent)}")
        else:
            md = format_chapter_md(entry)
            write_chapter(chapter_path, md)
            written.append(chapter_path)
            print(f"Wrote: {chapter_path.relative_to(paths.content_dir.parent)}")
        idx += 1
    if not written:
        print("No chapters written (all existed). Use overwrite=True to replace.")
    else:
        print(f"\nChapters written: {len(written)}")
    return written


def ingest_file(
    paths: SeriesPaths,
    input_path: Path,
    *,
    start_index: int = 1,
    overwrite: bool = False,
) -> List[Path]:
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    with input_path.open("r", encoding="utf-8") as fh:
        data: Dict[str, Any] = json.load(fh)
    talks = data.get("talks")
    if not isinstance(talks, list) or not talks:
        raise ValueError("No talks found in input JSON (expected key 'talks').")
    return ingest_talks(paths, talks, start_index=start_index, overwrite=overwrite)


__all__ = ["ingest_file", "ingest_talks", "format_chapter_md", "slugify"]
