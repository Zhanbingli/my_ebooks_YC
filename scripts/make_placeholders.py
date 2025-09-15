#!/usr/bin/env python3
import json
import os
import sys
from typing import Dict, Any, List
sys.path.append(os.path.join(os.path.dirname(__file__)))
from fetch_yc_ai_startup_school import split_title_and_speaker  # type: ignore

def main():
    src = 'build/videos.json'
    out = 'talks.json'
    if not os.path.exists(src):
        print(f"Missing {src}. Run fetch_yc_ai_startup_school.py --export-videos first.", file=sys.stderr)
        sys.exit(1)
    with open(src, 'r', encoding='utf-8') as f:
        vdata = json.load(f)
    talks: List[Dict[str, Any]] = []
    for v in vdata.get('videos', []):
        title = v.get('title') or 'Untitled'
        url = v.get('url') or ''
        talk_title, speaker = split_title_and_speaker(title)
        transcript = (
            f"This chapter is a placeholder for the full transcript.\n\n"
            f"Source video: {url}\n\n"
            f"Once subtitles are fetched (see README), this will be replaced by the full talk text."
        )
        talks.append({
            'speaker': speaker or 'Unknown Speaker',
            'title': talk_title or title,
            'date': '',
            'source_url': url,
            'transcript': transcript,
        })
    data = {'series': 'YC AI Startup School', 'talks': talks}
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Wrote placeholders to {out} ({len(talks)} talks)")

if __name__ == '__main__':
    main()
