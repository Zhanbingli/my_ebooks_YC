#!/usr/bin/env python3
import os
import sys
from datetime import datetime


CONTENT_DIR = "content"
BUILD_DIR = "build"


def list_markdown_files(path: str):
    files = [f for f in os.listdir(path) if f.lower().endswith('.md')]
    files.sort()  # relies on numeric prefixes like 01-, 02-
    return [os.path.join(path, f) for f in files]


def read_file(path: str) -> str:
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().rstrip() + "\n\n"


def ensure_dirs():
    os.makedirs(BUILD_DIR, exist_ok=True)


def build_title_page() -> str:
    # Lightweight title page; Pandoc can replace with metadata if used.
    title = "YC AI Startup School"
    subtitle = "Talks compiled into an eBook"
    author = "Y Combinator — Speakers"
    date = datetime.now().strftime("%Y-%m-%d")
    parts = [
        f"# {title}",
        f"\n_{subtitle}_\n",
        f"\n{author}\n",
        f"\n{date}\n",
        "\n---\n\n",
    ]
    return "\n".join(parts)


def build_book_md(files):
    parts = [build_title_page()]
    for path in files:
        parts.append(read_file(path))
    return "".join(parts)


def write_output(content: str, out_path: str):
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(content)


def main():
    ensure_dirs()
    if not os.path.isdir(CONTENT_DIR):
        print(f"Missing '{CONTENT_DIR}' directory. Nothing to build.", file=sys.stderr)
        sys.exit(1)

    files = list_markdown_files(CONTENT_DIR)
    if not files:
        print("No chapter files found in 'content/'.", file=sys.stderr)
        sys.exit(1)

    book_md = build_book_md(files)
    out_md = os.path.join(BUILD_DIR, "book.md")
    write_output(book_md, out_md)
    print(f"Built: {out_md}")


if __name__ == "__main__":
    main()

