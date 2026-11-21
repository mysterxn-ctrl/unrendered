#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ruben Ferraro — Unrendered (https://github.com/mysterxn-ctrl/unrendered)
"""Provider-agnostic image generation runner (stdlib only).

Every provider is described by a JSON *profile* (see providers/_TEMPLATE.json and
references/provider-adapters.md). The runner maps canonical parameters
(prompt, model, size, quality, complexity, n, ...) onto the provider's wire format,
handles sync or async (submit + poll) APIs, extracts images (base64, data URI or URL)
and saves them with a sidecar JSON for reproducibility. API keys are read from
environment variables only and are never written to disk or stdout.

Usage:
  imagegen.py profiles
  imagegen.py validate --profile NAME
  imagegen.py generate --profile NAME --model ID --prompt-file brief.txt [--size 1536x1024]
                       [--quality high] [--complexity high] [--n 3] [--out-dir out/x] [--dry-run]
  imagegen.py edit --profile NAME --model ID --prompt-file edit.txt --image in.png [--image ref.png]
                   [--mask mask.png] [--complexity low] ...
  Extra provider fields: --set key=value (repeatable, raw passthrough into the body).
"""
from __future__ import annotations

import argparse
import base64
import datetime as _dt
import json
import math
import mimetypes
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = Path(os.environ.get("UNRENDERED_HOME") or Path.home() / ".config" / "unrendered").expanduser()
PROFILE_DIRS = [STATE_DIR / "providers", SKILL_DIR / "providers"]
CANONICAL = ["prompt", "model", "size", "quality", "complexity", "n", "output_format", "background",
             "moderation", "seed", "negative_prompt", "images", "mask", "output_compression"]
USER_AGENT = "unrendered/1.0"


# ----------------------------------------------------------------------------- utils
def die(msg: str, code: int = 2):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def warn(msg: str):
    print(f"warning: {msg}", file=sys.stderr)


def load_profile(name: str) -> dict:
    p = Path(name)
    if p.suffix == ".json" and p.exists():
        return json.loads(p.read_text())
    for d in PROFILE_DIRS:
        f = d / f"{name}.json"
        if f.exists():
            prof = json.loads(f.read_text())
            prof.setdefault("_file", str(f))
            return prof
    die(f"profile '{name}' not found in {[str(d) for d in PROFILE_DIRS]}")


def expand_env(s: str) -> str:
    return re.sub(r"\$\{([A-Z0-9_]+)\}", lambda m: os.environ.get(m.group(1), ""), s)


def get_path(obj, path: str):
    """Resolve 'a.b[0].c', 'data[*].url', '[0]' etc. Returns a flat list of matches."""
    tokens = re.findall(r"[^.\[\]]+|\[\*\]|\[\d+\]", path)
    cur = [obj]
    for t in tokens:
        nxt = []
        for o in cur:
            if t == "[*]":
                if isinstance(o, list):
                    nxt.extend(o)
                elif isinstance(o, dict):
                    nxt.extend(o.values())
            elif t.startswith("["):
                i = int(t[1:-1])
                if isinstance(o, list) and -len(o) <= i < len(o):
                    nxt.append(o[i])
            elif isinstance(o, dict) and t in o:
                nxt.append(o[t])
        cur = nxt
    out = []
    for v in cur:
        if isinstance(v, list):
            out.extend(v)
        elif v is not None:
            out.append(v)
    return out


def set_path(obj: dict, path: str, value):
    parts = path.split(".")
    for p in parts[:-1]:
        obj = obj.setdefault(p, {})
    obj[parts[-1]] = value


def parse_size(size: str):
    m = re.fullmatch(r"(\d+)\s*[xX×]\s*(\d+)", str(size))
    return (int(m.group(1)), int(m.group(2))) if m else None


def aspect_from_size(size: str, choices=None) -> str:
    wh = parse_size(size)
    if not wh:
        return size  # already a ratio or 'auto'
    w, h = wh
    if choices:
        target = w / h
        def ratio(c):
            a, b = c.split(":")
            return float(a) / float(b)
        return min(choices, key=lambda c: abs(math.log(ratio(c) / target)))
    g = math.gcd(w, h)
    return f"{w // g}:{h // g}"


