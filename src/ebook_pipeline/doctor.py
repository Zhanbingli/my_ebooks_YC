"""Lightweight environment checks to make the CLI easier to use."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

from . import PROJECT_ROOT
from .config import Config, load_config, resolve_config_path
from .paths import SeriesPaths
from .utils import find_yt_dlp

__all__ = ["doctor"]


def _rel(path: Path) -> Path:
    try:
        return path.relative_to(PROJECT_ROOT)
    except ValueError:
        return path


def _series_list(cfg: Config, series_slug: Optional[str]) -> Sequence:
    if series_slug:
        return [cfg.get(series_slug)]
    return cfg.list_series()


def _count_markdown(paths: SeriesPaths) -> int:
    if not paths.content_dir.exists():
        return 0
    return sum(1 for p in paths.content_dir.glob("*.md"))


def doctor(cfg: Optional[Config], *, config_path: Path, series_slug: Optional[str] = None, verbose: bool = False) -> int:
    """Print environment status and return the number of detected issues."""

    issues = 0
    cfg_path = resolve_config_path(config_path)
    print(f"Config: {_rel(cfg_path)}")
    if not cfg_path.exists():
        print("  Missing config. Run `my-ebook init --series <slug> --with-intro` to get started.")
        return 1

    if cfg is None:
        try:
            cfg = load_config(cfg_path)
        except Exception as exc:
            print(f"  Could not parse config: {exc}")
            return 1

    ytdlp = find_yt_dlp()
    if ytdlp:
        print(f"yt-dlp: {_rel(ytdlp)}")
    else:
        issues += 1
        print("yt-dlp: not found. Install with `python3 -m pip install yt-dlp` or set YTDLP=/path/to/yt-dlp")

    try:
        series_list = _series_list(cfg, series_slug)
    except KeyError as exc:
        print(exc)
        return issues + 1
    if not series_list:
        print("No series defined. Add one with `my-ebook init --series <slug>`.")
        return issues or 1

    for series in series_list:
        paths = series.to_paths()
        print(f"\nSeries: {series.slug} — {series.title}")

        if not paths.data_dir.exists():
            issues += 1
            print(f"  data dir: missing ({_rel(paths.data_dir)}) — run `my-ebook init --series {series.slug}`")
        else:
            print(f"  data dir: {_rel(paths.data_dir)}")

        videos_exists = paths.videos_path.exists()
        talks_exists = paths.talks_path.exists()
        if videos_exists:
            print(f"  videos.json: {_rel(paths.videos_path)}")
        else:
            issues += 1
            print(f"  videos.json: missing ({_rel(paths.videos_path)}) — run `my-ebook fetch --series {series.slug}`")

        if talks_exists:
            print(f"  talks.json: {_rel(paths.talks_path)}")
        else:
            issues += 1
            print(f"  talks.json: missing ({_rel(paths.talks_path)}) — run `my-ebook update --series {series.slug}`")

        if paths.content_dir.exists():
            chapters = _count_markdown(paths)
            if chapters:
                print(f"  chapters: {chapters} Markdown file(s) in {_rel(paths.content_dir)}")
            else:
                issues += 1
                print(
                    f"  chapters: none found in {_rel(paths.content_dir)} — ingest talks with "
                    f"`my-ebook ingest --series {series.slug}`"
                )
        else:
            issues += 1
            print(f"  content dir: missing ({_rel(paths.content_dir)}) — run `my-ebook init --series {series.slug}`")

        if paths.metadata_path:
            if paths.metadata_path.exists():
                print(f"  metadata: {_rel(paths.metadata_path)}")
            else:
                issues += 1
                print(f"  metadata: missing ({_rel(paths.metadata_path)}) — edit or recreate your YAML metadata file")
        elif verbose:
            print("  metadata: not configured; defaults will be used")

        if paths.build_dir.exists():
            book = paths.book_path
            if book.exists():
                print(f"  book.md: present at {_rel(book)}")
            else:
                print(f"  book.md: not built yet — run `my-ebook build --series {series.slug}`")
        elif verbose:
            print(f"  build dir: {_rel(paths.build_dir)} (will be created on build)")

    return issues
