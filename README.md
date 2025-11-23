YC AI Startup School — eBook Toolkit

Overview
- Offline-first toolkit that turns YouTube talks into a polished eBook.
- Installable CLI (`my-ebook` / `python -m ebook_pipeline`) with an end-to-end pipeline.
- Bootstrap new series with `my-ebook init`, manage multiple series via `config/series.json`.
- Works in-repo or anywhere else; point the tools with `EBOOK_PIPELINE_HOME` or `--config`.

Install
1) Python 3.9+ available.
2) From the repo root: `python3 -m pip install --user -e .`
   - Playwright helper: `python3 -m pip install --user -e .[playwright]`
   - Dev tools: `python3 -m pip install --user -e .[dev]`
3) Verify: `my-ebook --help`

Configuration Root
- Default root is the closest folder containing `config/series.json` (usually this repo).
- Override with `EBOOK_PIPELINE_HOME=/path/to/workdir` or by passing `--config /path/to/series.json` to any command.

Project Layout
- `config/series.json` — catalogue of series and metadata locations.
- `data/<slug>/` — raw assets (`videos.json`, `talks.json`, `subs/`).
- `content/<slug>/` — Markdown chapters (generated).
- `build/<slug>/` — compiled manuscripts (`book.md`, export targets).
- `metadata/<slug>.yaml` — title-page defaults used during build.
- `src/ebook_pipeline/` — reusable Python package powering the toolkit.

Bootstrap a Series
1) Create config + folders:  
   `my-ebook init --series my-series --title "My Talks" --playlist-id <YT_PLAYLIST> --with-intro`
2) The command writes/updates `config/series.json`, creates metadata YAML, and prepares `data/`, `content/`, and `build/` for the slug.
3) Adjust metadata in `metadata/<slug>.yaml` and replace the auto-introduction if desired.

Quick Start (existing YC series)
1) Inspect configured series: `my-ebook list`
2) Run the pipeline:  
   `my-ebook update --series yc-ai-startup-school --with-subtitles --browser chrome --use-yt-dlp`  
   Flags: `--skip-fetch`, `--skip-polish`, `--skip-build`, `--limit N`, `--langs en,en-US,en-GB`

CLI Highlights
- `--config` — point at an alternate `series.json`.
- `init` — bootstrap a new series entry plus folders.
- `fetch` — discover playlist + fetch transcripts (fallbacks to YouTube page parsing).
- `subtitles` — download `.vtt` subtitles via yt-dlp (cookies or browser-based auth).
- `enrich` — clean transcripts and optionally ask yt-dlp for missing dates/URLs.
- `ingest` — convert `talks.json` into numbered chapter Markdown.
- `polish` — tidy filler language, casing, headings.
- `build` — concatenate chapters into `build/<slug>/book.md`.
- `update` — orchestrated pipeline; accepts the same flags as the individual steps.

Working With YouTube Resources
- Override defaults with `--playlist-id` or `--query` on fetch/update.
- Subtitle options:
  - `my-ebook subtitles --browser chrome` (uses yt-dlp `--cookies-from-browser`).
  - `my-ebook subtitles --cookies path/to/cookies.txt` (Netscape export).
- Playwright fallback: `scripts/fetch_transcripts_playwright.py --series <slug> --show`.

Manual Scripts (legacy)
- Legacy scripts under `scripts/` proxy to the shared package for users who rely on previous commands (e.g., `python3 scripts/ingest_json.py --series yc-ai-startup-school`).
- Each accepts a `--series` flag so content for new playlists can live alongside existing material.

Pandoc Exports (optional)
- EPUB: `pandoc --metadata-file=metadata/yc-ai-startup-school.yaml -o build/yc-ai-startup-school/yc-ai-startup-school.epub content/yc-ai-startup-school/*.md`
- PDF (LaTeX): `pandoc --metadata-file=metadata/yc-ai-startup-school.yaml -o build/yc-ai-startup-school/yc-ai-startup-school.pdf content/yc-ai-startup-school/*.md`

Troubleshooting
- Missing transcripts: try `--with-subtitles --browser chrome` or Playwright fallback.
- yt-dlp not found: install via `python3 -m pip install yt-dlp` or set `YTDLP=/path/to/yt-dlp`.
- Cookies: export Safari/Chrome cookies (`cookies.txt`) to bypass YouTube authentication checks.

中文提示
- 新建系列可用：`my-ebook init --series my-series --title "我的课程" --playlist-id <ID> --with-intro`
- 全流程一键执行：`my-ebook update --series yc-ai-startup-school --with-subtitles --browser chrome --use-yt-dlp`。
- 如被 YouTube 限制，可改用 `scripts/fetch_transcripts_playwright.py --show`。
