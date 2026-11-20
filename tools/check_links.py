#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ruben Ferraro — Unrendered (https://github.com/mysterxn-ctrl/unrendered)
"""Check every relative link and anchor in the repository's Markdown files (GitHub slug rules)."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {".git", "node_modules"}


def md_files():
    for p in ROOT.rglob("*.md"):
        if not SKIP.intersection(p.relative_to(ROOT).parts):
            yield p


def strip_code(text: str) -> str:
    text = re.sub(r"^```.*?^```", "", text, flags=re.M | re.S)
    return re.sub(r"`[^`\n]*`", "", text)


def slugs(path: Path) -> set:
    out, seen = set(), {}
    for line in strip_code(path.read_text(encoding="utf-8")).splitlines():
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", line)
        if not m:
            continue
        title = re.sub(r"<[^>]+>|\[([^\]]*)\]\([^)]*\)", r"\1", m.group(2))
        s = re.sub(r"[^\w\- ]", "", title.strip().lower()).replace(" ", "-")
        n = seen.get(s, 0)
        out.add(s if n == 0 else f"{s}-{n}")
        seen[s] = n + 1
    # explicit anchors
    out |= set(re.findall(r'<a\s+(?:name|id)="([^"]+)"', path.read_text(encoding="utf-8")))
    return out


def main() -> int:
    errors = []
    for md in md_files():
        text = strip_code(md.read_text(encoding="utf-8"))
        targets = re.findall(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)", text)
        targets += re.findall(r'(?:href|src)="([^"]+)"', text)
        for t in targets:
            if re.match(r"^(https?:|mailto:|data:)", t):
                continue
            path, _, frag = t.partition("#")
            target = md if not path else (md.parent / path).resolve()
            if not target.exists():
                errors.append(f"{md.relative_to(ROOT)}: missing {t}")
            elif frag and target.suffix == ".md" and frag.lower() not in slugs(target):
                errors.append(f"{md.relative_to(ROOT)}: missing anchor {t}")
    for e in errors:
        print("BROKEN", e)
    print(f"checked {sum(1 for _ in md_files())} Markdown files: {len(errors)} problem(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
