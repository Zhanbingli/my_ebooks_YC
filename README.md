YC AI Startup School — eBook Toolkit

What it does
- Fetch YouTube playlist videos, grab transcripts (or subtitles), and clean them.
- Convert talks into numbered Markdown chapters and build a single `book.md`.
- One-shot CLI pipeline: `my-ebook update --series yc-ai-startup-school --with-subtitles --browser chrome --use-yt-dlp`.
- Web UI: `my-ebook-web --host 0.0.0.0 --port 8000` lets you paste a video link and download its transcript; Docker: `docker build -t ebook-web . && docker run -p 8000:8000 ebook-web`.

Key commands
- `my-ebook init --series <slug> --title "Title" --playlist-id <ID> --with-intro`
- `my-ebook doctor --series <slug>` quick health check.
- `my-ebook update --series <slug> [...]` end-to-end fetch → ingest → polish → build.
- `my-ebook-web` minimal UI for a single video transcript.

中文速览
- 一键跑通：`my-ebook update --series yc-ai-startup-school --with-subtitles --browser chrome --use-yt-dlp`
- 简单网页端：`my-ebook-web --host 0.0.0.0 --port 8000`（或用 Docker）粘贴视频链接即可下载字幕。
