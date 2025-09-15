#!/usr/bin/env python3
import os
import re
import argparse
from typing import List, Tuple


CONTENT_DIR = "content"


FILLER_PATTERNS = [
    r"\b(?:um+|uh+|er+|ah+)\b[,.!?]*",  # ums/uhs
    r"\b(?:you know|i mean|kind of|sort of)\b[\s,.-]*",
    r"\b(?:okay|ok|yeah|right)\b[\s,.-]*",
    # 'like' only when used as discourse marker with trailing comma/period or dash
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
    # Remove duplicated spaces created by deletions
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([,.;:!?])", r"\1", out)
    return out.strip()


def sentence_case_paragraph(p: str) -> str:
    # Normalize whitespace
    p = re.sub(r"\s+", " ", p).strip()
    if not p:
        return p
    # Capitalize sentence starts
    parts = re.split(r"([.!?]+)\s+", p)
    rebuilt: List[str] = []
    i = 0
    while i < len(parts):
        seg = parts[i]
        sep = parts[i+1] if i+1 < len(parts) else ""
        # Capitalize first alpha
        seg2 = list(seg)
        for j, ch in enumerate(seg2):
            if ch.isalpha():
                seg2[j] = ch.upper()
                break
        seg_fixed = "".join(seg2)
        # Pronoun 'i' capitalization
        seg_fixed = re.sub(r"\bi\b", "I", seg_fixed)
        for pat, repl in CONTRACTIONS:
            seg_fixed = re.sub(pat, repl, seg_fixed, flags=re.IGNORECASE)
        # Terms uppercasing
        for pat, repl in LOWER_TO_UPPER_TERMS:
            seg_fixed = re.sub(pat, repl, seg_fixed, flags=re.IGNORECASE)
        rebuilt.append(seg_fixed)
        if sep:
            rebuilt.append(sep + " ")
        i += 2
    out = "".join(rebuilt).strip()
    return out


def add_subheadings(paras: List[str]) -> List[str]:
    if len(paras) < 6:
        return paras
    headings = [
        "## Introduction",
        "## Key Ideas",
        "## Technical Insights",
        "## Applications",
        "## Conclusion",
    ]
    # Decide number of sections based on length
    sections = min(len(headings), max(2, min(5, len(paras) // 6)))
    heads = headings[:sections]
    # Compute cut points
    result: List[str] = []
    n = len(paras)
    for idx, h in enumerate(heads):
        start = (n * idx) // sections
        end = (n * (idx + 1)) // sections
        if idx == 0:
            result.append(h)
        else:
            result.append("")
            result.append(h)
        result.extend(paras[start:end])
    return result


def split_header_body(content: str) -> Tuple[List[str], List[str]]:
    lines = content.splitlines()
    header_lines: List[str] = []
    i = 0
    while i < len(lines):
        header_lines.append(lines[i])
        if i >= 1 and not lines[i].strip():
            # stop after the first blank line following meta block
            break
        # Stop header capture after encountering first non-meta paragraph
        if i >= 1 and not lines[i].startswith("-") and not lines[i].startswith("#"):
            # Insert a blank separator line for consistency
            header_lines.append("")
            break
        i += 1
    body = content.split("\n", len(header_lines))[-1]
    body = body.strip("\n")
    return header_lines, body.split("\n\n") if body else []


def process_file(path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    header, paras = split_header_body(content)
    if not paras:
        return
    # Clean + case corrections
    cleaned = []
    for p in paras:
        p2 = remove_filler(p)
        p3 = sentence_case_paragraph(p2)
        cleaned.append(p3)
    # Add subheadings
    with_heads = add_subheadings(cleaned)
    # Reassemble
    out = "\n".join(header).rstrip() + "\n\n" + "\n\n".join(with_heads).rstrip() + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)


def main():
    ap = argparse.ArgumentParser(description="Polish chapters: remove fillers, fix casing, and add subheadings")
    ap.add_argument("--file", default="", help="Process a single file (path in content/). If empty, process all chapters.")
    args = ap.parse_args()

    targets: List[str] = []
    if args.file:
        targets = [args.file if args.file.startswith(CONTENT_DIR + os.sep) else os.path.join(CONTENT_DIR, args.file)]
    else:
        for name in os.listdir(CONTENT_DIR):
            if not name.endswith('.md'):
                continue
            if name.startswith('000-introduction'):
                continue
            targets.append(os.path.join(CONTENT_DIR, name))
        targets.sort()

    for path in targets:
        process_file(path)
        print(f"Polished: {path}")


if __name__ == "__main__":
    main()

