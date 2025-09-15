#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from typing import Dict, Any, List, Optional, Tuple
import shutil


# Reuse heuristics from fetch script by importing dynamically
sys.path.append(os.path.join(os.path.dirname(__file__)))
from fetch_yc_ai_startup_school import (
    split_title_and_speaker,
    get_yt_initial_player_response,
)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)


def run(cmd: List[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def find_yt_dlp() -> Optional[str]:
    # Prefer env override
    env_path = os.environ.get('YTDLP') or os.environ.get('YT_DLP')
    if env_path and os.path.exists(env_path):
        return env_path
    # macOS user install default path
    mac_user_bin = os.path.expanduser('~/Library/Python/3.9/bin/yt-dlp')
    if os.path.exists(mac_user_bin):
        return mac_user_bin
    # Common PATH lookup
    which = shutil.which('yt-dlp') or shutil.which('yt_dlp')
    if which:
        return which
    # Homebrew path
    brew_bin = '/opt/homebrew/bin/yt-dlp'
    if os.path.exists(brew_bin):
        return brew_bin
    return None


def find_vtt_for_video(subs_dir: str, video_id: str) -> Optional[str]:
    if not os.path.isdir(subs_dir):
        return None
    # yt-dlp usually saves as {id}.{lang}.vtt
    candidates = []
    for name in os.listdir(subs_dir):
        if not name.endswith('.vtt'):
            continue
        if not name.startswith(video_id + ".") and name != f"{video_id}.vtt":
            continue
        candidates.append(os.path.join(subs_dir, name))
    # Prefer en > en-US > en-GB
    def score(path: str) -> int:
        n = os.path.basename(path)
        if n.endswith('.en.vtt'): return 3
        if n.endswith('.en-US.vtt'): return 2
        if n.endswith('.en-GB.vtt'): return 2
        return 1
    candidates.sort(key=score, reverse=True)
    return candidates[0] if candidates else None


def parse_vtt_to_paragraphs(path: str) -> str:
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        lines = [ln.rstrip('\n') for ln in f]
    # Remove header and NOTE lines
    text_lines: List[str] = []
    for ln in lines:
        if not ln:
            text_lines.append("")
            continue
        if ln.startswith('WEBVTT') or ln.startswith('NOTE'):
            continue
        if re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> ", ln):
            # timestamp line; skip
            continue
        # Remove position/cue settings left on same line
        if re.match(r"^\d+$", ln):
            # cue identifier; skip
            continue
        # Skip common VTT metadata lines
        if re.match(r"^(Kind|Language|Style|Region):", ln, flags=re.IGNORECASE):
            continue
        # Skip lines that are character-level time-coded (contain <c> or <00:..>)
        if '<c>' in ln or re.search(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", ln):
            continue
        # Remove simple annotation tags like <...> or [Music]
        clean = re.sub(r"<[^>]+>", "", ln)
        clean = re.sub(r"\[(music|applause|laughter|inaudible)[^\]]*\]", "", clean, flags=re.IGNORECASE)
        # Skip consecutive duplicates
        trimmed = clean.strip()
        if text_lines and trimmed and text_lines[-1] == trimmed:
            continue
        text_lines.append(trimmed)

    # Merge into paragraphs on blank lines and also cap by length
    paras: List[str] = []
    buf: List[str] = []
    seen_in_para = set()
    for ln in text_lines:
        if not ln.strip():
            # treat blank as soft separator; do not flush paragraph immediately
            continue
        frag = ln.strip()
        if buf and frag:
            last = buf[-1]
            if last == frag:
                # avoid consecutive duplicates
                continue
            # Roll-up captions: if new line extends the last line, replace it
            if frag.startswith(last) and len(frag) > len(last) + 2:
                buf[-1] = frag
                continue
            # Conversely, if last is an extension of current, drop current
            if last.startswith(frag) and len(last) > len(frag) + 2:
                continue
        if frag and frag in seen_in_para:
            # avoid duplicate lines within the same paragraph
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
    # Cleanup spaces
    paras = [re.sub(r"\s+", " ", p).strip() for p in paras if p.strip()]
    return "\n\n".join(paras) + "\n"


def load_cookies_from_netscape(path: str) -> Dict[str, str]:
    jar: Dict[str, str] = {}
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            for ln in f:
                ln = ln.strip()
                if not ln or ln.startswith('#'):
                    continue
                parts = ln.split('\t')
                if len(parts) < 7:
                    parts = re.split(r"\s+", ln)
                    if len(parts) < 7:
                        continue
                domain, flag, path_cookie, secure, expiry, name, value = parts[:7]
                if name and value:
                    jar[name] = value
    except FileNotFoundError:
        pass
    return jar


def cookie_header_from_jar(jar: Dict[str, str]) -> str:
    return "; ".join([f"{k}={v}" for k, v in jar.items()])


def http_get(url: str, cookies_path: Optional[str] = None) -> Optional[str]:
    from urllib.request import Request, urlopen
    headers = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    if cookies_path:
        jar = load_cookies_from_netscape(cookies_path)
        if jar:
            headers["Cookie"] = cookie_header_from_jar(jar)
    try:
        req = Request(url, headers=headers)
        with urlopen(req, timeout=20) as resp:
            charset = resp.headers.get_content_charset() or 'utf-8'
            data = resp.read()
            try:
                return data.decode(charset, errors='replace')
            except LookupError:
                return data.decode('utf-8', errors='replace')
    except Exception:
        return None


def fetch_transcript_via_cookies(video_id: str, cookies_path: str) -> Optional[str]:
    # Fetch watch page with cookies, parse caption track baseUrl and download XML
    watch_url = f"https://www.youtube.com/watch?v={video_id}&hl=en"
    html = http_get(watch_url, cookies_path=cookies_path)
    if not html:
        return None
    pr = get_yt_initial_player_response(html)
    if not pr:
        return None
    try:
        tracks = pr.get('captions', {}).get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
    except Exception:
        tracks = []
    if not tracks:
        return None
    # Prefer English, then first
    def score(t: Dict[str, Any]) -> int:
        lang = t.get('languageCode', '')
        name = t.get('name', {})
        s = 0
        if lang.startswith('en'): s += 3
        if 'English' in str(name): s += 1
        if t.get('kind') == 'asr': s += 1
        return s
    tracks.sort(key=score, reverse=True)
    base = tracks[0].get('baseUrl')
    if not base:
        return None
    if 'fmt=' not in base:
        sep = '&' if '?' in base else '?'
        base = base + f"{sep}fmt=srv1"
    xml = http_get(base, cookies_path=cookies_path)
    if not xml:
        return None
    # Reuse xml->paragraphs from fetch script
    from fetch_yc_ai_startup_school import xml_to_paragraphs  # type: ignore
    return xml_to_paragraphs(xml)


def main():
    parser = argparse.ArgumentParser(description="Download subtitles with yt-dlp (using browser cookies) and build talks.json")
    parser.add_argument("--videos-json", default="build/videos.json", help="Path to videos list exported by fetch script.")
    parser.add_argument("--browser", default="", help="Browser name for --cookies-from-browser (e.g., 'safari', 'chrome', 'edge', 'firefox').")
    parser.add_argument("--cookies", default="", help="Path to cookies.txt file (netscape format) to pass to yt-dlp.")
    parser.add_argument("--out", default="talks.json", help="Output talks JSON path.")
    parser.add_argument("--subs-dir", default="build/subs", help="Directory to store downloaded subtitle files.")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of videos processed (0=all).")
    args = parser.parse_args()

    if not os.path.exists(args.videos_json):
        print(f"Missing {args.videos_json}. Run fetch_yc_ai_startup_school.py with --export-videos first.", file=sys.stderr)
        sys.exit(1)

    with open(args.videos_json, 'r', encoding='utf-8') as f:
        vdata = json.load(f)
    videos = vdata.get('videos') or []
    if args.limit and args.limit > 0:
        videos = videos[: args.limit]

    os.makedirs(args.subs_dir, exist_ok=True)
    talks: List[Dict[str, Any]] = []

    for i, v in enumerate(videos, start=1):
        vid = v.get('video_id')
        title = v.get('title') or ''
        url = v.get('url')
        print(f"[{i}/{len(videos)}] {vid} — {title}")
        # Download subs
        ytdlp = find_yt_dlp()
        if not ytdlp:
            print("  yt-dlp not found. Please install yt-dlp or set YTDLP env var to its path.", file=sys.stderr)
            rc = 1
        else:
            cmd = [ytdlp,
                   '--skip-download',
                   '--write-auto-sub', '--write-sub',
                   '--sub-lang', 'en,en-US,en-GB',
                   '--sub-format', 'vtt',
                   # Improve YouTube handling by selecting web/ios clients and disabling throttling side-effects
                   '--extractor-args', 'youtube:player_client=web,web_creator,ios|njsig']
            # Output template into subs dir
            cmd += ['-o', os.path.join(args.subs_dir, '%(id)s.%(ext)s')]
            # Be tolerant if no streams are downloadable
            cmd += ['--ignore-no-formats-error']
            if args.cookies:
                cmd += ['--cookies', args.cookies]
            elif args.browser:
                cmd += ['--cookies-from-browser', args.browser]
            cmd.append(url)
            rc = run(cmd)
        transcript = None
        if rc == 0:
            vtt = find_vtt_for_video(args.subs_dir, vid)
            if vtt:
                transcript = parse_vtt_to_paragraphs(vtt)
        if not transcript and args.cookies:
            print("  yt-dlp failed or no VTT; trying direct fetch with cookies...")
            transcript = fetch_transcript_via_cookies(vid, args.cookies)
        if not transcript:
            print("  Could not obtain subtitles; skipping")
            continue
        talk_title, speaker = split_title_and_speaker(title)
        talks.append({
            'speaker': speaker or 'Unknown Speaker',
            'title': talk_title or title,
            'date': '',
            'source_url': url,
            'transcript': transcript,
        })

    if not talks:
        print("No talks processed. Ensure your browser is supported and logged into YouTube, then re-run with --browser option.", file=sys.stderr)
        sys.exit(2)

    out = {
        'series': 'YC AI Startup School',
        'talks': talks,
    }
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote: {args.out} ({len(talks)} talks)")


if __name__ == '__main__':
    main()
