"""Chapter polishing helpers for light language cleanup."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .paths import SeriesPaths

FILLER_PATTERNS = [
    r"\b(?:um+|uh+|er+|ah+)\b[,.!?]*",
    r"\b(?:you know|i mean|kind of|sort of)\b[\s,.-]*",
    r"\b(?:okay|ok|yeah|right)\b[\s,.-]*",
    r"\blike\b(?=\s*[,.\-])",
]

LOWER_TO_UPPER_TERMS = [
    (r"\byc\b", "YC"),
    (r"\bai\b", "AI"),
]

CONTRACTIONS = [
    (r"\bi'm\b", "I'm"),
    (r"\bi've\b", "I've"),
    (r"\bi'll\b", "I'll"),
    (r"\bi'd\b", "I'd"),
]


def remove_filler(text: str) -> str:
    out = text
    for pat in FILLER_PATTERNS:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([,.;:!?])", r"\1", out)
    return out.strip()


def sentence_case_paragraph(paragraph: str) -> str:
    paragraph = re.sub(r"\s+", " ", paragraph).strip()
    if not paragraph:
        return paragraph
    parts = re.split(r"([.!?]+)\s+", paragraph)
    rebuilt: List[str] = []
    idx = 0
    while idx < len(parts):
        seg = parts[idx]
        sep = parts[idx + 1] if idx + 1 < len(parts) else ""
        seg_chars = list(seg)
        for pos, ch in enumerate(seg_chars):
            if ch.isalpha():
                seg_chars[pos] = ch.upper()
                break
        seg_fixed = "".join(seg_chars)
        seg_fixed = re.sub(r"\bi\b", "I", seg_fixed)
        for pat, repl in CONTRACTIONS:
            seg_fixed = re.sub(pat, repl, seg_fixed, flags=re.IGNORECASE)
        for pat, repl in LOWER_TO_UPPER_TERMS:
            seg_fixed = re.sub(pat, repl, seg_fixed, flags=re.IGNORECASE)
        rebuilt.append(seg_fixed)
        if sep:
            rebuilt.append(sep + " ")
        idx += 2
    return "".join(rebuilt).strip()


def add_subheadings(paragraphs: List[str]) -> List[str]:
    if len(paragraphs) < 6:
        return paragraphs
    headings = [
        "## Introduction",
        "## Key Ideas",
        "## Technical Insights",
        "## Applications",
        "## Conclusion",
    ]
    sections = min(len(headings), max(2, min(5, len(paragraphs) // 6)))
    heads = headings[:sections]
    result: List[str] = []
    total = len(paragraphs)
    for idx, heading in enumerate(heads):
        start = (total * idx) // sections
        end = (total * (idx + 1)) // sections
        if idx == 0:
            result.append(heading)
        else:
            result.append("")
            result.append(heading)
        result.extend(paragraphs[start:end])
    return result


def split_header_body(content: str) -> Tuple[List[str], List[str]]:
    lines = content.splitlines()
    header_lines: List[str] = []
    idx = 0
    while idx < len(lines):
        header_lines.append(lines[idx])
        if idx >= 1 and not lines[idx].strip():
            break
        if idx >= 1 and not lines[idx].startswith("-") and not lines[idx].startswith("#"):
            header_lines.append("")
            break
        idx += 1
    body = content.split("\n", len(header_lines))[-1]
    body = body.strip("\n")
    return header_lines, body.split("\n\n") if body else []


def polish_file(path: Path) -> None:
    content = path.read_text(encoding="utf-8")
    header, paragraphs = split_header_body(content)
    if not paragraphs:
        return
    cleaned = [sentence_case_paragraph(remove_filler(p)) for p in paragraphs]
    with_heads = add_subheadings(cleaned)
    out = "\n".join(header).rstrip() + "\n\n" + "\n\n".join(with_heads).rstrip() + "\n"
    path.write_text(out, encoding="utf-8")


def iter_chapters(paths: SeriesPaths) -> Iterable[Path]:
    for path in sorted(paths.content_dir.glob("*.md")):
        if path.name.startswith("000-introduction"):
            continue
        yield path


def polish_series(paths: SeriesPaths, file: Optional[Path] = None) -> List[Path]:
    targets: List[Path]
    if file:
        targets = [file if file.is_absolute() else paths.content_dir / file]
    else:
        targets = list(iter_chapters(paths))
    updated: List[Path] = []
    for path in targets:
        polish_file(path)
        updated.append(path)
        print(f"Polished: {path}")
    return updated


__all__ = ["polish_series", "polish_file"]
