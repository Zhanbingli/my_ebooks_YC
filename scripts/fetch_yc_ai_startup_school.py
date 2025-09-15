#!/usr/bin/env python3
import argparse
import html
import json
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Iterable
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)


def fetch(url: str, retries: int = 3, sleep: float = 0.5) -> str:
    last_err = None
    for i in range(retries):
        try:
            req = Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
            with urlopen(req, timeout=20) as resp:
                charset = resp.headers.get_content_charset() or "utf-8"
                data = resp.read()
                try:
                    return data.decode(charset, errors="replace")
                except LookupError:
                    return data.decode("utf-8", errors="replace")
        except (URLError, HTTPError) as e:
            last_err = e
            time.sleep(sleep)
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def _extract_braced_json(source: str, anchor: str) -> Optional[str]:
    # Find anchor and extract balanced-brace JSON starting at the first '{' after it.
    idx = source.find(anchor)
    if idx == -1:
        return None
    brace_start = source.find('{', idx)
    if brace_start == -1:
        return None
    depth = 0
    for j in range(brace_start, len(source)):
        c = source[j]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return source[brace_start:j+1]
    return None


def get_yt_initial_data(html_text: str) -> Optional[Dict[str, Any]]:
    # Try various patterns that appear on YouTube pages.
    patterns = [
        "ytInitialData = ",
        "var ytInitialData = ",
        ">ytInitialData\"\s*:\s*",
    ]
    for p in patterns:
        js = _extract_braced_json(html_text, p)
        if js:
            try:
                return json.loads(js)
            except json.JSONDecodeError:
                continue
    return None


def get_yt_initial_player_response(html_text: str) -> Optional[Dict[str, Any]]:
    patterns = [
        "ytInitialPlayerResponse = ",
        "var ytInitialPlayerResponse = ",
        "\"ytInitialPlayerResponse\"\s*:\s*",
    ]
    # Try each pattern; if multiple matches exist, scan forward to find one with videoDetails
    for p in patterns:
        start = 0
        while True:
            idx = html_text.find(p, start)
            if idx == -1:
                break
            js = _extract_braced_json(html_text[idx:], p)
            if js:
                try:
                    obj = json.loads(js)
                    if isinstance(obj, dict) and ('videoDetails' in obj or 'captions' in obj):
                        return obj
                except json.JSONDecodeError:
                    pass
            start = idx + len(p)
    return None


def fetch_video_meta(video_id: str) -> Dict[str, Any]:
    url = f"https://www.youtube.com/watch?v={video_id}&hl=en"
    html_text = fetch(url)
    pr = get_yt_initial_player_response(html_text) or {}
    vd = pr.get('videoDetails', {})
    mf = pr.get('microformat', {}).get('playerMicroformatRenderer', {})
    meta = {
        'shortDescription': vd.get('shortDescription') or '',
        'author': vd.get('author') or '',
        'publishDate': mf.get('publishDate') or '',
    }
    return meta


def rfind(obj: Any, key: str) -> Iterable[Any]:
    # Recursively yield values for given key in nested dict/list.
    if isinstance(obj, dict):
        if key in obj:
            yield obj[key]
        for v in obj.values():
            yield from rfind(v, key)
    elif isinstance(obj, list):
        for item in obj:
            yield from rfind(item, key)


def text_from_runs(node: Dict[str, Any]) -> str:
    if not node:
        return ""
    if "simpleText" in node and isinstance(node["simpleText"], str):
        return node["simpleText"]
    runs = node.get("runs") or []
    return "".join(run.get("text", "") for run in runs if isinstance(run, dict))


def _score_title_for_series(title: str) -> int:
    t = title.lower()
    s = 0
    if "ai" in t: s += 2
    if "startup" in t: s += 2
    if "school" in t: s += 2
    if "yc" in t or "y combinator" in t: s += 1
    if "ai startup school" in t: s += 5
    return s


