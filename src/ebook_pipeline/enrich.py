"""Transcript cleaning and metadata enrichment helpers."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .paths import SeriesPaths


def run_json(cmd: List[str]) -> Optional[Dict[str, Any]]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        txt = out.decode("utf-8", errors="replace")
        match = re.search(r"\{.*\}\s*$", txt, flags=re.S)
        data = txt if match is None else match.group(0)
        return json.loads(data)
    except Exception:
        return None


def find_yt_dlp() -> Optional[Path]:
    for env in ("YTDLP", "YT_DLP"):
        val = os.environ.get(env)
        if val:
            path = Path(val).expanduser()
            if path.exists():
                return path
    which = shutil.which("yt-dlp") or shutil.which("yt_dlp")
    if which:
        return Path(which)
    candidates = [
        Path(".venv/bin/yt-dlp"),
        Path("/opt/homebrew/bin/yt-dlp"),
        Path("~/Library/Python/3.9/bin/yt-dlp").expanduser(),
    ]
    for cand in candidates:
        if cand.exists():
            return cand
    return None


def normalize_date(yyyymmdd: str) -> Optional[str]:
    if not yyyymmdd or not re.match(r"^\d{8}$", yyyymmdd):
        return None
    try:
        dt = datetime.strptime(yyyymmdd, "%Y%m%d")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def clean_text(text: str) -> str:
    paras = re.split(r"\n\s*\n", text.strip(), flags=re.S)
    cleaned: List[str] = []
    for p in paras:
        p = re.sub(r"\[(music|applause|laughter|inaudible)[^\]]*\]", "", p, flags=re.I)
        p = re.sub(r"\((music|applause|laughter|inaudible)[^\)]*\)", "", p, flags=re.I)
        p = re.sub(r"<[^>]+>", "", p)
        p = re.sub(r"\s+", " ", p)
        p = re.sub(r"\s+([,.;:!?])", r"\1", p)
        p = re.sub(r"([,.;:!?])(?!\s|$)", r"\1 ", p)
        p = re.sub(r"\s{2,}", " ", p)
        p = p.strip()
        if p:
            cleaned.append(p)
    return "\n\n".join(cleaned) + "\n"


def enrich_with_ytdlp(url: str, ytdlp: Path, cookies: Optional[Path] = None, browser: str = "") -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    if not ytdlp:
        return meta
    cmd = [str(ytdlp), "--skip-download", "-J", url]
    if cookies:
        cmd += ["--cookies", str(cookies)]
    elif browser:
        cmd += ["--cookies-from-browser", browser]
    data = run_json(cmd)
    if not isinstance(data, dict):
        return meta
    if "entries" in data and isinstance(data["entries"], list) and data["entries"]:
        data = data["entries"][0]
    upload_date = str(data.get("upload_date") or "")
    if upload_date:
        nd = normalize_date(upload_date)
        if nd:
            meta["date"] = nd
    if data.get("webpage_url"):
        meta["source_url"] = data["webpage_url"]
    return meta


def enrich_talks(
    paths: SeriesPaths,
    *,
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    videos_path: Optional[Path] = None,
    use_yt_dlp: bool = False,
    cookies: Optional[Path] = None,
    browser: str = "",
) -> int:
    src_path = input_path or paths.talks_path
    out_path = output_path or src_path
    if not src_path.exists():
        raise FileNotFoundError(f"Missing talks file: {src_path}")

    talks_data = json.loads(src_path.read_text(encoding="utf-8"))
    talks: List[Dict[str, Any]] = talks_data.get("talks") or []

    if use_yt_dlp:
        ytdlp = find_yt_dlp()
    else:
        ytdlp = None

    changed = 0
    for t in talks:
        src = (t.get("source_url") or "").strip()
        txt = (t.get("transcript") or "").rstrip()
        new_txt = clean_text(txt)
        if new_txt != txt + "\n":
            t["transcript"] = new_txt
            changed += 1
        if use_yt_dlp and ytdlp and src and not t.get("date"):
            meta = enrich_with_ytdlp(src, ytdlp, cookies=cookies, browser=browser)
            if meta.get("date") and not t.get("date"):
                t["date"] = meta["date"]
                changed += 1
            if meta.get("source_url") and meta["source_url"] != src:
                t["source_url"] = meta["source_url"]
                changed += 1

    if changed:
        out_path.write_text(json.dumps(talks_data, ensure_ascii=False, indent=2), encoding="utf-8")
    return changed


__all__ = ["clean_text", "enrich_talks", "find_yt_dlp"]
