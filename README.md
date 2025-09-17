YC AI Startup School — eBook Toolkit

Overview
- Offline-first tooling to turn YouTube talks into a polished eBook.
- Supports multiple series via `config/series.json`; default slug: `yc-ai-startup-school`.
- Unified CLI (`my-ebook` or `python -m ebook_pipeline.cli`) orchestrates discovery, subtitle fetching, ingestion, polishing, and book assembly.

Project Layout
- `config/series.json` — catalogue of series and metadata paths.
- `data/<slug>/` — raw assets (`videos.json`, `talks.json`, `subs/`).
- `content/<slug>/` — Markdown chapters (generated).
- `build/<slug>/` — compiled manuscripts (`book.md`, export targets).
- `metadata/<slug>.yaml` — key/value pairs for title page defaults.
- `src/ebook_pipeline/` — reusable Python package powering the toolkit.

Quick Start (fresh repo)
1. Ensure Python 3.9+ is available. Optional: install the CLI entry point:
   - `python3 -m pip install --user -e .`
   - or run via module: `python3 -m ebook_pipeline.cli --help`
2. Inspect configured series:
   - `my-ebook list`
3. Run the end-to-end pipeline:
   - `my-ebook update`
   - Adds/refreshes `data/yc-ai-startup-school/talks.json`, regenerates Markdown under `content/yc-ai-startup-school/`, and builds `build/yc-ai-startup-school/book.md`.

CLI Highlights
- `my-ebook fetch` — discover playlist + fetch transcripts (falls back to YouTube APIs).
- `my-ebook subtitles` — download `.vtt` subs via yt-dlp (requires logged-in browser or cookies).
- `my-ebook enrich` — clean transcripts and optionally ask yt-dlp for missing dates.
- `my-ebook ingest` — turn `talks.json` into numbered chapter Markdown.
- `my-ebook polish` — tidy filler language, casing, headings.
- `my-ebook build` — concatenate chapters into `build/<slug>/book.md`.
- `my-ebook update` — orchestrated pipeline with flags for skipping/focusing steps (`--with-subtitles`, `--use-yt-dlp`, `--skip-polish`, etc.).

Working With YouTube Resources
- Default discovery targets `YC AI Startup School`; override with `--playlist-id` or `--query` per command.
- Subtitle options:
  - `my-ebook subtitles --browser chrome` (uses yt-dlp `--cookies-from-browser`).
  - `my-ebook subtitles --cookies path/to/cookies.txt` (Netscape export).
- Playwright fallback: `scripts/fetch_transcripts_playwright.py --series yc-ai-startup-school --show` for hostile environments.

Manual Scripts (still available)
- Legacy scripts under `scripts/` now proxy to the shared package for users who rely on previous commands (e.g. `python3 scripts/ingest_json.py --series yc-ai-startup-school`).
- Each accepts a `--series` flag so content for new playlists can live alongside existing material.

Customize or Add New Series
1. Duplicate the entry in `config/series.json` with a new slug and metadata path.
2. Place series-specific metadata in `metadata/<new-slug>.yaml` (simple key:value lines).
3. Run `my-ebook update --series <new-slug> --query "Your Playlist"` and follow the usual workflow.

Pandoc Exports (optional)
- EPUB: `pandoc --metadata-file=metadata/yc-ai-startup-school.yaml -o build/yc-ai-startup-school/yc-ai-startup-school.epub content/yc-ai-startup-school/*.md`
- PDF (LaTeX): `pandoc --metadata-file=metadata/yc-ai-startup-school.yaml -o build/yc-ai-startup-school/yc-ai-startup-school.pdf content/yc-ai-startup-school/*.md`

Troubleshooting
- Missing transcripts: try `--with-subtitles --browser chrome` or Playwright fallback.
- yt-dlp not found: install via `python3 -m pip install yt-dlp` or set `YTDLP=/path/to/yt-dlp`.
- Cookies: export Safari/Chrome cookies (`cookies.txt`) to bypass YouTube authentication checks.

中文提示
- 全流程可一键执行：`my-ebook update --with-subtitles --browser chrome --use-yt-dlp`。
- 多系列并存：在 `config/series.json` 中新增条目，即可独立维护不同主题的资源与章节。
- 如果被 YouTube 限制，可改用 `scripts/fetch_transcripts_playwright.py --show`，以浏览器界面方式抓取字幕。