def find_playlist_id(query: str = "YC AI Startup School") -> Optional[str]:
    # Strategy 1: YouTube search results
    try:
        url = f"https://www.youtube.com/results?search_query={quote_plus(query + ' playlist')}"
        html_text = fetch(url)
        data = get_yt_initial_data(html_text)
        if data:
            candidates: List[Tuple[str, str]] = []
            for pr in rfind(data, "playlistRenderer"):
                if not isinstance(pr, dict):
                    continue
                plid = pr.get("playlistId")
                title = text_from_runs(pr.get("title") or {})
                if plid and title:
                    candidates.append((plid, title))
            if candidates:
                candidates.sort(key=lambda x: _score_title_for_series(x[1]), reverse=True)
                return candidates[0][0]
    except Exception:
        pass

    # Strategy 2: YC channel playlists page
    try:
        ch_url = "https://www.youtube.com/@ycombinator/playlists"
        ch_html = fetch(ch_url)
        data = get_yt_initial_data(ch_html)
        if data:
            candidates: List[Tuple[str, str]] = []
            for gr in rfind(data, "gridPlaylistRenderer"):
                if not isinstance(gr, dict):
                    continue
                plid = gr.get("playlistId")
                title = text_from_runs(gr.get("title") or {})
                if plid and title:
                    candidates.append((plid, title))
            if candidates:
                candidates.sort(key=lambda x: _score_title_for_series(x[1]), reverse=True)
                return candidates[0][0]
    except Exception:
        pass

    # Strategy 3: YC channel search page
    try:
        ch_search = f"https://www.youtube.com/@ycombinator/search?query={quote_plus(query)}"
        ch_html = fetch(ch_search)
        data = get_yt_initial_data(ch_html)
        if data:
            candidates: List[Tuple[str, str]] = []
            for pr in rfind(data, "playlistRenderer"):
                if not isinstance(pr, dict):
                    continue
                plid = pr.get("playlistId")
                title = text_from_runs(pr.get("title") or {})
                if plid and title:
                    candidates.append((plid, title))
            if candidates:
                candidates.sort(key=lambda x: _score_title_for_series(x[1]), reverse=True)
                return candidates[0][0]
    except Exception:
        pass

    return None


def get_playlist_videos(playlist_id: str) -> List[Dict[str, Any]]:
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    html_text = fetch(url)
    data = get_yt_initial_data(html_text)
    if not data:
        raise RuntimeError("Could not parse ytInitialData for playlist page")

    videos: List[Dict[str, Any]] = []
    for pvr in rfind(data, "playlistVideoRenderer"):
        if not isinstance(pvr, dict):
            continue
        vid = pvr.get("videoId")
        title = text_from_runs(pvr.get("title") or {})
        if not vid or not title:
            continue
        videos.append({
            "video_id": vid,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={vid}",
        })
    # Deduplicate (playlist may repeat in renderer)
    seen = set()
    uniq: List[Dict[str, Any]] = []
    for v in videos:
        if v["video_id"] in seen:
            continue
        seen.add(v["video_id"])
        uniq.append(v)
    return uniq


def clean_title_for_series(title: str) -> str:
    t = title
    # Remove series suffixes like "| AI Startup School" or "- AI Startup School"
    t = re.sub(r"\s*[|\-]\s*ai startup school.*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*\(ai startup school.*\)$", "", t, flags=re.IGNORECASE)
    return t.strip()


def looks_like_person(name: str) -> bool:
    tokens = name.replace("–", "-").replace("—", "-").split()
    if not (1 <= len(tokens) <= 6):
        return False
    good = 0
    for tok in tokens:
        # Allow initials like "J." and hyphenated parts
        parts = tok.split('-')
        ok = all(p and p[0].isupper() for p in parts if p)
        if ok:
            good += 1
    return good >= max(1, len(tokens) - 1)


def split_title_and_speaker(raw_title: str) -> Tuple[str, Optional[str]]:
    t = clean_title_for_series(raw_title)

    # Common patterns: "Speaker: Talk", "Talk by Speaker", "Speaker - Talk"
    # 1) A by B
    m = re.search(r"(.+?)\s+by\s+(.+)$", t, flags=re.IGNORECASE)
    if m:
        talk, speaker = m.group(1).strip(), m.group(2).strip()
        if looks_like_person(speaker):
            return talk, speaker

    # 1.5) A with B
    m = re.search(r"(.+?)\s+with\s+(.+)$", t, flags=re.IGNORECASE)
    if m:
        talk, speaker = m.group(1).strip(), m.group(2).strip()
        if looks_like_person(speaker):
            return talk, speaker

    # 2) A: B (if A looks like person)
    m = re.search(r"^([^:]+):\s*(.+)$", t)
    if m:
        left, right = m.group(1).strip(), m.group(2).strip()
        if looks_like_person(left):
            return right, left

    # 3) A - B (if A looks like person)
    m = re.search(r"^([^\-|–—]+)[\-|–—]\s*(.+)$", t)
    if m:
        left, right = m.group(1).strip(), m.group(2).strip()
        if looks_like_person(left):
            return right, left

    # 4) A | ... Name
    if '|' in t:
        left, right = t.rsplit('|', 1)
        right = right.strip()
        # Often right side ends with a name, possibly with titles
        # e.g., "Anthropic Co-founder Jared Kaplan" -> take tail tokens that look like a person
        tokens = right.split()
        # Extract last 2-4 tokens as candidate name
        for take in (4, 3, 2):
            if len(tokens) >= take:
                cand = ' '.join(tokens[-take:])
                if looks_like_person(cand):
                    return left.strip(), cand

    # 4) Default: all title, speaker unknown
    return t, None


