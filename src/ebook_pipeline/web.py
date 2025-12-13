"""Tiny Flask UI: paste a YouTube link, get a transcript to copy or download."""

from __future__ import annotations

import argparse
from urllib.parse import quote

from flask import Flask, render_template_string, request

from .youtube import fetch_single_transcript

DEFAULT_LANGS = "en,en-US,en-GB"

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Transcript Fetcher</title>
  <style>
    :root { color-scheme: light; font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; padding: 24px; background: radial-gradient(circle at 10% 20%, #f4f7ff 0, #f4f7ff 40%, #fff 100%); color: #111; }
    .card { max-width: 900px; margin: 0 auto; background: #fff; border-radius: 14px; box-shadow: 0 12px 40px rgba(0,0,0,0.08); padding: 28px; }
    h1 { margin-top: 0; }
    label { display: block; font-weight: 600; margin: 10px 0 6px; }
    input[type="text"] { width: 100%; padding: 12px; border: 1px solid #d4d8e1; border-radius: 10px; font-size: 15px; }
    input[type="text"]:focus { outline: 2px solid #4c7df0; border-color: #4c7df0; }
    .row { display: flex; gap: 12px; align-items: center; }
    button { background: linear-gradient(120deg, #4c7df0, #8f67ff); color: #fff; border: none; padding: 12px 18px; border-radius: 10px; font-size: 15px; cursor: pointer; }
    button:hover { filter: brightness(1.05); }
    .pill { display: inline-block; padding: 8px 12px; border-radius: 999px; background: #eef2ff; color: #31416b; font-size: 13px; }
    .error { color: #c62828; font-weight: 600; margin: 12px 0; }
    .result { margin-top: 18px; background: #f8fafc; border: 1px solid #e4e8f0; border-radius: 12px; padding: 16px; }
    textarea { width: 100%; min-height: 320px; border: 1px solid #d4d8e1; border-radius: 12px; padding: 12px; font-size: 14px; font-family: "SFMono-Regular", ui-monospace, Menlo, Consolas, monospace; }
    .meta { font-size: 14px; color: #445; margin-bottom: 8px; display: flex; gap: 12px; flex-wrap: wrap; }
    .actions { display: flex; gap: 12px; align-items: center; margin: 12px 0; }
    a.download { text-decoration: none; padding: 10px 14px; border-radius: 10px; background: #111; color: #fff; font-weight: 600; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Download YouTube Transcript</h1>
    <p>Paste a video URL, click fetch, then copy or download the transcript.</p>
    <form method="post">
      <label for="video_url">YouTube URL</label>
      <input id="video_url" type="text" name="video_url" placeholder="https://www.youtube.com/watch?v=..." value="{{ video_url|default('') }}" required>
      <div class="row">
        <div style="flex:1">
          <label for="langs">Languages (fallback list)</label>
          <input id="langs" type="text" name="langs" value="{{ langs or default_langs }}" placeholder="en,en-US,en-GB">
        </div>
        <div style="align-self:flex-end">
          <button type="submit">Fetch Transcript</button>
        </div>
      </div>
    </form>
    {% if error %}
      <div class="error">{{ error }}</div>
    {% endif %}
    {% if transcript %}
      <div class="result">
        <div class="meta">
          <span class="pill">Title: {{ title }}</span>
          <span class="pill">Speaker: {{ speaker }}</span>
          {% if date %}<span class="pill">Date: {{ date }}</span>{% endif %}
        </div>
        <div class="actions">
          <a class="download" href="{{ download_href }}" download="{{ video_id }}.txt">Download .txt</a>
          <span class="pill">{{ transcript.split()|length }} words</span>
        </div>
        <textarea readonly>{{ transcript }}</textarea>
      </div>
    {% endif %}
  </div>
</body>
</html>
"""


def _parse_langs(value: str) -> list[str]:
    langs = [item.strip() for item in (value or "").split(",") if item.strip()]
    return langs or DEFAULT_LANGS.split(",")


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index():
        context = {
            "video_url": "",
            "langs": DEFAULT_LANGS,
            "default_langs": DEFAULT_LANGS,
            "error": "",
            "title": "",
            "speaker": "",
            "date": "",
            "transcript": "",
            "video_id": "",
            "download_href": "",
        }
        if request.method == "POST":
            video_url = request.form.get("video_url", "").strip()
            langs_raw = request.form.get("langs", DEFAULT_LANGS)
            context["video_url"] = video_url
            context["langs"] = langs_raw
            try:
                result = fetch_single_transcript(video_url, _parse_langs(langs_raw))
            except ValueError as exc:
                context["error"] = str(exc)
            except Exception as exc:  # pragma: no cover - UI fallback
                context["error"] = f"抓取失败：{exc}"
            else:
                if not result:
                    context["error"] = "未找到可用字幕（可能需要登录或该视频未提供字幕）。"
                else:
                    context.update(
                        {
                            "title": result.get("title") or result.get("raw_title") or "Untitled",
                            "speaker": result.get("speaker") or "Unknown Speaker",
                            "date": result.get("date") or "",
                            "transcript": result.get("transcript") or "",
                            "video_id": result.get("video_id") or "",
                            "download_href": "data:text/plain;charset=utf-8,"
                            + quote((result.get("transcript") or "")),
                        }
                    )
        return render_template_string(PAGE, **context)

    return app


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Launch a minimal UI to download YouTube transcripts.")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000).")
    parser.add_argument("--debug", action="store_true", help="Enable Flask debug mode.")
    args = parser.parse_args(argv)

    app = create_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
