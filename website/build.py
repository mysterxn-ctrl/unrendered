#!/usr/bin/env python3
"""Build the Unrendered website (landing page + documentation) as static files.

Lives in website/ of the repository and reads the repository as its content source.

Sources (in the repository, --repo)
  docs/*.md                         documentation (single source; also readable on GitHub)
  assets/brand/                     logos and social images
  skills/unrendered/models.json     live model selection shown on the landing page
  skills/unrendered/benchmarks/     leaderboard snapshots shown on the landing page
Sources (in this folder)
  site.json                         site config, page order, titles, meta descriptions
  templates/*.html                  page templates ({{placeholders}})
  static/                           css, js, fonts
  brand-extra/                      website-only images: hero art, favicons, app icons, Open Graph image

Usage
  python website/build.py --out _site [--base-url https://example.org/path] [--check-links]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

import markdown
from pygments.formatters import HtmlFormatter

SITE = Path(__file__).resolve().parent
EXTRA = SITE / "brand-extra"
ROOT = DOCS = BRAND = SKILL = None  # set from --repo in configure()
ms = None


def configure(repo: Path):
    """Point the builder at a repository checkout and load its model-selection module."""
    global ROOT, DOCS, BRAND, SKILL, ms
    ROOT = repo.resolve()
    DOCS, BRAND, SKILL = ROOT / "docs", ROOT / "assets" / "brand", ROOT / "skills" / "unrendered"
    if not (SKILL / "SKILL.md").exists():
        sys.exit(f"not an Unrendered repository: {ROOT}")
    # read only the bundled registry/snapshots (never a developer's local state)
    os.environ["UNRENDERED_HOME"] = str(SKILL)
    sys.path.insert(0, str(SKILL / "scripts"))
    import model_select  # noqa: E402
    ms = model_select


# ----------------------------------------------------------------------------- helpers
def render(tpl: str, **kw) -> str:
    def sub(m):
        key = m.group(1)
        if key not in kw:
            raise KeyError(f"template placeholder '{key}' has no value")
        return str(kw[key])
    return re.sub(r"\{\{(\w+)\}\}", sub, tpl)


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def fmt_date(iso: str) -> str:
    d = dt.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b')} {d.year}"


# ----------------------------------------------------------------------------- mermaid → static flow
def mermaid_to_flow(src: str) -> str:
    nodes, order = {}, []
    for nid, label in re.findall(r"(\w+)\[([^\]]+)\]", src):
        if nid not in nodes:
            nodes[nid] = label
            order.append(nid)
    def label_html(nid):
        parts = re.split(r"<br\s*/?>", nodes.get(nid, nid))
        out = f"<b>{esc(parts[0])}</b>"
        if len(parts) > 1:
            out += f"<small>{esc(' '.join(parts[1:]))}</small>"
        return out
    def name(nid):
        return esc(re.split(r"<br\s*/?>", nodes.get(nid, nid))[0])
    items = []
    for i, nid in enumerate(order):
        if i:
            items.append('<span class="arrow" aria-hidden="true">→</span>')
        items.append(f'<div class="node">{label_html(nid)}</div>')
    notes = []
    for a, lbl, b in re.findall(r"(\w+)(?:\[[^\]]*\])?\s*--\s*([^->\n]+?)\s*-->\s*(\w+)", src):
        notes.append(f"{name(a)} → {name(b)} on <em>{esc(lbl.strip())}</em>")
    for a, b in re.findall(r"^\s*(\w+)\s*-->\s*(\w+)\s*$", src, flags=re.M):
        if a in order and b in order and order.index(b) < order.index(a):
            notes.append(f"{name(a)} → back to {name(b)}")
    note_html = f'<p class="notes">{" · ".join(notes)}</p>' if notes else ""
    return f'<div class="flow" role="img" aria-label="Pipeline diagram">{"".join(items)}{note_html}</div>'


# ----------------------------------------------------------------------------- docs
class Site:
    def __init__(self, out: Path, base_url: str | None):
        self.cfg = json.loads(read(SITE / "site.json"))
        self.base_url = (base_url or self.cfg["base_url"]).rstrip("/")
        self.base = urlparse(self.base_url).path.rstrip("/")
        self.repo = self.cfg["repo"]
        self.branch = self.cfg["branch"]
        self.out = out
        self.today = dt.date.today().isoformat()
        self.docs = self.cfg["docs"]
        self.slug_of = {d["file"]: d["slug"] for d in self.docs}
        self.tpl = {n: read(SITE / "templates" / f"{n}.html") for n in ("base", "home-base", "home", "doc", "404")}
        self.edit_base = f"{self.repo}/edit/{self.branch}"
        self.pages = []  # (url_path, lastmod)

    # -------------------------------------------------------------- urls
    def doc_url(self, slug: str) -> str:
        return f"{self.base}/docs/{slug + '/' if slug else ''}"

    def abs_url(self, path: str) -> str:
        return self.base_url + path[len(self.base):] if path.startswith(self.base) else self.base_url + path

    def size_images(self, body: str) -> str:
        try:
            from PIL import Image
        except ImportError:
            return body
        def fix(m):
            tag = m.group(0)
            if " width=" in tag:
                return tag
            src = re.search(r'src="([^"]+)"', tag).group(1)
            name = Path(src).name
            f = next((d / name for d in (BRAND, EXTRA) if (d / name).exists()), None) if "/assets/brand/" in src else None
            if not f or not f.exists():
                return tag
            w, h = Image.open(f).size
            return tag[:-1].rstrip("/").rstrip() + f' width="{w}" height="{h}" loading="lazy" decoding="async">'
        return re.sub(r"<img [^>]+>", fix, body)

    def rewrite_links(self, body: str, src: Path) -> str:
        def fix(m):
            attr, url = m.group(1), html.unescape(m.group(2))
            if re.match(r"^(https?:|mailto:|#|data:)", url):
                return m.group(0)
            path, _, frag = url.partition("#")
            target = (src.parent / path).resolve()
            frag = f"#{frag}" if frag else ""
            if target.suffix == ".md" and target.parent == DOCS and target.name in self.slug_of:
                new = self.doc_url(self.slug_of[target.name]) + frag
            elif BRAND in target.parents or EXTRA in target.parents:
                new = f"{self.base}/assets/brand/{target.name}"
            else:
                try:
                    rel = target.relative_to(ROOT).as_posix()
                except ValueError:
                    return m.group(0)
                kind = "tree" if target.is_dir() else "blob"
                new = f"{self.repo}/{kind}/{self.branch}/{rel}{frag}"
            return f'{attr}="{esc(new)}"'
        return re.sub(r'(href|src)="([^"]+)"', fix, body)

    # -------------------------------------------------------------- page shell
    def shell(self, *, title, description, canonical_path, content, jsonld, og_type="website", robots="index,follow",
              body_class="", current="", preload="", extra_css="", og_title=None, base_tpl="base"):
        cur = {k: "" for k in ("cur_start", "cur_how", "cur_models", "cur_docs")}
        if current:
            cur[current] = ' aria-current="page"'
        return render(
            self.tpl[base_tpl], title=esc(title), description=esc(description), canonical=self.abs_url(canonical_path),
            robots=robots, og_type=og_type, og_title=esc(og_title or title), base_url=self.base_url, base=self.base,
            repo=self.repo, branch=self.branch, version=self.cfg["version"], year=dt.date.today().year,
            jsonld=json.dumps(jsonld, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"),
            content=content, body_class=body_class, preload=preload, extra_css=extra_css, asset_v=self.asset_v, **cur)

    def write(self, url_path: str, page: str, lastmod: str | None = None, sitemap=True):
        rel = url_path[len(self.base):].lstrip("/")
        f = self.out / rel / "index.html" if (not rel or rel.endswith("/")) else self.out / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(page, encoding="utf-8")
        if sitemap:
            self.pages.append((url_path, lastmod or self.today))

    # -------------------------------------------------------------- docs pages
    def build_docs(self):
        md = markdown.Markdown(
            extensions=["tables", "fenced_code", "codehilite", "toc", "attr_list", "sane_lists", "smarty"],
            extension_configs={
                "codehilite": {"guess_lang": False, "css_class": "hl"},
                "toc": {"permalink": "#", "permalink_class": "anchor", "permalink_title": "Link to this section",
                        "toc_depth": "2-3"},
            })
        for i, d in enumerate(self.docs):
            src = DOCS / d["file"]
            text = read(src)
            text = re.sub(r"```mermaid\n(.*?)```", lambda m: "\n" + mermaid_to_flow(m.group(1)) + "\n", text, flags=re.S)
            md.reset()
            body = self.size_images(self.rewrite_links(md.convert(text), src))
            toc = self.toc_html(md.toc_tokens)
            url = self.doc_url(d["slug"])
            prev_d = self.docs[i - 1] if i > 0 else None
            next_d = self.docs[i + 1] if i + 1 < len(self.docs) else None
            pager = ""
            if prev_d:
                pager += f'<a class="prev" href="{self.doc_url(prev_d["slug"])}"><small>Previous</small><span>{esc(prev_d["title"])}</span></a>\n'
            if next_d:
                pager += f'<a class="next" href="{self.doc_url(next_d["slug"])}"><small>Next</small><span>{esc(next_d["title"])}</span></a>\n'
            crumbs = [("Home", f"{self.base}/"), ("Docs", self.doc_url(""))] + ([(d["title"], url)] if d["slug"] else [])
            current_attr = ' aria-current="page"'
            breadcrumb = "\n".join(
                f'<li><a href="{u}"{current_attr if n == len(crumbs) - 1 else ""}>{esc(t)}</a></li>'
                for n, (t, u) in enumerate(crumbs))
            content = render(self.tpl["doc"], sidebar=self.sidebar(d["slug"]), breadcrumb=breadcrumb, body=body,
                             edit_url=f"{self.repo}/edit/{self.branch}/docs/{d['file']}", pager=pager, toc=toc)
            title = d.get("seo_title") or f"{d['title']} — Unrendered docs"
            jsonld = {"@context": "https://schema.org", "@graph": [
                {"@type": "TechArticle", "headline": d["title"], "description": d["description"],
                 "url": self.abs_url(url), "inLanguage": "en", "dateModified": self.today,
                 "image": f"{self.base_url}/assets/brand/og-image.jpg",
                 "author": {"@type": "Person", "name": "Ruben Ferraro", "url": "https://github.com/mysterxn-ctrl"},
                 "publisher": {"@type": "Organization", "name": "Unrendered",
                               "logo": {"@type": "ImageObject", "url": f"{self.base_url}/assets/brand/icon-512.png"}},
                 "isPartOf": {"@type": "WebSite", "name": "Unrendered", "url": self.base_url + "/"}},
                {"@type": "BreadcrumbList", "itemListElement": [
                    {"@type": "ListItem", "position": n + 1, "name": t, "item": self.abs_url(u)}
                    for n, (t, u) in enumerate(crumbs)]}]}
            current = {"getting-started": "cur_start", "how-it-works": "cur_how", "model-selection": "cur_models"}.get(
                d["slug"], "cur_docs")
            page = self.shell(title=title, description=d["description"], canonical_path=url, content=content,
                              jsonld=jsonld, og_type="article", body_class="doc-page", current=current,
                              extra_css=f'<link rel="stylesheet" href="{self.base}/assets/css/code.css?v={self.asset_v}">',
                              og_title=d["title"] if d["slug"] else "Unrendered documentation")
            self.write(url, page)

    def toc_html(self, tokens):
        def walk(ts):
            out = []
            for t in ts:
                if t["level"] == 1:
                    out += walk(t.get("children", []))
                    continue
                child = walk(t.get("children", [])) if t["level"] == 2 else []
                sub = f"<ul>{''.join(child)}</ul>" if child else ""
                out.append(f'<li><a href="#{t["id"]}">{t["name"]}</a>{sub}</li>')
            return out
        lis = walk(tokens)
        return f'<p class="nav-h">On this page</p>\n<ul>{"".join(lis)}</ul>' if lis else ""

    def sidebar(self, current_slug):
        out, section = [], None
        for d in self.docs:
            if d["section"] != section:
                if section is not None:
                    out.append("</ul>")
                section = d["section"]
                out.append(f'<p class="nav-h">{esc(section)}</p><ul>')
            cur = ' aria-current="page"' if d["slug"] == current_slug else ""
            out.append(f'<li><a href="{self.doc_url(d["slug"])}"{cur}>{esc(d.get("nav", d["title"]))}</a></li>')
        out.append("</ul>")
        return "\n".join(out)

    # -------------------------------------------------------------- home
    def boards_html(self):
        """Leaderboard tables (real bundled rows) plus the JSON the page's decision rule runs on."""
        reg, _ = ms.load_registry()
        snaps = ms.load_snapshots()
        names = {"generate": "Image generation", "edit": "Image editing"}
        cards, data = [], {"default": reg["default"], "tracks": {}}
        for track in ms.TRACKS:
            board = ms.pick_board(snaps, track, "primary")
            if not board:
                continue
            rows = ms.merge_configs(board["rows"])[:5]
            items = []
            for r in rows:
                m = ms.find_model(reg, r["name"])
                items.append({"id": m["id"] if m else r["key"], "name": r["name"], "elo": round(r["elo"]),
                              "ci": round(r["ci"]) if r.get("ci") is not None else None})
            data["tracks"][track] = {"rows": items, "current": reg["default"][track]}
            trs = []
            for i, r in enumerate(items, 1):
                ci = f'<span class="ci">± {r["ci"]}</span>' if r["ci"] is not None else ""
                trs.append(f'<tr data-model="{esc(r["id"])}"><td class="rank">{i}</td><td>{esc(r["name"])}</td>'
                           f'<td class="num"><span data-sc-count="{r["elo"] - 200} {r["elo"]}" data-sc-count-ms="1400">{r["elo"]}</span> {ci}</td></tr>')
            cards.append(f"""      <div class="board" data-track="{track}" data-sc-in>
        <p class="board__title">{names[track]}</p>
        <table><caption class="visually-hidden">{names[track]}: top five on the Artificial Analysis arena, Elo with 95% confidence interval</caption>
        <thead><tr><th scope="col">#</th><th scope="col">Model</th><th scope="col" class="num">Elo</th></tr></thead>
        <tbody>{''.join(trs)}</tbody></table>
        <p class="board__verdict" data-verdict="{track}">Decision rule runs in this page.</p>
      </div>""")
        return "\n".join(cards), json.dumps(data, ensure_ascii=False).replace("</", "<\\/")

    def build_home(self):
        boards, board_json = self.boards_html()
        content = render(self.tpl["home"], base=self.base, repo=self.repo, repo_slug=self.cfg["repo_slug"],
                         branch=self.branch, year=dt.date.today().year, boards=boards, board_json=board_json)
        home = self.cfg["home"]
        url = f"{self.base}/"
        person = {"@type": "Person", "name": "Ruben Ferraro", "url": "https://github.com/mysterxn-ctrl"}
        jsonld = {"@context": "https://schema.org", "@graph": [
            {"@type": "WebSite", "@id": self.base_url + "/#website", "name": "Unrendered", "url": self.base_url + "/",
             "description": home["description"], "inLanguage": "en", "author": person},
            {"@type": "SoftwareApplication", "name": "Unrendered", "alternateName": "Unrendered agent skill",
             "description": home["description"], "url": self.base_url + "/", "image": f"{self.base_url}/assets/brand/og-image.jpg",
             "applicationCategory": "DeveloperApplication", "applicationSubCategory": "AI image generation",
             "operatingSystem": "Windows, macOS, Linux", "softwareVersion": self.cfg["version"],
             "license": "https://www.apache.org/licenses/LICENSE-2.0", "downloadUrl": self.repo, "isAccessibleForFree": True,
             "author": person, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
             "keywords": "photorealistic AI images, AI image generation, AI image editing, agent skill, Claude Code skill, "
                         "Codex skill, GPT Image, image generation API, prompt engineering, AI photography"},
            {"@type": "SoftwareSourceCode", "name": "Unrendered", "codeRepository": self.repo,
             "programmingLanguage": "Python", "runtimePlatform": "Python 3.9+",
             "license": "https://www.apache.org/licenses/LICENSE-2.0", "author": person,
             "description": home["description"]}]}
        page = self.shell(title=home["title"], description=home["description"], canonical_path=url, content=content,
                          jsonld=jsonld, body_class="home", og_title="Unrendered: photos, not renders.",
                          base_tpl="home-base")
        self.write(url, page)

    def build_404(self):
        content = render(self.tpl["404"], base=self.base)
        page = self.shell(title="Page not found — Unrendered: photos, not renders",
                          description="This page does not exist. Browse the Unrendered documentation or return to the homepage.",
                          canonical_path=f"{self.base}/404.html", content=content,
                          jsonld={"@context": "https://schema.org", "@type": "WebPage", "name": "Page not found"},
                          robots="noindex")
        (self.out / "404.html").write_text(page, encoding="utf-8")

    # -------------------------------------------------------------- static + meta files
    def copy_static(self):
        shutil.copytree(SITE / "static", self.out / "assets", dirs_exist_ok=True)
        shutil.copytree(BRAND, self.out / "assets" / "brand", dirs_exist_ok=True)
        shutil.copytree(EXTRA, self.out / "assets" / "brand", dirs_exist_ok=True)
        shutil.copy2(EXTRA / "favicon.ico", self.out / "favicon.ico")
        css = HtmlFormatter(style="github-dark").get_style_defs(".hl")
        css = re.sub(r"^\.hl \{ background: [^}]+\}\n?", "", css, flags=re.M)
        (self.out / "assets" / "css" / "code.css").write_text(
            "/* syntax highlighting (Pygments github-dark) */\n" + css, encoding="utf-8")
        (self.out / ".nojekyll").write_text("", encoding="utf-8")

    def write_meta(self):
        urls = "\n".join(
            f"  <url><loc>{esc(self.abs_url(u))}</loc><lastmod>{lm}</lastmod>"
            f"<priority>{'1.0' if u == self.base + '/' else '0.8'}</priority></url>" for u, lm in self.pages)
        (self.out / "sitemap.xml").write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{urls}\n</urlset>\n", encoding="utf-8")
        (self.out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {self.base_url}/sitemap.xml\n",
                                             encoding="utf-8")
        manifest = {"name": "Unrendered", "short_name": "Unrendered", "description": self.cfg["home"]["description"],
                    "start_url": f"{self.base}/", "scope": f"{self.base}/", "display": "standalone",
                    "background_color": "#0a0d14", "theme_color": "#0a0d14",
                    "icons": [{"src": f"{self.base}/assets/brand/icon-192.png", "sizes": "192x192", "type": "image/png"},
                              {"src": f"{self.base}/assets/brand/icon-512.png", "sizes": "512x512", "type": "image/png"}]}
        (self.out / "site.webmanifest").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        lines = [f"# Unrendered", "", f"> {self.cfg['home']['description']}", "",
                 "Unrendered is an agent skill (SKILL.md) for photorealistic image generation and editing through any "
                 "image-generation API, with autonomous benchmark-based model selection.", "", "## Documentation", ""]
        for d in self.docs:
            lines.append(f"- [{d['title']}]({self.abs_url(self.doc_url(d['slug']))}): {d['description']}")
        lines += ["", "## Source", "", f"- [Repository]({self.repo})",
                  f"- [Skill instructions]({self.repo}/blob/{self.branch}/skills/unrendered/SKILL.md)"]
        (self.out / "llms.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def build(self):
        if self.out.exists():
            shutil.rmtree(self.out)
        self.out.mkdir(parents=True)
        h = hashlib.sha1()
        for f in sorted((SITE / "static").rglob("*.*")):
            if f.suffix in (".css", ".js"):
                h.update(f.read_bytes())
        self.asset_v = h.hexdigest()[:10]
        self.copy_static()
        self.build_home()
        self.build_docs()
        self.build_404()
        self.write_meta()
        print(f"built {len(self.pages)} pages into {self.out} (base {self.base or '/'})")


# ----------------------------------------------------------------------------- link check
def check_links(out: Path, base: str) -> int:
    ids_cache, errors = {}, []
    def ids_of(f: Path):
        if f not in ids_cache:
            ids_cache[f] = set(re.findall(r'\sid="([^"]+)"', f.read_text(encoding="utf-8")))
        return ids_cache[f]
    def resolve(path: str):
        rel = path[len(base):] if base and path.startswith(base) else path
        f = out / rel.lstrip("/")
        if f.is_dir() or rel.endswith("/"):
            f = f / "index.html"
        return f
    for page in out.rglob("*.html"):
        text = page.read_text(encoding="utf-8")
        for attr, url in re.findall(r'(href|src|srcset|imagesrcset)="([^"]+)"', text):
            for u in ([s.strip().split(" ")[0] for s in url.split(",")] if "srcset" in attr else [url]):
                u = html.unescape(u)
                if re.match(r"^(https?:|mailto:|data:)", u):
                    continue
                path, _, frag = u.partition("#")
                path = path.split("?")[0]
                target = page if not path else resolve(path) if path.startswith("/") else (page.parent / path)
                if not target.exists():
                    errors.append(f"{page.relative_to(out)}: missing {u}")
                elif frag and target.suffix == ".html" and frag not in ids_of(target):
                    errors.append(f"{page.relative_to(out)}: missing anchor {u}")
    for e in errors:
        print("BROKEN", e)
    print(f"link check: {len(errors)} problem(s)")
    return 1 if errors else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=os.environ.get("UNRENDERED_REPO", str(SITE.parent)),
                    help="path to the Unrendered repository (default: the repository this folder lives in)")
    ap.add_argument("--out", default="_site")
    ap.add_argument("--base-url", help="override site.json base_url (e.g. for local previews)")
    ap.add_argument("--check-links", action="store_true")
    a = ap.parse_args()
    configure(Path(a.repo))
    out = Path(a.out).resolve()
    site = Site(out, a.base_url)
    site.build()
    if a.check_links:
        sys.exit(check_links(out, site.base))


if __name__ == "__main__":
    main()
