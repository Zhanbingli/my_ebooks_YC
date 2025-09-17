"""Centralized helpers for resolving repository paths for a given series."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import PROJECT_ROOT


@dataclass
class SeriesPaths:
    """Resolve filesystem locations for a named content series."""

    slug: str
    metadata_file: Optional[str] = None
    data_root: str = "data"
    content_root: str = "content"
    build_root: str = "build"

    def _resolve_under(self, root: str) -> Path:
        return PROJECT_ROOT / root / self.slug

    @property
    def data_dir(self) -> Path:
        return self._resolve_under(self.data_root)

    @property
    def transcripts_dir(self) -> Path:
        return self.data_dir / "subs"

    @property
    def videos_path(self) -> Path:
        return self.data_dir / "videos.json"

    @property
    def talks_path(self) -> Path:
        return self.data_dir / "talks.json"

    @property
    def content_dir(self) -> Path:
        return self._resolve_under(self.content_root)

    @property
    def build_dir(self) -> Path:
        return self._resolve_under(self.build_root)

    @property
    def book_path(self) -> Path:
        return self.build_dir / "book.md"

    @property
    def metadata_path(self) -> Optional[Path]:
        if not self.metadata_file:
            return None
        return (PROJECT_ROOT / self.metadata_file).resolve()

    def ensure(self) -> None:
        """Create directory tree for the series if missing."""

        for path in [
            self.data_dir,
            self.transcripts_dir,
            self.content_dir,
            self.build_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)


__all__ = ["SeriesPaths"]
