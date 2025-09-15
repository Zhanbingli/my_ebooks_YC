#!/usr/bin/env python3
import sys
from youtube_transcript_api import YouTubeTranscriptApi

def main():
    vid = sys.argv[1] if len(sys.argv) > 1 else 'LCEmiRjPEtQ'
    try:
        tr = YouTubeTranscriptApi.get_transcript(vid, languages=['en'])
        print(f"OK {vid} => {len(tr)} segments")
    except Exception as e:
        print(f"ERR {vid} => {e}")

if __name__ == '__main__':
    main()

