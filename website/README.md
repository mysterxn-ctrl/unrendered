# Unrendered website

Source of the Unrendered website on GitHub Pages: a live-surface landing page plus the full documentation, built from [`docs/`](../docs) and the bundled model registry.

## Build locally

```bash
pip install -r website/requirements.txt
```

```bash
python3 website/build.py --out _site --check-links
```

Preview with the production base path:

```bash
mkdir -p /tmp/preview && rm -rf /tmp/preview/unrendered && cp -r _site /tmp/preview/unrendered
```

```bash
python3 -m http.server 8000 --directory /tmp/preview
```

Open `http://localhost:8000/unrendered/`.

## Contents

| Path | Purpose |
|---|---|
| `build.py` | Markdown → HTML, SEO metadata, JSON-LD, sitemap, robots.txt, llms.txt, link check |
| `site.json` | Base URL, page order, titles and meta descriptions |
| `templates/` | Landing page and documentation templates |
| `static/` | CSS, JavaScript, self-hosted fonts (Sora, Inter: SIL OFL), scroll engine |
| `brand-extra/` | Website-only images: hero art, example images, favicons, app icons, Open Graph image |
| `design/` | Design brief and plan |

Deployment: `.github/workflows/pages.yml` builds and publishes on every push to `main`.

© 2026 Ruben Ferraro. Brand images are not covered by the Apache License; see `assets/brand/LICENSE.md`.
