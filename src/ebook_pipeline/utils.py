"""Shared utilities used across the ebook pipeline."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Optional

__all__ = ["find_yt_dlp"]


def find_yt_dlp() -> Optional[Path]:
    """Locate a yt-dlp binary via env vars, PATH, or common install locations."""

    for env_var in ("YTDLP", "YT_DLP"):
        val = os.environ.get(env_var)
        if val:
            env_path = Path(val).expanduser()
            if env_path.exists():
                return env_path

    which = shutil.which("yt-dlp") or shutil.which("yt_dlp")
    candidates = [Path(which)] if which else []
    candidates.extend(
        [
            Path(".venv/bin/yt-dlp"),
            Path("~/Library/Python/3.9/bin/yt-dlp").expanduser(),
            Path("/opt/homebrew/bin/yt-dlp"),
        ]
    )
    for cand in candidates:
        if cand.exists():
            return cand
    return None