def tier_from_size(size: str, tiers=None) -> str:
    wh = parse_size(size)
    if not wh:
        return size
    mp = wh[0] * wh[1] / 1e6
    tiers = tiers or {"1K": 1.6, "2K": 4.6, "4K": 9.9}
    for name, limit in sorted(tiers.items(), key=lambda kv: kv[1]):
        if mp <= limit:
            return name
    return list(tiers)[-1]


def file_to_data_uri(ref: str) -> str:
    if re.match(r"^(https?:|data:)", ref):
        return ref
    p = Path(ref)
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def file_to_b64(ref: str) -> str:
    if ref.startswith("data:"):
        return ref.split(",", 1)[1]
    return base64.b64encode(Path(ref).read_bytes()).decode()


def sniff_ext(data: bytes, fallback="png") -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data.lstrip()[:5] in (b"<?xml", b"<svg ") or b"<svg" in data[:256]:
        return "svg"
    if data[4:12] in (b"ftypavif", b"ftypheic"):
        return "avif" if b"avif" in data[4:12] else "heic"
    return fallback


# ----------------------------------------------------------------------------- HTTP
class Http:
    def __init__(self, profile: dict, dry_run=False, verbose=False):
        self.p = profile
        self.dry = dry_run
        self.verbose = verbose
        self.base = expand_env(profile.get("base_url", "")).rstrip("/")
        self.timeout = profile.get("timeout_s", 300)

    def _auth(self, headers: dict, url: str) -> str:
        a = self.p.get("auth", {"type": "none"})
        t = a.get("type", "header")
        if t == "none":
            return url
        key = os.environ.get(a.get("env", ""), "")
        if not key:
            if a.get("optional"):
                return url
            die(f"environment variable {a.get('env')} is not set (profile auth). Set it; never paste keys in chat.")
        if t == "header":
            headers[a.get("header", "Authorization")] = a.get("prefix", "Bearer ") + key
        elif t == "query":
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{urllib.parse.quote(a.get('param', 'key'))}={urllib.parse.quote(key)}"
        return url

    def request(self, method: str, url: str, body=None, content_type="json", extra_headers=None, auth=True):
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        headers.update(self.p.get("headers", {}))
        headers.update(extra_headers or {})
        data = None
        if body is not None:
            if content_type == "multipart":
                data, ctype = encode_multipart(body)
                headers["Content-Type"] = ctype
            else:
                data = json.dumps(body).encode()
                headers["Content-Type"] = "application/json"
        if auth:
            url = self._auth(headers, url)
        if self.dry:
            shown = {k: ("***" if k.lower() in ("authorization", "x-api-key", "api-key", "x-key") or "key" in k.lower() or "token" in k.lower() else v) for k, v in headers.items()}
            preview = body if content_type != "multipart" else {k: (f"<file {v[0]}>" if isinstance(v, tuple) else v) for k, v in body.items()}
            safe_url = re.sub(r"([?&][^=]*(key|token)[^=]*=)[^&]+", r"\1***", url, flags=re.I)
            print(json.dumps({"method": method, "url": safe_url, "headers": shown, "body": _truncate(preview)}, indent=2))
            return None
        last_err = None
        for attempt in range(5):
            req = urllib.request.Request(url, data=data, method=method, headers=headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    raw = r.read()
                    ctype = r.headers.get("Content-Type", "")
                    if "json" in ctype or raw[:1] in (b"{", b"["):
                        return json.loads(raw.decode() or "null")
                    return {"__binary__": raw, "__content_type__": ctype}
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace")[:2000]
                last_err = f"HTTP {e.code}: {msg}"
                if e.code in (408, 409, 425, 429, 500, 502, 503, 504) and attempt < 4:
                    time.sleep(min(60, 2 ** attempt * 2))
                    continue
                die(f"{method} {url.split('?')[0]} failed: {last_err}", 3)
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                last_err = str(e)
                if attempt < 4:
                    time.sleep(min(60, 2 ** attempt * 2))
                    continue
                die(f"{method} {url.split('?')[0]} failed: {last_err}", 3)
        die(f"request failed: {last_err}", 3)

    def download(self, url: str) -> bytes:
        headers = {"User-Agent": USER_AGENT}
        if self.p.get("download_with_auth"):
            url = self._auth(headers, url)
        for attempt in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=self.timeout) as r:
                    return r.read()
            except Exception as e:  # noqa: BLE001
                if attempt == 3:
                    die(f"download failed: {e}", 3)
                time.sleep(2 ** attempt)