def fetch_transcript_xml(video_id: str, langs: List[str]) -> Optional[str]:
    base = f"https://www.youtube.com/api/timedtext?v={video_id}"
    # Try non-ASR first, then ASR.
    for lang in langs:
        for kind in (None, "asr"):
            url = base + f"&lang={lang}"
            if kind:
                url += f"&kind={kind}"
            try:
                xml_text = fetch(url)
            except Exception:
                continue
            if xml_text.strip().startswith("<transcript") and "<text" in xml_text:
                return xml_text
    return None


def fetch_transcript_from_player_response(video_id: str) -> Optional[str]:
    # Load watch page and try to extract caption tracks from player response.
    url = f"https://www.youtube.com/watch?v={video_id}&hl=en"
    try:
        html_text = fetch(url)
        pr = get_yt_initial_player_response(html_text)
    except Exception:
        pr = None
    if not pr:
        return None
    try:
        tracks = pr.get('captions', {}).get('playerCaptionsTracklistRenderer', {}).get('captionTracks', [])
    except Exception:
        tracks = []
    # Prefer English tracks
    def track_score(t: Dict[str, Any]) -> int:
        lang = t.get('languageCode', '')
        name = text_from_runs(t.get('name') or {})
        s = 0
        if lang.startswith('en'): s += 3
        if 'English' in name: s += 2
        if t.get('kind') == 'asr': s += 1
        return s
    if not tracks:
        return None
    tracks.sort(key=track_score, reverse=True)
    base_url = tracks[0].get('baseUrl')
    if not base_url:
        return None
    # Ensure we get XML format
    if 'fmt=' not in base_url:
        sep = '&' if '?' in base_url else '?'
        base_url = base_url + f"{sep}fmt=srv1"
    try:
        return fetch(base_url)
    except Exception:
        return None


def xml_to_paragraphs(xml_text: str) -> str:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return ""

    lines: List[Tuple[float, float, str]] = []  # (start, end, text)
    for node in root.findall("text"):
        start = float(node.attrib.get("start", "0"))
        dur = float(node.attrib.get("dur", "2"))
        end = start + dur
        # Node text may be inside; needs unescape and replace newlines
        raw = node.text or ""
        txt = html.unescape(raw).replace("\n", " ").strip()
        if not txt:
            continue
        lines.append((start, end, txt))

    if not lines:
        return ""

    # Merge lines into paragraphs based on time gaps
    lines.sort(key=lambda x: x[0])
    paras: List[str] = []
    buf: List[str] = []
    last_end = lines[0][1]
    for i, (s, e, txt) in enumerate(lines):
        gap = s - last_end
        if gap > 2.5 and buf:
            paras.append(" ".join(buf))
            buf = []
        buf.append(txt)
        last_end = e
        # Also break long paragraphs
        if len(" ".join(buf)) > 800:
            paras.append(" ".join(buf))
            buf = []
    if buf:
        paras.append(" ".join(buf))

    # Final cleanup: collapse spaces
    paras = [re.sub(r"\s+", " ", p).strip() for p in paras if p.strip()]
    return "\n\n".join(paras) + "\n"


def fetch_transcript_with_library(video_id: str, langs: List[str]) -> Optional[str]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except Exception:
        return None
    # Try languages in order; fall back to translated transcript to English.
    for lang in langs:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])
            break
        except Exception:
            transcript = None
    if transcript is None:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        except Exception:
            transcript = None
    if transcript is None:
        try:
            # Try translated transcript to English if original not available
            full = YouTubeTranscriptApi.list_transcripts(video_id)
            for tr in full:
                try:
                    translated = tr.translate('en')
                    transcript = translated.fetch()
                    break
                except Exception:
                    continue
        except Exception:
            transcript = None
    if not transcript:
        return None
    # transcript is a list of dicts: {'text': str, 'start': float, 'duration': float}
    lines = []
    last_end = 0.0
    buf: List[str] = []
    paras: List[str] = []
    for item in transcript:
        s = float(item.get('start', 0.0))
        d = float(item.get('duration', 0.0))
        e = s + d
        txt = (item.get('text') or '').replace('\n', ' ').strip()
        if not txt:
            continue
        if s - last_end > 2.5 and buf:
            paras.append(' '.join(buf))
            buf = []
        buf.append(txt)
        last_end = e
        if len(' '.join(buf)) > 800:
            paras.append(' '.join(buf))
            buf = []
    if buf:
        paras.append(' '.join(buf))
    paras = [re.sub(r"\s+", " ", p).strip() for p in paras if p.strip()]
    return "\n\n".join(paras) + "\n"


