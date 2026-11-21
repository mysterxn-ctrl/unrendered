#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ruben Ferraro — Unrendered (https://github.com/mysterxn-ctrl/unrendered)
"""Optional optical/film finishing pass for images that still look too clean.

Subtle by default. Every effect is opt-in-strength and physically motivated:
  --grain      luminance-weighted sensor/film grain (0-1, default 0.25; stronger in shadows/midtones)
  --vignette   natural lens falloff (0-1, default 0.15)
  --ca         lateral chromatic aberration in px at the corners (default 0.6)
  --rolloff    soft highlight shoulder (0-1, default 0.2) to remove digital-harsh whites
  --jpeg Q     save as JPEG at quality Q (in-camera look) instead of PNG

Usage: photo_finish.py in.png -o out.png [--grain 0.25 --vignette 0.15 --ca 0.6 --rolloff 0.2]
Provenance: ICC profile, EXIF, XMP and DPI are kept; no camera EXIF is fabricated. Writing new pixels would
drop a C2PA manifest, so files that carry one are refused (exit code 3) instead of being silently stripped.
Requires Pillow + numpy.
"""
import argparse
import sys

try:
    import numpy as np
    from PIL import Image
except ImportError:
    sys.exit("needs: pip install pillow numpy")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--grain", type=float, default=0.25)
    ap.add_argument("--vignette", type=float, default=0.15)
    ap.add_argument("--ca", type=float, default=0.6)
    ap.add_argument("--rolloff", type=float, default=0.2)
    ap.add_argument("--jpeg", type=int)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()

    with open(a.src, "rb") as fh:
        raw = fh.read()
    if b"c2pa" in raw:  # C2PA manifests live in JUMBF boxes labelled "c2pa"
        print("refused: this file carries C2PA provenance data, and a finishing pass would remove it. "
              "Keep the image as delivered, or apply the edit with a C2PA-aware tool that records it.", file=sys.stderr)
        sys.exit(3)
    src = Image.open(a.src)
    info = dict(src.info)
    im = np.asarray(src.convert("RGB")).astype(np.float32) / 255.0
    h, w, _ = im.shape
    rng = np.random.default_rng(a.seed)

    # lateral chromatic aberration: scale R up and B down radially by a fraction of a pixel at corners
    if a.ca > 0:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        cx, cy = (w - 1) / 2, (h - 1) / 2
        rmax = np.hypot(cx, cy)
        def remap(ch, k):
            s = 1 + k * a.ca / rmax
            xs = np.clip(cx + (xx - cx) / s, 0, w - 1)
            ys = np.clip(cy + (yy - cy) / s, 0, h - 1)
            x0, y0 = np.floor(xs).astype(int), np.floor(ys).astype(int)
            x1, y1 = np.minimum(x0 + 1, w - 1), np.minimum(y0 + 1, h - 1)
            fx, fy = xs - x0, ys - y0
            return (ch[y0, x0] * (1 - fx) * (1 - fy) + ch[y0, x1] * fx * (1 - fy)
                    + ch[y1, x0] * (1 - fx) * fy + ch[y1, x1] * fx * fy)
        im[..., 0] = remap(im[..., 0], +1)
        im[..., 2] = remap(im[..., 2], -1)

    # highlight roll-off (soft shoulder above 0.8)
    if a.rolloff > 0:
        t = 0.8
        k = a.rolloff * 4
        over = np.clip(im - t, 0, None)
        im = np.where(im > t, t + (1 - t) * (1 - np.exp(-k * over / (1 - t))) / (1 - np.exp(-k)), im)

    # vignette (cos^4-like falloff)
    if a.vignette > 0:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.hypot((xx - w / 2) / (w / 2), (yy - h / 2) / (h / 2)) / np.sqrt(2)
        im *= (1 - a.vignette * r ** 2.2)[..., None]

    # grain: mostly luminance, stronger in mid/shadows, slightly clumped
    if a.grain > 0:
        lum = im @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
        n = rng.normal(0, 1, (h, w)).astype(np.float32)
        n = (n + np.roll(n, 1, 0) + np.roll(n, 1, 1)) / np.sqrt(3)
        amp = a.grain * 0.045 * (0.35 + 0.65 * (1 - lum) ** 0.8)
        im += (n * amp)[..., None]
        im += rng.normal(0, a.grain * 0.006, im.shape).astype(np.float32)  # faint chroma noise

    out = Image.fromarray((np.clip(im, 0, 1) * 255 + 0.5).astype(np.uint8))
    keep = {k: v for k, v in info.items() if k in ("icc_profile", "exif", "xmp", "dpi")}
    if a.jpeg:
        out.save(a.out, "JPEG", quality=a.jpeg, subsampling=1, **keep)
    else:
        out.save(a.out, **keep)
    print(a.out)


if __name__ == "__main__":
    main()