def _truncate(o, n=200):
    if isinstance(o, str):
        return o if len(o) <= n or not re.match(r"^(data:|[A-Za-z0-9+/=]{200,})", o) else o[:60] + f"...<{len(o)} chars>"
    if isinstance(o, dict):
        return {k: _truncate(v, n) for k, v in o.items()}
    if isinstance(o, list):
        return [_truncate(v, n) for v in o]
    return o


def encode_multipart(fields: dict):
    boundary = "----photoreal" + uuid.uuid4().hex
    out = bytearray()
    for name, value in fields.items():
        values = value if isinstance(value, list) else [value]
        for v in values:
            out += f"--{boundary}\r\n".encode()
            if isinstance(v, tuple):  # (path_or_name, bytes, mime)
                fname, content, mime = v
                out += f'Content-Disposition: form-data; name="{name}"; filename="{Path(fname).name}"\r\n'.encode()
                out += f"Content-Type: {mime}\r\n\r\n".encode() + content + b"\r\n"
            else:
                sv = v if isinstance(v, str) else json.dumps(v)
                out += f'Content-Disposition: form-data; name="{name}"\r\n\r\n{sv}\r\n'.encode()
    out += f"--{boundary}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={boundary}"


# ----------------------------------------------------------------------------- mapping
def apply_transform(value, spec: dict, multipart: bool):
    t = spec.get("transform")
    if t is None:
        pass
    elif t == "aspect_ratio":
        value = aspect_from_size(value, spec.get("choices"))
    elif t == "resolution_tier":
        value = tier_from_size(value, spec.get("tiers"))
    elif t == "width":
        value = parse_size(value)[0]
    elif t == "height":
        value = parse_size(value)[1]
    elif t == "int":
        value = int(value)
    elif t == "float":
        value = float(value)
    elif t == "bool":
        value = str(value).lower() in ("1", "true", "yes")
    elif t == "list":
        value = value if isinstance(value, list) else [value]
    elif t == "first":
        value = value[0] if isinstance(value, list) else value
    elif t in ("data_uri", "b64", "file"):
        items = value if isinstance(value, list) else [value]
        conv = []
        for ref in items:
            if t == "data_uri":
                conv.append(file_to_data_uri(ref))
            elif t == "b64":
                conv.append(file_to_b64(ref))
            else:
                if not multipart:
                    die("transform 'file' requires content_type 'multipart'")
                conv.append((ref, Path(ref).read_bytes(), mimetypes.guess_type(ref)[0] or "image/png"))
        value = conv if (isinstance(value, list) and not spec.get("single")) else conv[0]
    elif t == "template":
        value = spec["template"].format(value=value)
    else:
        die(f"unknown transform '{t}'")
    if "map" in spec:
        value = spec["map"].get(str(value), value)
    return value


def build_body(op: dict, canon: dict, profile: dict):
    multipart = op.get("content_type") == "multipart"
    body: dict = json.loads(json.dumps(op.get("static", {})))
    params = op.get("params", {})
    dropped = []
    prompt = canon.get("prompt", "")
    if canon.get("negative_prompt") and "negative_prompt" not in params:
        prompt = f"{prompt}\nAvoid: {canon['negative_prompt']}"
    canon = dict(canon, prompt=prompt)
    for key, value in canon.items():
        if value is None or value == [] or key.startswith("_"):
            continue
        if key == "negative_prompt" and "negative_prompt" not in params:
            continue
        specs = params.get(key)
        if specs is None:
            if key == "n":
                continue  # handled client-side by looping
            if key == "model" and "{model}" in (op.get("path", "") + op.get("url", "")):
                continue  # model travels in the URL
            dropped.append(key)
            continue
        for spec in specs if isinstance(specs, list) else [specs]:
            if isinstance(spec, str):
                spec = {"to": spec}
            v = apply_transform(value, spec, multipart)
            if spec.get("to"):
                set_path(body, spec["to"], v)
    for extra in canon.get("_set", []):
        k, _, v = extra.partition("=")
        try:
            v = json.loads(v)
        except json.JSONDecodeError:
            pass
        set_path(body, k, v)
    if dropped:
        warn(f"provider profile has no mapping for {dropped}; not sent (add them to the profile if the provider supports them)")
    return body


