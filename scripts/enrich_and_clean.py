#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional


def run_json(cmd: List[str]) -> Optional[Dict[str, Any]]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        txt = out.decode('utf-8', errors='replace')
        # yt-dlp may emit non-JSON warnings on some stderr merged; try last JSON-looking line
        # But since we merged stderr into stdout, try to find first JSON object
        m = re.search(r"\{.*\}\s*$", txt, flags=re.S)
        data = txt if m is None else m.group(0)
        return json.loads(data)
    except Exception:
        return None


def find_yt_dlp() -> Optional[str]:
    import shutil
    env_path = os.environ.get('YTDLP') or os.environ.get('YT_DLP')
    if env_path and os.path.exists(env_path):
        return env_path
    # venv
    cand = os.path.join('.venv', 'bin', 'yt-dlp')
    if os.path.exists(cand):
        return cand
    which = shutil.which('yt-dlp') or shutil.which('yt_dlp')
    if which:
        return which
    for p in ['/opt/homebrew/bin/yt-dlp', os.path.expanduser('~/Library/Python/3.9/bin/yt-dlp')]:
        if os.path.exists(p):
            return p
    return None


def normalize_date(yyyymmdd: str) -> Optional[str]:
    if not yyyymmdd:
        return None
    if not re.match(r"^\d{8}$", yyyymmdd):
        return None
    try:
        dt = datetime.strptime(yyyymmdd, '%Y%m%d')
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return None


def clean_text(text: str) -> str:
    # Preserve paragraph structure; operate per paragraph
    paras = re.split(r"\n\s*\n", text.strip(), flags=re.S)
    cleaned: List[str] = []
    for p in paras:
        # Remove bracketed noise like [Music], (Applause), <...>
        p = re.sub(r"\[(music|applause|laughter|inaudible)[^\]]*\]", "", p, flags=re.I)
        p = re.sub(r"\((music|applause|laughter|inaudible)[^\)]*\)", "", p, flags=re.I)
        p = re.sub(r"<[^>]+>", "", p)
        # Collapse repeated punctuation and spaces
        p = re.sub(r"\s+", " ", p)
        p = re.sub(r"\s+([,.;:!?])", r"\1", p)
        p = re.sub(r"([,.;:!?])(?!\s|$)", r"\1 ", p)
        p = re.sub(r"\s{2,}", " ", p)
        p = p.strip()
        if p:
            cleaned.append(p)
    return "\n\n".join(cleaned) + "\n"


def enrich_with_ytdlp(url: str, ytdlp: str, cookies: str = "", browser: str = "") -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    if not ytdlp:
        return meta
    cmd = [ytdlp, '--skip-download', '-J', url]
    if cookies:
        cmd += ['--cookies', cookies]
    elif browser:
        cmd += ['--cookies-from-browser', browser]
    data = run_json(cmd)
    if not isinstance(data, dict):
        return meta
    # video JSON may be wrapped under 'entries' for playlists; handle both
    if 'entries' in data and isinstance(data['entries'], list) and data['entries']:
        data = data['entries'][0]
    upload_date = str(data.get('upload_date') or "")
    if upload_date:
        nd = normalize_date(upload_date)
        if nd:
            meta['date'] = nd
    # Ensure source_url normalized
    if data.get('webpage_url'):
        meta['source_url'] = data['webpage_url']
    return meta


def main():
    ap = argparse.ArgumentParser(description='Clean transcripts and enrich talks.json with metadata like date via yt-dlp')
    ap.add_argument('--in', dest='in_path', default='talks.json', help='Input talks.json')
    ap.add_argument('--out', dest='out_path', default='talks.json', help='Output talks.json (overwrites by default)')
    ap.add_argument('--videos-json', default='build/videos.json', help='Optional videos list for reference')
    ap.add_argument('--use-yt-dlp', action='store_true', help='Use yt-dlp to fetch missing metadata (upload date)')
    ap.add_argument('--cookies', default='', help='Path to cookies.txt for yt-dlp')
    ap.add_argument('--browser', default='', help='Browser name for yt-dlp --cookies-from-browser (chrome, safari, edge, firefox)')
    args = ap.parse_args()

    with open(args.in_path, 'r', encoding='utf-8') as f:
        talks_data = json.load(f)
    talks: List[Dict[str, Any]] = talks_data.get('talks') or []

    video_map: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(args.videos_json):
        try:
            with open(args.videos_json, 'r', encoding='utf-8') as vf:
                vdata = json.load(vf)
            for v in (vdata.get('videos') or []):
                if isinstance(v, dict) and v.get('url'):
                    video_map[v['url']] = v
        except Exception:
            pass

    ytdlp = find_yt_dlp() if args.use_yt_dlp else None

    changed = 0
    for t in talks:
        src = (t.get('source_url') or '').strip()
        # Clean transcript
        txt = (t.get('transcript') or '').rstrip()
        new_txt = clean_text(txt)
        if new_txt != (txt + "\n"):
            t['transcript'] = new_txt
            changed += 1

        # Fill date via yt-dlp if missing
        if args.use_yt_dlp and (not t.get('date')) and src:
            meta = enrich_with_ytdlp(src, ytdlp or '', args.cookies, args.browser)
            if meta.get('date') and not t.get('date'):
                t['date'] = meta['date']
                changed += 1
            if meta.get('source_url') and meta['source_url'] != src:
                t['source_url'] = meta['source_url']
                changed += 1

    if changed:
        with open(args.out_path, 'w', encoding='utf-8') as f:
            json.dump(talks_data, f, ensure_ascii=False, indent=2)
        print(f'Updated talks: {changed} changes written to {args.out_path}')
    else:
        print('No changes required (transcripts clean and metadata present).')


if __name__ == '__main__':
    main()

