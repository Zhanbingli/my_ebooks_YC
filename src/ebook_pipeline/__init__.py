"""Shared tooling for building eBooks from YouTube transcripts."""

from __future__ import annotations

import os
from pathlib import Path

__all__ = ["__version__", "PROJECT_ROOT"]

__version__ = "0.1.0"


def _discover_project_root() -> Path:
    """Resolve the working root so the CLI works both in-repo and when installed.

    Order of precedence:
    1) ``EBOOK_PIPELINE_HOME`` env var.
    2) The first parent of CWD containing ``config/series.json``.
    3) The repository root (two parents up from this file).
    """

    env_home = os.environ.get("EBOOK_PIPELINE_HOME")
    if env_home:
        env_path = Path(env_home).expanduser().resolve()
        if env_path.exists():
            return env_path

    cwd = Path.cwd().resolve()
    for base in [cwd, *cwd.parents]:
        if (base / "config" / "series.json").exists():
            return base

    return Path(__file__).resolve().parents[2]


PROJECT_ROOT = _discover_project_root()
