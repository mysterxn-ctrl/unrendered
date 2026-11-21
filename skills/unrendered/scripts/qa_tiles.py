#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ruben Ferraro — Unrendered (https://github.com/mysterxn-ctrl/unrendered)
"""Cut images into overlapping, enlarged tiles so every region can be inspected at full detail.

  qa_tiles.py IMG [IMG ...] -o OUT_DIR [--tile 640] [--zoom 2] [--overlap 0.15]

Vision models usually see a whole image downscaled, which hides wrong fingers, a third arm at the frame
edge or garbled small text. This writes, per image:
  <name>_full.jpg      the whole frame (long edge 1568 px) for composition, anatomy count and light
  <name>_rRcC.jpg      tiles covering the full frame edge to edge, enlarged by --zoom, each labelled
                       with its position, so nothing is only seen in the corner of a downscaled view
and prints a JSON list of the files to open, in reading order. Requires Pillow (pip install pillow).
"""
import argparse
import json
import math
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError:
    sys.exit("needs: pip install pillow")

FULL_EDGE = 1568
LABEL_H = 30
ROWS = {1: ["middle"], 2: ["top", "bottom"], 3: ["top", "middle", "bottom"]}
COLS = {1: ["centre"], 2: ["left", "right"], 3: ["left", "centre", "right"]}


def spans(length: int, count: int, overlap: float):
    """Start/end of `count` windows that cover 0..length with the given overlap."""
    if count == 1:
        return [(0, length)]
    size = math.ceil(length / (count - (count - 1) * overlap))
    step = (length - size) / (count - 1)
    return [(round(i * step), round(i * step) + size) for i in range(count)]


def place(names: dict, i: int, n: int) -> str:
    return names[n][i] if n in names else f"{i + 1}/{n}"


def tiles_for(path: Path, out: Path, tile: int, zoom: float, overlap: float):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    w, h = im.size
    files = []

    full = im.copy()
    full.thumbnail((FULL_EDGE, FULL_EDGE), Image.LANCZOS)
    f = out / f"{path.stem}_full.jpg"
    full.save(f, quality=92)
    files.append({"file": str(f), "region": "full frame", "box": [0, 0, w, h]})

    cols, rows = max(1, math.ceil(w / tile)), max(1, math.ceil(h / tile))
    for r, (y0, y1) in enumerate(spans(h, rows, overlap)):
        for c, (x0, x1) in enumerate(spans(w, cols, overlap)):
            crop = im.crop((x0, y0, x1, y1))
            crop = crop.resize((round(crop.width * zoom), round(crop.height * zoom)), Image.LANCZOS)
            region = f"{place(ROWS, r, rows)}-{place(COLS, c, cols)}"
            sheet = Image.new("RGB", (crop.width, crop.height + LABEL_H), (18, 18, 18))
            sheet.paste(crop, (0, LABEL_H))
            ImageDraw.Draw(sheet).text(
                (8, 8), f"{path.name}  row {r + 1}/{rows}  col {c + 1}/{cols}  {region}  "
                        f"x {x0}-{x1}  y {y0}-{y1}  {zoom:g}x", fill=(235, 235, 235))
            f = out / f"{path.stem}_r{r + 1}c{c + 1}.jpg"
            sheet.save(f, quality=92)
            files.append({"file": str(f), "region": region, "box": [x0, y0, x1, y1]})
    return {"image": str(path), "size": [w, h], "tiles": files}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+")
    ap.add_argument("-o", "--out", required=True, help="output folder")
    ap.add_argument("--tile", type=int, default=640, help="target tile size in source pixels (default 640)")
    ap.add_argument("--zoom", type=float, default=2.0, help="enlargement of each tile (default 2)")
    ap.add_argument("--overlap", type=float, default=0.15, help="overlap between neighbouring tiles (default 0.15)")
    a = ap.parse_args()
    if not 0 <= a.overlap < 0.5 or a.zoom <= 0 or a.tile < 64:
        sys.exit("use --tile >= 64, --zoom > 0 and 0 <= --overlap < 0.5")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    print(json.dumps([tiles_for(Path(p), out, a.tile, a.zoom, a.overlap) for p in a.images], indent=2))


if __name__ == "__main__":
    main()
