# Module with helpers to discover YC AI Startup School videos and transcripts.
import html
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Iterable
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET

from . import PROJECT_ROOT
from .paths import SeriesPaths


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)


def extract_video_id(url_or_id: str) -> Optional[str]:
    """Return an 11-character video id from a YouTube URL or a bare id."""

    candidate = (url_or_id or "").strip()
    if not candidate:
        return None
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", candidate):
        return candidate
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", candidate)
    if m:
        return m.group(1)
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", candidate)
    if m:
        return m.group(1)
    return None


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
        'title': vd.get('title') or '',
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
    transcript = None
    try:
        # New API (v1.2+): instance methods
        api = YouTubeTranscriptApi()
        # Try preferred languages
        try:
            transcript = api.fetch(video_id, languages=langs)
        except Exception:
            # Try English fallback
            try:
                transcript = api.fetch(video_id, languages=['en'])
            except Exception:
                transcript = None
        if transcript is None:
            # Try translated transcript to English
            try:
                tl = api.list(video_id)
                for tr in tl:
                    try:
                        t = tr.translate('en').fetch()
                        if t:
                            transcript = t
                            break
                    except Exception:
                        continue
            except Exception:
                transcript = None
    except TypeError:
        # Older API with static methods
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
    # transcript is a list of dicts or objects with attrs: text, start, duration
    lines = []
    last_end = 0.0
    buf: List[str] = []
    paras: List[str] = []
    for item in transcript:
        if isinstance(item, dict):
            s = float(item.get('start', 0.0))
            d = float(item.get('duration', 0.0))
            txt = (item.get('text') or '')
        else:
            s = float(getattr(item, 'start', 0.0))
            d = float(getattr(item, 'duration', 0.0))
            txt = getattr(item, 'text', '')
        e = s + d
        txt = str(txt).replace('\n', ' ').strip()
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


def fetch_single_transcript(video_url_or_id: str, langs: List[str]) -> Optional[Dict[str, str]]:
    """Fetch a single video's transcript plus basic metadata."""

    vid = extract_video_id(video_url_or_id)
    if not vid:
        raise ValueError("Invalid YouTube URL or video id.")

    transcript = fetch_transcript_with_library(vid, langs) or ""
    if not transcript:
        xml_text = fetch_transcript_from_player_response(vid) or fetch_transcript_xml(vid, langs)
        transcript = xml_to_paragraphs(xml_text) if xml_text else ""

    try:
        meta = fetch_video_meta(vid)
    except Exception:
        meta = {}

    raw_title = (meta.get("title") or "").strip()
    talk_title, speaker = split_title_and_speaker(raw_title or vid)
    if not talk_title:
        talk_title = raw_title or f"Video {vid}"
    if not speaker:
        speaker = meta.get("author") or "Unknown Speaker"

    if not transcript:
        return None

    return {
        "video_id": vid,
        "title": talk_title,
        "speaker": speaker,
        "date": meta.get("publishDate") or "",
        "source_url": f"https://www.youtube.com/watch?v={vid}",
        "transcript": transcript.strip() + "\n",
        "raw_title": raw_title or "",
    }


class PlaylistDiscoveryError(RuntimeError):
    """Raised when a playlist cannot be discovered."""


def fetch_and_store(
    paths: SeriesPaths,
    *,
    languages: List[str],
    playlist_id: Optional[str] = None,
    query: str = "YC AI Startup School",
    limit: int = 0,
    export_videos: bool = True,
    series_title: str = "YC AI Startup School",
    sleep: float = 0.3,
    talks_path: Optional[Path] = None,
    videos_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Fetch playlist videos, pull transcripts, and persist to disk.

    Returns a dictionary with playlist metadata, the exported video list,
    and the talks collection that was written to ``paths.talks_path``.
    """

    paths.ensure()

    resolved_playlist = (playlist_id or "").strip()
    if not resolved_playlist:
        resolved_playlist = find_playlist_id(query)
    if not resolved_playlist:
        raise PlaylistDiscoveryError(
            "Could not resolve a YouTube playlist. Provide --playlist-id or adjust the query."
        )

    videos = get_playlist_videos(resolved_playlist)
    if limit and limit > 0:
        videos = videos[:limit]

    talks: List[Dict[str, Any]] = []
    exported_list: List[Dict[str, Any]] = []
    for idx, video in enumerate(videos, start=1):
        vid = video.get("video_id")
        title = video.get("title")
        print(f"[{idx}/{len(videos)}] Fetching transcript for {vid} — {title}")
        try:
            entry = assemble_talk_entry(video, languages)
        except Exception as exc:  # pragma: no cover - defensive fallback
            print(f"  Error: {exc}")
            entry = None
        if entry:
            talks.append(entry)
        else:
            print("  Skipped (no transcript)")
        exported_list.append(
            {
                "video_id": video.get("video_id"),
                "title": video.get("title"),
                "url": video.get("url"),
            }
        )
        time.sleep(sleep)

    target_videos = videos_path or paths.videos_path
    if export_videos:
        payload = {"playlist_id": resolved_playlist, "videos": exported_list}
        with open(target_videos, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        try:
            rel_video = target_videos.relative_to(PROJECT_ROOT)
        except ValueError:
            rel_video = target_videos
        print(f"Exported video list to {rel_video}")

    target_talks = talks_path or paths.talks_path
    talks_payload = {"series": series_title, "talks": talks}
    with open(target_talks, "w", encoding="utf-8") as fh:
        json.dump(talks_payload, fh, ensure_ascii=False, indent=2)
    try:
        rel_talks = target_talks.relative_to(PROJECT_ROOT)
    except ValueError:
        rel_talks = target_talks
    print(f"Wrote talks to {rel_talks} ({len(talks)} entries)")

    if not talks:
        print("Warning: no talks with transcripts were stored.")

    return {
        "playlist_id": resolved_playlist,
        "videos": exported_list,
        "talks": talks,
    }


__all__ = [
    "extract_video_id",
    "PlaylistDiscoveryError",
    "assemble_talk_entry",
    "fetch_and_store",
    "fetch_single_transcript",
    "fetch_video_meta",
    "find_playlist_id",
    "get_playlist_videos",
    "get_yt_initial_player_response",
    "split_title_and_speaker",
    "xml_to_paragraphs",
]
