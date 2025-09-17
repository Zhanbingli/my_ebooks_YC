"""Command line interface for managing ebook pipelines."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

from . import PROJECT_ROOT
from .build import build_book
from .config import Config, load_config
from .enrich import enrich_talks
from .ingest import ingest_file
from .paths import SeriesPaths
from .polish import polish_series
from .subtitles import download_subtitles
from .youtube import PlaylistDiscoveryError, fetch_and_store


def parse_languages(value: str) -> List[str]:
    langs = [item.strip() for item in value.split(",") if item.strip()]
    return langs or ["en"]


def resolve_paths(cfg: Config, slug: str) -> SeriesPaths:
    series = cfg.get(slug)
    return series.to_paths()


def cmd_list(cfg: Config, _args: argparse.Namespace) -> None:
    print("Available series:")
    for series in cfg.list_series():
        paths = series.to_paths()
        print(f"- {series.slug}: {series.title}")
        print(f"    data: {paths.data_dir.relative_to(PROJECT_ROOT)}")
        print(f"    content: {paths.content_dir.relative_to(PROJECT_ROOT)}")
        print(f"    build: {paths.build_dir.relative_to(PROJECT_ROOT)}")


def cmd_fetch(cfg: Config, args: argparse.Namespace) -> None:
    series = cfg.get(args.series)
    paths = series.to_paths()
    languages = parse_languages(args.langs)
    playlist_id = args.playlist_id or (series.youtube or {}).get("playlist_id")
    query = args.query or (series.youtube or {}).get("playlist_query") or series.title
    try:
        fetch_and_store(
            paths,
            languages=languages,
            playlist_id=playlist_id,
            query=query,
            limit=args.limit,
            export_videos=not args.skip_video_export,
            series_title=series.title,
        )
    except PlaylistDiscoveryError as exc:
        raise SystemExit(str(exc))


def cmd_subtitles(cfg: Config, args: argparse.Namespace) -> None:
    paths = resolve_paths(cfg, args.series)
    videos_path = Path(args.videos_json) if args.videos_json else None
    cookies_path = Path(args.cookies) if args.cookies else None
    out_path = Path(args.out) if args.out else None
    download_subtitles(
        paths,
        videos_path=videos_path,
        cookies=cookies_path,
        browser=args.browser,
        limit=args.limit,
        export_talks_path=out_path,
    )


def cmd_ingest(cfg: Config, args: argparse.Namespace) -> None:
    paths = resolve_paths(cfg, args.series)
    input_path = Path(args.input) if args.input else paths.talks_path
    ingest_file(paths, input_path, start_index=args.start_index, overwrite=args.overwrite)


def cmd_enrich(cfg: Config, args: argparse.Namespace) -> None:
    paths = resolve_paths(cfg, args.series)
    input_path = Path(args.input) if args.input else paths.talks_path
    output_path = Path(args.out) if args.out else None
    cookies_path = Path(args.cookies) if args.cookies else None
    changed = enrich_talks(
        paths,
        input_path=input_path,
        output_path=output_path,
        use_yt_dlp=args.use_yt_dlp,
        cookies=cookies_path,
        browser=args.browser,
    )
    target = output_path or input_path
    if changed:
        print(f"Updated talks: {changed} change(s) written to {target}")
    else:
        print("No changes required (transcripts clean and metadata present).")


def cmd_polish(cfg: Config, args: argparse.Namespace) -> None:
    paths = resolve_paths(cfg, args.series)
    file_path = Path(args.file) if args.file else None
    polish_series(paths, file=file_path)


def cmd_build(cfg: Config, args: argparse.Namespace) -> None:
    series = cfg.get(args.series)
    paths = series.to_paths()
    metadata_path: Optional[Path]
    if args.metadata:
        md_path = Path(args.metadata)
        if not md_path.is_absolute():
            md_path = (PROJECT_ROOT / args.metadata).resolve()
        metadata_path = md_path
    else:
        metadata_path = paths.metadata_path
    build_book(paths, metadata_path=metadata_path)


def cmd_update(cfg: Config, args: argparse.Namespace) -> None:
    series = cfg.get(args.series)
    paths = series.to_paths()
    languages = parse_languages(args.langs)
    playlist_id = args.playlist_id or (series.youtube or {}).get("playlist_id")
    query = args.query or (series.youtube or {}).get("playlist_query") or series.title

    if not args.skip_fetch:
        try:
            fetch_and_store(
                paths,
                languages=languages,
                playlist_id=playlist_id,
                query=query,
                limit=args.limit,
                export_videos=not args.skip_video_export,
                series_title=series.title,
            )
        except PlaylistDiscoveryError as exc:
            raise SystemExit(str(exc))

    talks_source = paths.talks_path

    if args.with_subtitles:
        download_subtitles(
            paths,
            cookies=Path(args.cookies) if args.cookies else None,
            browser=args.browser,
            limit=args.limit,
        )

    if args.use_yt_dlp:
        enrich_talks(
            paths,
            input_path=talks_source,
            use_yt_dlp=True,
            cookies=Path(args.cookies) if args.cookies else None,
            browser=args.browser,
        )

    ingest_file(
        paths,
        talks_source,
        start_index=args.start_index,
        overwrite=True,
    )

    if not args.skip_polish:
        polish_series(paths)

    if not args.skip_build:
        metadata_path = paths.metadata_path
        build_book(paths, metadata_path=metadata_path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage eBook generation from YouTube content.")
    sub = parser.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("list", help="List configured series")
    sp.set_defaults(func=cmd_list)

    sp = sub.add_parser("fetch", help="Fetch playlist metadata and transcripts")
    sp.add_argument("--series", default="yc-ai-startup-school")
    sp.add_argument("--playlist-id", default="")
    sp.add_argument("--query", default="")
    sp.add_argument("--langs", default="en,en-US,en-GB")
    sp.add_argument("--limit", type=int, default=0)
    sp.add_argument("--skip-video-export", action="store_true")
    sp.set_defaults(func=cmd_fetch)

    sp = sub.add_parser("subtitles", help="Download subtitles via yt-dlp")
    sp.add_argument("--series", default="yc-ai-startup-school")
    sp.add_argument("--videos-json", default="")
    sp.add_argument("--browser", default="")
    sp.add_argument("--cookies", default="")
    sp.add_argument("--limit", type=int, default=0)
    sp.add_argument("--out", default="")
    sp.set_defaults(func=cmd_subtitles)

    sp = sub.add_parser("ingest", help="Convert talks.json into Markdown chapters")
    sp.add_argument("--series", default="yc-ai-startup-school")
    sp.add_argument("--input", default="")
    sp.add_argument("--start-index", type=int, default=1)
    sp.add_argument("--overwrite", action="store_true")
    sp.set_defaults(func=cmd_ingest)

    sp = sub.add_parser("enrich", help="Clean transcripts and enrich metadata")
    sp.add_argument("--series", default="yc-ai-startup-school")
    sp.add_argument("--input", default="")
    sp.add_argument("--out", default="")
    sp.add_argument("--use-yt-dlp", action="store_true")
    sp.add_argument("--cookies", default="")
    sp.add_argument("--browser", default="")
    sp.set_defaults(func=cmd_enrich)

    sp = sub.add_parser("polish", help="Polish chapter Markdown files")
    sp.add_argument("--series", default="yc-ai-startup-school")
    sp.add_argument("--file", default="")
    sp.set_defaults(func=cmd_polish)

    sp = sub.add_parser("build", help="Assemble chapters into build/book.md")
    sp.add_argument("--series", default="yc-ai-startup-school")
    sp.add_argument("--metadata", default="")
    sp.set_defaults(func=cmd_build)

    sp = sub.add_parser("update", help="Run the end-to-end update pipeline")
    sp.add_argument("--series", default="yc-ai-startup-school")
    sp.add_argument("--playlist-id", default="")
    sp.add_argument("--query", default="")
    sp.add_argument("--langs", default="en,en-US,en-GB")
    sp.add_argument("--limit", type=int, default=0)
    sp.add_argument("--skip-fetch", action="store_true")
    sp.add_argument("--skip-video-export", action="store_true")
    sp.add_argument("--with-subtitles", action="store_true")
    sp.add_argument("--cookies", default="")
    sp.add_argument("--browser", default="")
    sp.add_argument("--use-yt-dlp", action="store_true")
    sp.add_argument("--start-index", type=int, default=1)
    sp.add_argument("--skip-polish", action="store_true")
    sp.add_argument("--skip-build", action="store_true")
    sp.set_defaults(func=cmd_update)

    return parser


def main(argv: Optional[List[str]] = None) -> None:
    cfg = load_config()
    parser = build_parser()
    args = parser.parse_args(argv)
    func = getattr(args, "func")
    func(cfg, args)


if __name__ == "__main__":
    main()
