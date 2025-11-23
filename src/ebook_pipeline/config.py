"""Configuration loading for ebook pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from . import PROJECT_ROOT
from .paths import SeriesPaths


CONFIG_PATH = PROJECT_ROOT / "config" / "series.json"


def resolve_config_path(path: Optional[str | Path]) -> Path:
    """Normalize a user-supplied config path against the working root."""

    if path is None or path == "":
        return CONFIG_PATH
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = (PROJECT_ROOT / candidate).resolve()
    return candidate


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


def load_config(path: Optional[Path | str] = None) -> Config:
    cfg_path = resolve_config_path(path)
    if not cfg_path.exists():
        raise FileNotFoundError(f"Missing config file: {cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    series_raw = raw.get("series")
    if not isinstance(series_raw, list) or not series_raw:
        raise ValueError("No series defined in config.")
    series = [SeriesConfig.from_dict(item) for item in series_raw]
    return Config(series)


def load_or_create_config(cfg_path: Path) -> Dict[str, Any]:
    """Return config dict, creating a basic structure if missing."""

    if not cfg_path.exists():
        return {"series": []}
    with cfg_path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if not isinstance(raw, dict):
        raise ValueError("Invalid config format: expected a JSON object.")
    if "series" not in raw or not isinstance(raw["series"], list):
        raw["series"] = []
    return raw


def write_config(config: Dict[str, Any], path: Optional[Path | str] = None) -> Path:
    """Persist config JSON with stable formatting."""

    cfg_path = resolve_config_path(path)
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    with cfg_path.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, ensure_ascii=False, indent=2)
    return cfg_path


__all__ = [
    "Config",
    "SeriesConfig",
    "CONFIG_PATH",
    "load_config",
    "load_or_create_config",
    "resolve_config_path",
    "write_config",
]