def resolve_model(profile: dict, model: str, opname: str = "generate") -> str:
    """Canonical id -> provider wire id. Operation-level model_map (e.g. a separate edit model/endpoint) wins."""
    op = profile.get("operations", {}).get(opname, {}) or {}
    return op.get("model_map", {}).get(model) or profile.get("model_map", {}).get(model, model)


# ----------------------------------------------------------------------------- run
def run_op(profile: dict, opname: str, canon: dict, out_dir: Path, slug: str, dry: bool, verbose: bool):
    op = profile.get("operations", {}).get(opname)
    if not op:
        die(f"profile '{profile.get('name')}' has no '{opname}' operation")
    if profile.get("type") == "tool":
        print(json.dumps({"action": "CALL_TOOL", "tool": profile.get("tool"), "operation": opname,
                          "arguments_canonical": {k: v for k, v in canon.items() if v not in (None, []) and not k.startswith("_")},
                          "do": "This provider is an agent tool (e.g. MCP). Call it yourself with these canonical values mapped to its argument names, save the outputs, then continue with QA."}, indent=2))
        sys.exit(10)
    http = Http(profile, dry_run=dry, verbose=verbose)
    model_wire = resolve_model(profile, canon.get("model", ""), opname)
    canon = dict(canon, model=model_wire)
    path = op.get("path", "").replace("{model}", model_wire)
    url = op["url"].replace("{model}", model_wire) if op.get("url") else http.base + path
    url = expand_env(url)
    if op.get("query"):
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(op["query"])

    n = int(canon.get("n") or 1)
    native_n = "n" in op.get("params", {})
    calls = 1 if native_n else n
    saved = []
    for call_i in range(calls):
        body = build_body(op, canon, profile)
        resp = http.request(op.get("method", "POST"), url, body, op.get("content_type", "json"))
        if dry:
            if calls > 1:
                print(f"(would repeat {calls}x client-side because the profile maps no 'n')")
            return []
        resp = maybe_poll(http, op, resp)
        images, meta = extract_images(http, op, resp)
        if not images:
            die("no image found in response. Check the profile's result.paths. Response (truncated): "
                + json.dumps(_truncate(resp if not isinstance(resp, dict) or "__binary__" not in resp else "<binary>"))[:1500], 4)
        for img in images:
            saved.append(save_image(img, out_dir, slug, len(saved) + 1, canon, profile, opname, meta))
    return saved


def maybe_poll(http: Http, op: dict, resp):
    a = op.get("async")
    if not a:
        return resp
    status_path = a.get("status_path", "status")
    done = [s.lower() for s in a.get("done", ["completed", "succeeded", "success", "done", "ready"])]
    failed = [s.lower() for s in a.get("failed", ["failed", "error", "canceled", "cancelled"])]

    st = get_path(resp, status_path)
    if st and str(st[0]).lower() in done and a.get("result_in_submit", True):
        return resp

    poll_url = None
    if a.get("poll_url_path"):
        found = get_path(resp, a["poll_url_path"])
        poll_url = found[0] if found else None
    if not poll_url:
        ids = get_path(resp, a.get("id_path", "id"))
        if not ids:
            die("async: no job id in submit response: " + json.dumps(_truncate(resp))[:800], 4)
        poll_url = expand_env(a["poll_url"]).replace("{base_url}", http.base).replace("{id}", str(ids[0]))
    interval = a.get("interval_s", 3)
    deadline = time.time() + a.get("timeout_s", 900)
    while time.time() < deadline:
        time.sleep(interval)
        r = http.request(a.get("poll_method", "GET"), poll_url)
        st = get_path(r, status_path)
        s = str(st[0]).lower() if st else ""
        if s in failed:
            die(f"generation failed: {json.dumps(_truncate(r))[:1500]}", 5)
        if s in done:
            if a.get("result_url_path"):
                ru = get_path(r, a["result_url_path"])
                if ru:
                    return http.request("GET", ru[0])
            return r
        interval = min(interval * 1.3, 15)
    die("async: timed out waiting for result", 5)


