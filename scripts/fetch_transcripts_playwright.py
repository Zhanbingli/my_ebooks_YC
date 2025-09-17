#!/usr/bin/env python3
import argparse
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ebook_pipeline.config import load_config
from ebook_pipeline.youtube import split_title_and_speaker, xml_to_paragraphs as yt_xml_to_paragraphs


def load_videos(videos_json: str, limit: int = 0) -> List[Dict[str, Any]]:
    if not os.path.exists(videos_json):
        raise FileNotFoundError(f"Missing {videos_json}. Run fetch_yc_ai_startup_school.py --export-videos first.")
    with open(videos_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    videos = data.get('videos') or []
    if limit and limit > 0:
        videos = videos[: limit]
    return videos


def parse_cookies_txt(path: str) -> List[Dict[str, Any]]:
    # Convert Netscape cookies.txt to Playwright cookie objects
    cookies: List[Dict[str, Any]] = []
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
            domain, flag, path_c, secure, expiry, name, value = parts[:7]
            if not name or name.startswith('#'):
                continue
            cookie: Dict[str, Any] = {
                'name': name,
                'value': value,
                'domain': domain.lstrip('.'),
                'path': path_c or '/',
                'secure': (secure.upper() == 'TRUE'),
            }
            try:
                cookie['expires'] = int(expiry)
            except Exception:
                pass
            cookies.append(cookie)
    return cookies


def prefer_en_track(tracks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not tracks:
        return None
    def score(t: Dict[str, Any]) -> int:
        lang = t.get('languageCode') or ''
        s = 0
        if str(lang).startswith('en'):
            s += 3
        if t.get('kind') == 'asr':
            s += 1
        return s
    tracks = list(tracks)
    tracks.sort(key=score, reverse=True)
    return tracks[0]


def xml_to_paragraphs(xml_text: str) -> str:
    # Reuse logic from the shared youtube helpers to keep formatting consistent
    return yt_xml_to_paragraphs(xml_text)


def extract_transcript_via_innertube(page) -> Optional[str]:
    # In page context, read player response and fetch caption baseUrl
    base_url = page.evaluate("""
        () => {
          try {
            const pr = window.ytInitialPlayerResponse || (window.ytcfg && window.ytcfg.data && window.ytcfg.data.PLAYER_RESPONSE) || null;
            if (!pr) return null;
            const tl = pr.captions && pr.captions.playerCaptionsTracklistRenderer && pr.captions.playerCaptionsTracklistRenderer.captionTracks || [];
            if (!tl || !tl.length) return null;
            const en = tl.find(t => (t.languageCode||'').startsWith('en')) || tl[0];
            return en && en.baseUrl || null;
          } catch (e) {
            return null;
          }
        }
    """)
    if not base_url:
        return None
    # Ensure format param
    sep = '&' if '?' in base_url else '?'
    for fmt in ('srv1','srv3','json3','vtt','ttml'):
        url = f"{base_url}{sep}fmt={fmt}"
        try:
            xml = page.evaluate("url => fetch(url, {credentials:'include'}).then(r => r.text())", url)
        except Exception:
            xml = None
        if xml and '<text' in xml:
            return xml
    return None


def extract_transcript_via_ui(page) -> Optional[str]:
    # Try to open the transcript panel and scrape text
    # English and Chinese UI labels
    menu_btn = page.locator("button[aria-label*='More actions'], button[aria-label*='更多操作']").first
    try:
        menu_btn.wait_for(state='visible', timeout=5000)
        menu_btn.click()
    except Exception:
        pass

    # Try menu item
    item = page.locator("ytd-menu-service-item-renderer:has-text('Show transcript'), ytd-menu-service-item-renderer:has-text('显示字幕')").first
    try:
        item.wait_for(state='visible', timeout=5000)
        item.click()
    except Exception:
        # alternative location: within overflow menu at the right of player
        try:
            page.keyboard.press('Shift+/?')  # opens help, sometimes stabilizes UI; harmless if no-op
        except Exception:
            pass
        return None

    # Hide timestamps if toggle exists
    try:
        toggle = page.locator("button[aria-label*='Toggle timestamps'], button:has-text('Toggle timestamps')").first
        if toggle.is_visible():
            toggle.click()
    except Exception:
        pass

    # Collect lines from transcript segments
    try:
        page.wait_for_selector('ytd-transcript-segment-renderer', timeout=5000)
        texts = page.eval_on_selector_all(
            'ytd-transcript-segment-renderer',
            "els => els.map(e => (e.innerText || '').trim()).filter(Boolean)"
        )
        if texts:
            # YouTube often formats as "timestamp\ntext"; remove timestamps and blank lines
            lines: List[str] = []
            for t in texts:
                parts = t.split('\n')
                for p in parts:
                    p = p.strip()
                    if not p:
                        continue
                    # Filter timestamps like 00:12 or 0:12:34
                    if re.match(r"^\d{1,2}:\d{2}(:\d{2})?$", p):
                        continue
                    lines.append(p)
            if lines:
                # Merge into paragraphs roughly every ~800 chars
                paras: List[str] = []
                buf: List[str] = []
                for ln in lines:
                    buf.append(ln)
                    if len(' '.join(buf)) > 800:
                        paras.append(' '.join(buf))
                        buf = []
                if buf:
                    paras.append(' '.join(buf))
                return '\n\n'.join(paras) + '\n'
    except Exception:
        return None
    return None


def main():
    parser = argparse.ArgumentParser(description='Fetch YouTube transcripts via Playwright (Show transcript UI or innertube).')
    parser.add_argument('--series', default='yc-ai-startup-school', help='Series slug configured in config/series.json')
    parser.add_argument('--videos-json', default='', help='Videos list file (from --export-videos)')
    parser.add_argument('--out', default='', help='Output talks JSON path')
    parser.add_argument('--limit', type=int, default=0, help='Limit number of videos to process (0=all)')
    parser.add_argument('--cookies', default='cookies.txt', help='Path to cookies.txt (Netscape format)')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--show', action='store_true', help='Force headful (non-headless) mode for debugging')
    parser.add_argument('--channel', default='chrome', help='Browser channel to use (chrome, chromium, msedge)')
    args = parser.parse_args()

    series = load_config().get(args.series)
    paths = series.to_paths()

    videos_path = Path(args.videos_json) if args.videos_json else paths.videos_path
    out_path = Path(args.out) if args.out else paths.talks_path

    videos = load_videos(str(videos_path), args.limit)
    if not videos:
        raise SystemExit('No videos to process.')

    cookies_path = Path(args.cookies) if args.cookies else None

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser_type = p.chromium
        # Use new Chrome headless if using system Chrome channel
        headless_flag: bool = (args.headless or not args.show)
        extra_args = [
            '--disable-renderer-backgrounding',
            '--disable-background-timer-throttling',
            '--no-sandbox',
        ]
        # Force new headless for system Chrome
        if headless_flag and args.channel:
            extra_args.append('--headless=new')
        launch_kwargs: Dict[str, Any] = {
            'headless': headless_flag,
            'channel': args.channel if args.channel else None,
            'args': extra_args,
        }
        # Remove None values
        launch_kwargs = {k: v for k, v in launch_kwargs.items() if v is not None}

        browser = browser_type.launch(**launch_kwargs)
        context = browser.new_context(
            user_agent=(
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0 Safari/537.36'
            ),
            extra_http_headers={'Accept-Language': 'en-US,en;q=0.9'},
            viewport={'width': 1366, 'height': 900},
        )
        # Add cookies
        if cookies_path and cookies_path.exists():
            cookies = parse_cookies_txt(str(cookies_path))
            # Playwright requires domain cookies without leading dot sometimes; ensure path set
            for ck in cookies:
                if 'path' not in ck or not ck['path']:
                    ck['path'] = '/'
            try:
                context.add_cookies(cookies)
            except Exception:
                # Ignore cookie shape errors
                pass

        page = context.new_page()
        talks: List[Dict[str, Any]] = []
        for i, v in enumerate(videos, start=1):
            vid = v.get('video_id')
            title = v.get('title') or ''
            url = v.get('url')
            print(f"[{i}/{len(videos)}] {vid} — {title}")
            try:
                page.goto(url, wait_until='domcontentloaded', timeout=60000)
            except Exception as e:
                print('  navigation error:', e)
                continue

            transcript_text: Optional[str] = None
            # Try innertube first (fast)
            try:
                xml = extract_transcript_via_innertube(page)
                if xml:
                    transcript_text = xml_to_paragraphs(xml)
            except Exception:
                transcript_text = None
            # Fallback to UI scrape
            if not transcript_text:
                try:
                    t2 = extract_transcript_via_ui(page)
                except Exception:
                    t2 = None
                if t2:
                    transcript_text = t2

            if not transcript_text:
                print('  no transcript available; skipping')
                continue

            talk_title, speaker = split_title_and_speaker(title)
            talks.append({
                'speaker': speaker or 'Unknown Speaker',
                'title': talk_title or title,
                'date': '',
                'source_url': url,
                'transcript': transcript_text.strip() + '\n',
            })

        page.close()
        context.close()
        browser.close()

    if not talks:
        raise SystemExit('No transcripts fetched. Try --show (headful), or confirm cookies and transcript availability.')

    out = {'series': series.title, 'talks': talks}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open('w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"Wrote: {out_path} ({len(talks)} talks)")


if __name__ == '__main__':
    main()
