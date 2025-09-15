YC AI Startup School — eBook

Overview
- Goal: compile YC’s AI Startup School talks into an English eBook, one chapter per speaker.
- This repo provides a simple, dependency-light workflow you can use offline to organize content and build outputs with Pandoc (optional).

Quick Start
- Put transcripts into `talks.json` (see `talks.sample.json`).
- Generate chapter Markdown files: `python3 scripts/ingest_json.py --input talks.json`.
- Concatenate into a single book Markdown: `python3 scripts/build_book.py`.
- Optional: build EPUB/PDF with Pandoc (examples below).

Auto-Fetch (recommended)
- Discover playlist and export video list (no transcripts yet):
  - `python3 scripts/fetch_yc_ai_startup_school.py --export-videos --out talks.json`
- Download subtitles with your own browser cookies using yt-dlp:
  - First, ensure `yt-dlp` is installed (I can install it for you) and you are logged in to YouTube in the chosen browser.
  - Example (Safari on macOS):
    - `python3 scripts/download_subs.py --videos-json build/videos.json --browser safari --out talks.json`
  - Supported values for `--browser`: `safari`, `chrome`, `edge`, `firefox`.
  - Alternatively, export cookies to a Netscape-format file (cookies.txt) and pass it directly:
    - `python3 scripts/download_subs.py --videos-json build/videos.json --cookies path/to/cookies.txt --out talks.json`
- Then build chapters and the book:
  - `python3 scripts/ingest_json.py --input talks.json`
  - `python3 scripts/build_book.py`

Option: Playwright Transcript Scraper (UI)
- If YouTube blocks timedtext/yt-dlp in your environment, use the transcript panel via Playwright:
  1) Install Playwright: `python3 -m pip install --user playwright`
  2) Prefer using your installed Chrome to avoid big downloads: the script uses `channel=chrome` by default.
  3) Provide `cookies.txt` exported from your browser (Netscape format) in repo root.
  4) Run a small test (headless):
     - `python3 scripts/fetch_transcripts_playwright.py --videos-json build/videos.json --cookies cookies.txt --out talks.json --limit 2 --headless`
     - If it fails, try headful mode to watch it click UI: `python3 scripts/fetch_transcripts_playwright.py --videos-json build/videos.json --cookies cookies.txt --out talks.json --limit 2 --show`
  5) Full run:
     - `python3 scripts/fetch_transcripts_playwright.py --videos-json build/videos.json --cookies cookies.txt --out talks.json --headless`
  6) Build:
     - `python3 scripts/ingest_json.py --input talks.json --overwrite`
     - `python3 scripts/build_book.py`

Repo Layout
- `content/` — one Markdown file per talk (chapters).
- `build/` — generated outputs (`book.md`, optional `.epub`/`.pdf`).
- `scripts/` — helpers to ingest structured data and build the book.
- `metadata.yaml` — book-level metadata (title, author, language, etc.).

Supplying Content
- Preferred: add talks to `talks.json` with fields: `speaker`, `title`, `source_url` (optional), `date` (optional), and `transcript` (string).
- If you want me to fetch talks automatically from YC/YouTube, please approve network access and provide either:
  - A list of URLs for the talks you want, or
  - Confirmation to use the official YC AI Startup School series (I’ll discover and pull all talks and transcripts, where available).

Build Commands
- Concatenate to `build/book.md`:
  - `python3 scripts/build_book.py`
- With Pandoc (if installed) to produce EPUB:
  - `pandoc --metadata-file=metadata.yaml -o build/yc-ai-startup-school.epub content/*.md`
- With Pandoc to produce PDF (requires a LaTeX engine, e.g. `tectonic`):
  - `pandoc --metadata-file=metadata.yaml -o build/yc-ai-startup-school.pdf content/*.md`

Notes
- No external Python packages are required; JSON is used instead of YAML for portability.
- File names are auto-numbered and slugified for stable chapter ordering.
- You can safely rerun the ingest script; pass `--overwrite` to replace existing chapter files.
 - If YouTube blocks automated transcript access, using `yt-dlp` with `--cookies-from-browser` is the most reliable way to fetch subtitles.