def extract_images(http: Http, op: dict, resp):
    if isinstance(resp, dict) and "__binary__" in resp:
        return [resp["__binary__"]], {}
    paths = op.get("result", {}).get("paths", ["data[*].b64_json", "data[*].url", "images[*].url", "output", "outputs", "image", "url"])
    out = []
    for p in paths:
        for v in get_path(resp, p):
            if isinstance(v, dict):
                v = v.get("url") or v.get("b64_json") or v.get("base64") or v.get("image")
            if not isinstance(v, str) or not v:
                continue
            if v.startswith("data:"):
                out.append(base64.b64decode(v.split(",", 1)[1]))
            elif v.startswith("http://") or v.startswith("https://"):
                out.append(http.download(v))
            elif re.fullmatch(r"[A-Za-z0-9+/=_\-\s]{16,}", v[:400]):
                try:
                    raw = base64.b64decode(v + "=" * (-len(v) % 4), altchars=b"-_" if ("-" in v or "_" in v) else None)
                except ValueError:
                    continue
                # accept when the field is declared base64 or the bytes carry a known image signature
                if "b64" in p.lower() or "base64" in p.lower() or sniff_ext(raw, "") != "":
                    out.append(raw)
        if out:
            break
    meta = {}
    for name, p in op.get("result", {}).get("meta_paths", {"revised_prompt": "data[*].revised_prompt"}).items():
        vals = get_path(resp, p)
        if vals:
            meta[name] = vals
    return out, meta


def save_image(data: bytes, out_dir: Path, slug: str, idx: int, canon: dict, profile: dict, opname: str, meta: dict) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    ext = sniff_ext(data, canon.get("output_format") or "png")
    f = out_dir / f"{slug}-{ts}-{idx}.{ext}"
    while f.exists():
        idx += 100
        f = out_dir / f"{slug}-{ts}-{idx}.{ext}"
    f.write_bytes(data)
    side = {k: v for k, v in canon.items() if k not in ("images", "mask")}
    side["images"] = canon.get("images")
    side["mask"] = canon.get("mask")
    sidecar = {"file": f.name, "operation": opname, "profile": profile.get("name"), "request": side,
               "provider_meta": meta, "created": ts, "bytes": len(data)}
    f.with_suffix(".json").write_text(json.dumps(sidecar, indent=2, ensure_ascii=False))
    print(str(f))
    return str(f)


def auto_plan(task: str) -> dict:
    """Ask model_select for the benchmark-best model that a configured provider serves."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import contextlib
    import io
    import model_select as ms
    reg, reg_file = ms.load_registry()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ms.plan(reg, reg_file, task)
    plan = json.loads(buf.getvalue())
    for act in plan.get("actions", []):
        warn(f"{act['action']}: {act['do']}")
    if not plan.get("model"):
        die("no configured provider serves a ranked model - see the CONNECT_PROVIDER action above", 10)
    return plan


def registry_model(model_id: str):
    """The registry entry for a model id or alias, or None."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import model_select as ms
        reg, _ = ms.load_registry()
        return ms.find_model(reg, model_id)
    except Exception:  # noqa: BLE001
        return None


def apply_model_settings(a):
    """Fill quality/complexity from the model's tuned settings.

    Only parameters the model is known to accept are defaulted. For a model without tuned settings nothing is
    added, because many APIs reject fields they do not know; the agent passes --quality from the provider's docs.
    """
    m = registry_model(a.model) or {}
    s = m.get("settings") or {}
    key = ("edit_final" if a.final else "edit") if a.cmd == "edit" else ("final" if a.final else "candidate")
    st = s.get(key) or (s.get("edit") if key == "edit_final" else None) or {}
    if a.quality is None:
        a.quality = st.get("quality") or ("high" if "high" in s.get("quality_values", []) else None)
    if a.complexity is None:
        a.complexity = st.get("complexity") or (("low" if a.cmd == "edit" else "high")
                                                if s.get("complexity_values") else None)
    if a.quality is None:
        warn(f"no tuned settings for model '{a.model}': quality is left to the provider's default. "
             "Pass --quality with the provider's highest value (see the ONBOARD_MODEL action).")
    print(f"settings: model={a.model} profile={a.profile} quality={a.quality} complexity={a.complexity}", file=sys.stderr)


# ----------------------------------------------------------------------------- CLI
def cmd_profiles(_):
    seen = set()
    for d in PROFILE_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            if f.stem in seen or f.stem.startswith("_"):
                continue
            seen.add(f.stem)
            try:
                p = json.loads(f.read_text())
                env = p.get("auth", {}).get("env")
                ok = "key set" if (not env or os.environ.get(env)) else f"needs ${env}"
                print(f"{f.stem:32s} {ok:24s} ops={','.join(p.get('operations', {}))}  {f}")
            except Exception as e:  # noqa: BLE001
                print(f"{f.stem:32s} INVALID JSON: {e}")
    if not seen:
        print("no profiles yet - create one from providers/_TEMPLATE.json (see references/provider-adapters.md)")


