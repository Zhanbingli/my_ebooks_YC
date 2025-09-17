"""Configuration loading for ebook pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from . import PROJECT_ROOT
from .paths import SeriesPaths


CONFIG_PATH = PROJECT_ROOT / "config" / "series.json"


@dataclass
class SeriesConfig:
    slug: str
    title: str
    description: str = ""
    youtube: Dict[str, Any] | None = None
    metadata_file: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SeriesConfig":
        return cls(
            slug=data["slug"],
            title=data.get("title", data["slug"].replace("-", " ").title()),
            description=data.get("description", ""),
            youtube=data.get("youtube"),
            metadata_file=data.get("metadata_file"),
        )

    def to_paths(self) -> SeriesPaths:
        return SeriesPaths(slug=self.slug, metadata_file=self.metadata_file or None)


class Config:
    def __init__(self, series: Iterable[SeriesConfig]):
        self._series: Dict[str, SeriesConfig] = {s.slug: s for s in series}

    def list_series(self) -> List[SeriesConfig]:
        return sorted(self._series.values(), key=lambda s: s.slug)

    def get(self, slug: str) -> SeriesConfig:
        try:
            return self._series[slug]
        except KeyError as exc:
            raise KeyError(f"Unknown series slug '{slug}'.") from exc


def load_config(path: Optional[Path] = None) -> Config:
    cfg_path = path or CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"Missing config file: {cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    series_raw = raw.get("series")
    if not isinstance(series_raw, list) or not series_raw:
        raise ValueError("No series defined in config.")
    series = [SeriesConfig.from_dict(item) for item in series_raw]
    return Config(series)


__all__ = ["Config", "SeriesConfig", "load_config", "CONFIG_PATH"]
