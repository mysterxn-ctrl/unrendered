#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ruben Ferraro — Unrendered (https://github.com/mysterxn-ctrl/unrendered)
"""Regenerate the "Today's pick" table in README.md from the bundled model registry.

  python3 tools/update_readme.py           rewrite the block between the markers
  python3 tools/update_readme.py --check   exit 1 if the README is out of date (used in CI)
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "unrendered"
os.environ["UNRENDERED_HOME"] = str(SKILL)  # bundled data only, never local state
sys.path.insert(0, str(SKILL / "scripts"))
import model_select as ms  # noqa: E402

START, END = "<!-- unrendered:model-table:start -->", "<!-- unrendered:model-table:end -->"
TRACK_NAMES = {"generate": ("Generation", "text-to-image"), "edit": ("Editing", "image-editing")}


def display(reg, model_id):
    m = next((x for x in reg["models"] if x["id"] == model_id), None)
    return (m.get("aliases") or [model_id])[0] if m else model_id


def fmt(row):
    ci = f" ± {row['ci']:.0f}" if row.get("ci") is not None else ""
    return f"{row['elo']:.0f}{ci}"


def build_table() -> str:
    reg, _ = ms.load_registry()
    snaps = ms.load_snapshots()
    lines = ["| Track | Selected model | Why |", "|---|---|---|"]
    for track in ms.TRACKS:
        name, board_name = TRACK_NAMES[track]
        sel_id = reg["selected"][track]
        board = ms.pick_board(snaps, track, "primary")
        why = "Default starting point"
        if board:
            rows = ms.merge_configs(board["rows"])
            top = rows[0]
            sel = next((r for r in rows if (ms.find_model(reg, r["name"]) or {}).get("id") == sel_id), None)
            if sel is top:
                runner = rows[1] if len(rows) > 1 else None
                why = f"#1 on the Artificial Analysis {board_name} arena — {fmt(top)}"
                if runner:
                    why += f" vs. {fmt(runner)} for #2"
            elif sel:
                margin = top["elo"] - sel["elo"]
                ci = (top.get("ci") or 0) + (sel.get("ci") or 0)
                why = (f"{display(reg, ms.find_model(reg, top['name'])['id'])} leads the {board_name} arena by "
                       f"{margin:.0f} Elo — inside the combined CI of {ci:.0f}, so the current choice stays")
        lines.append(f"| {name} | **{display(reg, sel_id)}** | {why} |")
    checked = reg.get("last_checked", "")
    import datetime as dt
    d = dt.date.fromisoformat(checked)
    lines += ["", f"Leaderboard data as of {d.day} {d.strftime('%B')} {d.year}."]
    return "\n".join(lines)


def main() -> int:
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("markers not found in README.md")
        return 1
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    new = f"{head}{START}\n{build_table()}\n{END}{tail}"
    if "--check" in sys.argv:
        if new != text:
            print("README model table is out of date — run: python3 tools/update_readme.py")
            return 1
        print("README model table is up to date")
        return 0
    readme.write_text(new, encoding="utf-8")
    print("README model table updated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
