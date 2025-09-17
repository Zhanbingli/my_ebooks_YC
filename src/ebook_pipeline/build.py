"""Assemble Markdown chapters into a single book manuscript."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from . import PROJECT_ROOT
from .paths import SeriesPaths


def list_markdown_files(content_dir: Path) -> List[Path]:
    files = [p for p in content_dir.iterdir() if p.suffix.lower() == ".md"]
    files.sort()
    return files


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8").rstrip() + "\n\n"


def load_metadata(metadata_path: Optional[Path]) -> Dict[str, str]:
    data: Dict[str, str] = {}
    if not metadata_path or not metadata_path.exists():
        return data
    for line in metadata_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def build_title_page(metadata: Dict[str, str]) -> str:
    title = metadata.get("title", "YC AI Startup School")
    subtitle = metadata.get("subtitle", "Talks compiled into an eBook")
    author = metadata.get("author", "Y Combinator Speakers")
    date = metadata.get("date") or datetime.now().strftime("%Y-%m-%d")
    parts = [
        f"# {title}",
        f"\n_{subtitle}_\n" if subtitle else "",
        f"\n{author}\n" if author else "",
        f"\n{date}\n" if date else "",
        "\n---\n\n",
    ]
    return "\n".join(part for part in parts if part)


def build_book_md(files: Iterable[Path], metadata: Dict[str, str]) -> str:
    parts = [build_title_page(metadata)]
    for path in files:
        parts.append(read_file(path))
    return "".join(parts)


def write_output(content: str, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")


def build_book(paths: SeriesPaths, metadata_path: Optional[Path] = None) -> Path:
    paths.ensure()
    content_dir = paths.content_dir
    if not content_dir.exists():
        raise FileNotFoundError(f"Missing content directory: {content_dir}")

    files = list_markdown_files(content_dir)
    if not files:
        raise FileNotFoundError(f"No chapter files found in {content_dir}")

    metadata = load_metadata(metadata_path)
    book_md = build_book_md(files, metadata)
    out_path = paths.book_path
    write_output(book_md, out_path)
    try:
        rel = out_path.relative_to(PROJECT_ROOT)
    except ValueError:
        rel = out_path
    print(f"Built: {rel}")
    return out_path


__all__ = ["build_book", "build_book_md", "list_markdown_files", "load_metadata"]
