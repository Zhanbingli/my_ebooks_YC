"""Utilities to download and parse subtitles via yt-dlp."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from . import PROJECT_ROOT
from .paths import SeriesPaths
from .youtube import (
    get_yt_initial_player_response,
    split_title_and_speaker,
    xml_to_paragraphs,
)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)


def run(cmd: List[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def find_yt_dlp() -> Optional[Path]:
    for env_var in ("YTDLP", "YT_DLP"):
        val = os.environ.get(env_var)
        if not val:
            continue
        env_path = Path(val).expanduser()
        if env_path.exists():
            return env_path
    candidates = [
        Path(".venv/bin/yt-dlp"),
        Path("~/Library/Python/3.9/bin/yt-dlp").expanduser(),
        Path("/opt/homebrew/bin/yt-dlp"),
    ]
    which = shutil.which("yt-dlp") or shutil.which("yt_dlp")
    if which:
        candidates.insert(0, Path(which))
    for cand in candidates:
        if cand.exists():
            return cand
    return None


def find_vtt_for_video(subs_dir: Path, video_id: str) -> Optional[Path]:
    if not subs_dir.is_dir():
        return None
    candidates: List[Path] = []
    for path in subs_dir.iterdir():
        if path.suffix.lower() != ".vtt":
            continue
        name = path.name
        if not name.startswith(video_id + ".") and name != f"{video_id}.vtt":
            continue
        candidates.append(path)

    def score(path: Path) -> int:
        name = path.name
        if name.endswith(".en.vtt"):
            return 3
        if name.endswith(".en-US.vtt"):
            return 2
        if name.endswith(".en-GB.vtt"):
            return 2
        return 1

    candidates.sort(key=score, reverse=True)
    return candidates[0] if candidates else None


def parse_vtt_to_paragraphs(path: Path) -> str:
    lines = [ln.rstrip("\n") for ln in path.read_text(encoding="utf-8", errors="replace").splitlines()]
    text_lines: List[str] = []
    for ln in lines:
        if not ln:
            text_lines.append("")
            continue
        if ln.startswith("WEBVTT") or ln.startswith("NOTE"):
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> ", ln):
            continue
        if re.match(r"^\d+$", ln):
            continue
        if re.match(r"^(Kind|Language|Style|Region):", ln, flags=re.IGNORECASE):
            continue
        if "<c>" in ln or re.search(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", ln):
            continue
        clean = re.sub(r"<[^>]+>", "", ln)
        clean = re.sub(r"\[(music|applause|laughter|inaudible)[^\]]*\]", "", clean, flags=re.IGNORECASE)
        trimmed = clean.strip()
        if text_lines and trimmed and text_lines[-1] == trimmed:
            continue
        text_lines.append(trimmed)

    paras: List[str] = []
    buf: List[str] = []
    seen_in_para: set[str] = set()
    for ln in text_lines:
        if not ln.strip():
            continue
        frag = ln.strip()
        if buf and frag:
            last = buf[-1]
            if last == frag:
                continue
            if frag.startswith(last) and len(frag) > len(last) + 2:
                buf[-1] = frag
                continue
            if last.startswith(frag) and len(last) > len(frag) + 2:
                continue
        if frag and frag in seen_in_para:
            continue
        buf.append(frag)
        if frag:
            seen_in_para.add(frag)
        if len(" ".join(buf)) > 800:
            paras.append(" ".join(buf))
            buf = []
            seen_in_para.clear()
    if buf:
        paras.append(" ".join(buf))
    paras = [re.sub(r"\s+", " ", p).strip() for p in paras if p.strip()]
    return "\n\n".join(paras) + "\n"


def load_cookies_from_netscape(path: Path) -> Dict[str, str]:
    jar: Dict[str, str] = {}
    if not path.exists():
        return jar
    for ln in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = ln.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            parts = re.split(r"\s+", line)
            if len(parts) < 7:
                continue
        _, _, _, _, _, name, value = parts[:7]
        if name and value:
            jar[name] = value
    return jar


def cookie_header_from_jar(jar: Dict[str, str]) -> str:
    return "; ".join(f"{k}={v}" for k, v in jar.items())


def http_get(url: str, cookies_path: Optional[Path] = None) -> Optional[str]:
    from urllib.request import Request, urlopen

    headers = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    if cookies_path:
        jar = load_cookies_from_netscape(cookies_path)
        if jar:
            headers["Cookie"] = cookie_header_from_jar(jar)
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=20) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            data = resp.read()
            try:
                return data.decode(charset, errors="replace")
            except LookupError:
                return data.decode("utf-8", errors="replace")
    except Exception:
        return None


def fetch_transcript_via_cookies(video_id: str, cookies_path: Path) -> Optional[str]:
    watch_url = f"https://www.youtube.com/watch?v={video_id}&hl=en"
    html = http_get(watch_url, cookies_path=cookies_path)
    if not html:
        return None
    pr = get_yt_initial_player_response(html)
    if not pr:
        return None
    try:
        tracks = pr.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
    except Exception:
        tracks = []
    if not tracks:
        return None

    def score(track: Dict[str, str]) -> int:
        lang = track.get("languageCode", "")
        name = track.get("name", {})
        score_val = 0
        if lang.startswith("en"):
            score_val += 3
        if "English" in str(name):
            score_val += 1
        if track.get("kind") == "asr":
            score_val += 1
        return score_val

    tracks.sort(key=score, reverse=True)
    base = tracks[0].get("baseUrl")
    if not base:
        return None
    if "fmt=" not in base:
        sep = "&" if "?" in base else "?"
        base = f"{base}{sep}fmt=srv1"
    xml = http_get(base, cookies_path=cookies_path)
    if not xml:
        return None
    return xml_to_paragraphs(xml)


def download_subtitles(
    paths: SeriesPaths,
    *,
    videos_path: Optional[Path] = None,
    cookies: Optional[Path] = None,
    browser: str = "",
    limit: int = 0,
    export_talks_path: Optional[Path] = None,
) -> List[Dict[str, str]]:
    paths.ensure()
    videos_file = videos_path or paths.videos_path
    if not videos_file.exists():
        raise FileNotFoundError(
            f"Missing {videos_file}. Run fetch_yc_ai_startup_school.py --export-videos first."
        )
    data = json.loads(videos_file.read_text(encoding="utf-8"))
    videos = data.get("videos") or []
    if limit and limit > 0:
        videos = videos[:limit]

    subs_dir = paths.transcripts_dir
    subs_dir.mkdir(parents=True, exist_ok=True)

    out_talks_path = export_talks_path or paths.talks_path

    talks: List[Dict[str, str]] = []

    for idx, video in enumerate(videos, start=1):
        vid = video.get("video_id")
        title = video.get("title") or ""
        url = video.get("url")
        print(f"[{idx}/{len(videos)}] {vid} — {title}")
        ytdlp = find_yt_dlp()
        if not ytdlp:
            print("  yt-dlp not found. Install yt-dlp or set YTDLP to its path.")
            rc = 1
        else:
            cmd = [
                str(ytdlp),
                "--skip-download",
                "--write-auto-sub",
                "--write-sub",
                "--sub-lang",
                "en,en-US,en-GB",
                "--sub-format",
                "vtt",
                "--extractor-args",
                "youtube:player_client=web,web_creator,ios|njsig",
                "-o",
                str(subs_dir / "%(id)s.%(ext)s"),
                "--ignore-no-formats-error",
            ]
            if cookies:
                cmd += ["--cookies", str(cookies)]
            elif browser:
                cmd += ["--cookies-from-browser", browser]
            cmd.append(url)
            rc = run(cmd)
        transcript: Optional[str] = None
        if rc == 0:
            vtt = find_vtt_for_video(subs_dir, vid)
            if vtt:
                transcript = parse_vtt_to_paragraphs(vtt)
        if not transcript and cookies:
            print("  yt-dlp failed or no VTT; trying direct fetch with cookies...")
            transcript = fetch_transcript_via_cookies(vid, cookies)
        if not transcript:
            print("  Could not obtain subtitles; skipping")
            continue
        talk_title, speaker = split_title_and_speaker(title)
        talks.append(
            {
                "speaker": speaker or "Unknown Speaker",
                "title": talk_title or title,
                "date": "",
                "source_url": url,
                "transcript": transcript,
            }
        )

    if not talks:
        print("Warning: no subtitles were harvested.")
    payload = {"series": data.get("series") or "YC AI Startup School", "talks": talks}
    out_talks_path.parent.mkdir(parents=True, exist_ok=True)
    out_talks_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        rel = out_talks_path.relative_to(PROJECT_ROOT)
    except ValueError:
        rel = out_talks_path
    print(f"Wrote: {rel} ({len(talks)} talks)")
    return talks


__all__ = ["download_subtitles", "find_yt_dlp", "parse_vtt_to_paragraphs"]