def cmd_validate(a):
    p = load_profile(a.profile)
    problems = []
    if not p.get("operations"):
        problems.append("no operations")
    for name, op in p.get("operations", {}).items():
        if not (op.get("url") or p.get("base_url")):
            problems.append(f"{name}: no url/base_url")
        if "prompt" not in op.get("params", {}):
            problems.append(f"{name}: prompt not mapped")
        for k in op.get("params", {}):
            if k not in CANONICAL:
                problems.append(f"{name}: unknown canonical param '{k}' (allowed: {CANONICAL})")
        if op.get("async") and not (op["async"].get("poll_url") or op["async"].get("poll_url_path")):
            problems.append(f"{name}: async without poll_url / poll_url_path")
    env = p.get("auth", {}).get("env")
    if env and not os.environ.get(env):
        problems.append(f"env var {env} not set (needed for live calls)")
    print("OK" if not problems else "\n".join("- " + x for x in problems))
    sys.exit(0 if not problems else 1)


def gather_canon(a, op):
    prompt = Path(a.prompt_file).read_text() if a.prompt_file else (a.prompt or "")
    if not prompt.strip():
        die("empty prompt")
    c = {"prompt": prompt.strip(), "model": a.model, "size": a.size, "quality": a.quality,
         "complexity": a.complexity, "n": a.n, "output_format": a.output_format, "background": a.background,
         "moderation": a.moderation, "seed": a.seed, "negative_prompt": a.negative_prompt,
         "output_compression": a.output_compression, "_set": a.set or []}
    if op == "edit":
        c["images"] = a.image
        c["mask"] = a.mask
    return c


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("profiles")
    v = sub.add_parser("validate")
    v.add_argument("--profile", required=True)
    for name in ("generate", "edit"):
        g = sub.add_parser(name)
        g.add_argument("--profile", default="auto", help="provider profile name/path, or 'auto'")
        g.add_argument("--final", action="store_true", help="use the model's final settings (highest quality) for generate or edit")
        g.add_argument("--model", default="auto", help="canonical model id, or 'auto' = benchmark-best available (model_select.py plan)")
        g.add_argument("--prompt")
        g.add_argument("--prompt-file")
        g.add_argument("--size", default="1536x1024")
        g.add_argument("--quality", help="default: the model's tuned settings; none for a model without tuned settings")
        g.add_argument("--complexity", help="default: the model's tuned settings; only sent to models that support it")
        g.add_argument("--n", type=int, default=1)
        g.add_argument("--output-format")
        g.add_argument("--output-compression", type=int)
        g.add_argument("--background")
        g.add_argument("--moderation")
        g.add_argument("--seed", type=int)
        g.add_argument("--negative-prompt")
        g.add_argument("--set", action="append", help="raw provider field key=value (JSON values allowed)")
        g.add_argument("--out-dir", default="images")
        g.add_argument("--slug", default="img")
        g.add_argument("--dry-run", action="store_true")
        g.add_argument("--verbose", action="store_true")
        if name == "edit":
            g.add_argument("--image", action="append", required=True, help="edit target first, then references")
            g.add_argument("--mask")
    a = ap.parse_args()
    if a.cmd == "profiles":
        return cmd_profiles(a)
    if a.cmd == "validate":
        return cmd_validate(a)
    if a.model == "auto" or a.profile == "auto":
        plan = auto_plan(a.cmd)
        a.model = plan["model"] if a.model == "auto" else a.model
        a.profile = plan["provider_profile"] if a.profile == "auto" else a.profile
        if plan.get("note"):
            warn(plan["note"])
    apply_model_settings(a)
    prof = load_profile(a.profile)
    canon = gather_canon(a, a.cmd)
    files = run_op(prof, a.cmd, canon, Path(a.out_dir), re.sub(r"[^a-z0-9-]+", "-", a.slug.lower()), a.dry_run, a.verbose)
    if files:
        print(json.dumps({"saved": files}))


if __name__ == "__main__":
    main()
