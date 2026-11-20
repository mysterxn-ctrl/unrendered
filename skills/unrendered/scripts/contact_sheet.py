#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ruben Ferraro — Unrendered (https://github.com/mysterxn-ctrl/unrendered)
"""Build a labelled contact sheet of candidate images for side-by-side QA.

  contact_sheet.py img1.png img2.png ... -o sheet.jpg [--cell 768] [--crops]
--crops adds a 2x centre crop row per image so fine texture (skin, hands, text) is inspectable.
Requires Pillow (pip install pillow).
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Pillow missing: pip install pillow")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--cell", type=int, default=768)
    ap.add_argument("--crops", action="store_true")
    a = ap.parse_args()
    ims = [Image.open(p).convert("RGB") for p in a.images]
    rows = 2 if a.crops else 1
    pad, label_h = 12, 28
    W = len(ims) * (a.cell + pad) + pad
    H = rows * (a.cell + pad + label_h) + pad
    sheet = Image.new("RGB", (W, H), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    for i, (im, path) in enumerate(zip(ims, a.images)):
        x = pad + i * (a.cell + pad)
        t = im.copy()
        t.thumbnail((a.cell, a.cell))
        sheet.paste(t, (x, pad + label_h))
        d.text((x, pad + 6), f"#{i + 1}  {Path(path).name}  {im.width}x{im.height}", fill=(230, 230, 230))
        if a.crops:
            w, h = im.size
            cw, ch = w // 3, h // 3
            crop = im.crop((w // 2 - cw // 2, h // 2 - ch // 2, w // 2 + cw // 2, h // 2 + ch // 2))
            s = min(a.cell / crop.width, a.cell / crop.height)
            crop = crop.resize((int(crop.width * s), int(crop.height * s)), Image.LANCZOS)
            y = pad + label_h + a.cell + pad + label_h
            sheet.paste(crop, (x, y))
            d.text((x, y - label_h + 6), f"#{i + 1} centre crop (~3x)", fill=(200, 200, 200))
    sheet.save(a.out, quality=92)
    print(a.out)


if __name__ == "__main__":
    main()