def assemble_talk_entry(video: Dict[str, Any], langs: List[str]) -> Optional[Dict[str, Any]]:
    raw_title = video.get("title", "").strip()
    talk_title, speaker = split_title_and_speaker(raw_title)
    # Prefer robust library if available
    transcript = fetch_transcript_with_library(video["video_id"], langs) or ""
    if not transcript:
        # Try via player response caption track
        xml_text = fetch_transcript_from_player_response(video["video_id"]) or fetch_transcript_xml(video["video_id"], langs)
        transcript = xml_to_paragraphs(xml_text) if xml_text else ""
    date = ""
    if not transcript:
        # Fallback: use video description as a summary placeholder
        try:
            meta = fetch_video_meta(video["video_id"])  # may raise
        except Exception:
            meta = {}
        desc = (meta.get('shortDescription') or '').strip()
        date = (meta.get('publishDate') or '').strip()
        if desc:
            transcript = "Description (not a full transcript):\n\n" + desc + "\n"
    if not transcript:
        # Skip if no transcript at all
        return None
    return {
        "speaker": speaker or "Unknown Speaker",
        "title": talk_title or raw_title or "Untitled",
        "date": date,
        "source_url": video.get("url"),
        "transcript": transcript.strip() + "\n",
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch YC AI Startup School talks and transcripts from YouTube playlist.")
    parser.add_argument("--playlist-id", default="", help="Override playlist ID (if known).")
    parser.add_argument("--query", default="YC AI Startup School", help="Search query to discover playlist.")
    parser.add_argument("--langs", default="en,en-US,en-GB", help="Comma-separated language codes to try.")
    parser.add_argument("--limit", type=int, default=0, help="Max number of videos to process (0=all).")
    parser.add_argument("--out", default="talks.json", help="Output JSON file path.")
    parser.add_argument("--export-videos", action="store_true", help="Export video list to build/videos.json for external subtitle fetching.")
    args = parser.parse_args()

    langs = [l.strip() for l in args.langs.split(',') if l.strip()]

    playlist_id = args.playlist_id.strip()
    if not playlist_id:
        playlist_id = find_playlist_id(args.query)
    if not playlist_id:
        print("Could not find playlist id from search.", file=sys.stderr)
        sys.exit(1)

    print(f"Using playlist: {playlist_id}")
    videos = get_playlist_videos(playlist_id)
    if args.limit and args.limit > 0:
        videos = videos[: args.limit]

    talks: List[Dict[str, Any]] = []
    exported_list: List[Dict[str, Any]] = []
    for i, v in enumerate(videos, start=1):
        vid = v.get("video_id")
        title = v.get("title")
        print(f"[{i}/{len(videos)}] Fetching transcript for {vid} — {title}")
        try:
            entry = assemble_talk_entry(v, langs)
        except Exception as e:
            print(f"  Error: {e}")
            entry = None
        if entry:
            talks.append(entry)
        else:
            print("  Skipped (no transcript)")
        exported_list.append({
            "video_id": v.get("video_id"),
            "title": v.get("title"),
            "url": v.get("url"),
        })
        time.sleep(0.3)

    if args.export_videos:
        os.makedirs('build', exist_ok=True)
        with open('build/videos.json', 'w', encoding='utf-8') as f:
            json.dump({"playlist_id": playlist_id, "videos": exported_list}, f, ensure_ascii=False, indent=2)
        print("Exported video list to build/videos.json")

    if not talks:
        print("No talks with transcripts found.", file=sys.stderr)
        # still write an empty talks.json for downstream scripts
        with open(args.out, 'w', encoding='utf-8') as f:
            json.dump({"series": "YC AI Startup School", "talks": []}, f, ensure_ascii=False, indent=2)
        sys.exit(2)

    data = {"series": "YC AI Startup School", "talks": talks}
    with open(args.out, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Wrote: {args.out} ({len(talks)} talks)")


if __name__ == "__main__":
    main()
