#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ruben Ferraro — Unrendered (https://github.com/mysterxn-ctrl/unrendered)
"""Autonomous, benchmark-based model selection + availability resolution (stdlib only).

The skill - not a human - decides which image model to use. Decisions are made by code from
public blind-preference leaderboards, separately for each task track:
    generate  (text-to-image)        edit  (image editing)
Default starting point for both tracks: gpt-image-2.6-sunburst (models.json -> default).

Commands
  status                       registry age, selections, whether a refresh is due
  refresh [--force]            fetch leaderboards automatically, ingest, decide
  ingest FILE.json [...]       ingest leaderboard rows gathered by the agent (fallback when
                               auto-fetch is blocked) - schema printed by `schema`
  decide                       (re)apply the decision rule to ingested data
  plan --task generate|edit    THE ENTRY POINT: refresh if due, decide, then pick the best-ranked
                               model that a configured provider can actually serve; prints JSON
  schema                       print the ingest JSON schema
Exit codes: 0 ok, 10 agent action required (see "action" in output), 2 error.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
# User state survives skill/plugin updates. Override with UNRENDERED_HOME (maintainers point it at the
# skill folder to refresh the bundled seed data).
STATE_DIR = Path(os.environ.get("UNRENDERED_HOME") or Path.home() / ".config" / "unrendered").expanduser()
USER_DIR = STATE_DIR
PROFILE_DIRS = [STATE_DIR / "providers", SKILL_DIR / "providers"]
TRACKS = ("generate", "edit")
TODAY = dt.date.today().isoformat()

# Leaderboards the code reads itself. Primary = Artificial Analysis (blind arena, Elo + 95% CI).
# Secondary = LMArena/arena.ai (often blocks bots -> agent may ingest it manually).
SOURCES = [
    {"source": "artificial_analysis", "track": "generate", "category": "overall", "rank": "primary",
     "urls": ["https://artificialanalysis.ai/image/leaderboard/text-to-image",
              "https://artificialanalysis.ai/embed/text-to-image-leaderboard/leaderboard/text-to-image"]},
    {"source": "artificial_analysis", "track": "edit", "category": "overall", "rank": "primary",
     "urls": ["https://artificialanalysis.ai/image/leaderboard/editing"]},
    {"source": "lmarena", "track": "generate", "category": "overall", "rank": "secondary",
     "urls": ["https://arena.ai/leaderboard/text-to-image", "https://lmarena.ai/leaderboard/text-to-image"]},
    {"source": "lmarena", "track": "edit", "category": "overall", "rank": "secondary",
     "urls": ["https://arena.ai/leaderboard/image-edit", "https://lmarena.ai/leaderboard/image-edit"]},
]
# A photorealism-specific category, when a source offers one, outranks "overall" for this skill.
CATEGORY_PRIORITY = ["photorealistic", "photography", "people", "overall"]
MIN_ROWS = 5


# ----------------------------------------------------------------------------- registry io
def _freshness(reg: dict) -> str:
    return max(reg.get("last_checked", ""), reg.get("last_decided", ""))


def load_registry():
    """Newest of (bundled seed, user state) wins; user-only knowledge (onboarded models, duels) is merged in.

    Always returns the *user* registry path as the save target, so updates never touch the skill folder.
    """
    bundled_p, user_p = SKILL_DIR / "models.json", STATE_DIR / "models.json"
    bundled = json.loads(bundled_p.read_text())
    if not user_p.exists() or user_p.resolve() == bundled_p.resolve():
        return bundled, user_p
    user = json.loads(user_p.read_text())
    base, other = (user, bundled) if _freshness(user) >= _freshness(bundled) else (bundled, user)
    ids = {m["id"] for m in base["models"]}
    for m in other["models"]:
        if m["id"] not in ids:
            base["models"].append(m)
        elif m.get("onboarded") and not next(x for x in base["models"] if x["id"] == m["id"]).get("onboarded"):
            base["models"] = [m if x["id"] == m["id"] else x for x in base["models"]]
    for k in ("duels",):
        if other.get(k) and not base.get(k):
            base[k] = other[k]
    return base, user_p


def save_registry(reg: dict, p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n")
    return p


def bench_dir(_reg_file: Path = None) -> Path:
    d = STATE_DIR / "benchmarks"
    d.mkdir(parents=True, exist_ok=True)
    return d


# ----------------------------------------------------------------------------- names
def slug(name: str) -> str:
    s = name.lower()
    s = re.sub(r"\([^)]*\)", " ", s)                      # drop "(max)" etc.
    s = re.sub(r"^(openai|google|microsoft|black forest labs|bfl|xai|spacexai|klingai|bytedance)[\s:/_-]+", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def config_of(name: str) -> str:
    m = re.search(r"\(([^)]*)\)", name)
    return m.group(1).strip().lower() if m else ""


def model_keys(m: dict) -> set:
    keys = {slug(m["id"])}
    keys |= {slug(a) for a in m.get("aliases", [])}
    return keys


def find_model(reg: dict, name: str):
    s = slug(name)
    for m in reg["models"]:
        if s in model_keys(m):
            return m
    return None


# ----------------------------------------------------------------------------- parsing
def strip_html(raw: str) -> str:
    raw = raw.replace('\\"', '"').replace("\\n", "\n")
    raw = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", lambda m: m.group(0) if "elo" in m.group(0).lower() else " ", raw)
    txt = re.sub(r"(?s)<[^>]+>", "\n", raw)
    txt = html.unescape(txt)
    return re.sub(r"[ \t\r\f\v]+", " ", txt)


ROW_RES = [
    # "GPT Image 2.6 Sunburst (max)\n1261±1495% interval 1247 to 1275"
    re.compile(r"(?P<name>[A-Za-z][A-Za-z0-9 .:+_/\-]{2,60}(?:\([^)\n]{1,20}\))?)\s*\n+\s*(?P<elo>\d{3,4})\s*±\s*\d*[^\n]{0,30}?interval\s*(?P<lo>\d{3,4})\s*(?:to|-|–)\s*(?P<hi>\d{3,4})"),
    # "Name\n1261 ±14"   (CI not glued to following digits)
    re.compile(r"(?P<name>[A-Za-z][A-Za-z0-9 .:+_/\-]{2,60}(?:\([^)\n]{1,20}\))?)\s*\n+\s*(?P<elo>\d{3,4})\s*±\s*(?P<ci>\d{1,2})(?!\d)"),
    # markdown/HTML table: "| 1 | Name | Vendor | 1261 | ..."  or with "±14"
    re.compile(r"\|\s*\d+\s*\|\s*(?P<name>[^|\n]{3,60}?)\s*\|\s*(?P<vendor>[^|\n]{1,40}?)\s*\|\s*(?P<elo>\d{3,4})(?:\s*±\s*(?P<ci>\d{1,2}))?\s*\|"),
    # JSON-ish: "name":"X", ... "elo":1261 ... "ci":14
    re.compile(r'"(?:name|model|model_name|modelName)"\s*:\s*"(?P<name>[^"]{3,80})"[^{}]{0,600}?"(?:elo|score|rating)"\s*:\s*(?P<elo>\d{3,4}(?:\.\d+)?)(?:[^{}]{0,200}?"(?:ci|ci95|confidence_interval|ciWidth)"\s*:\s*(?P<ci>\d{1,2}(?:\.\d+)?))?'),
]


def parse_rows(raw: str):
    text = strip_html(raw) if "<" in raw[:2000] else raw
    best = []
    for rx in ROW_RES:
        rows, seen = [], set()
        for m in rx.finditer(text):
            name = m.group("name").strip(" |-:")
            if not re.search(r"[A-Za-z]{2}", name) or name.lower() in ("model", "rank", "elo"):
                continue
            elo = float(m.group("elo"))
            if not 600 <= elo <= 2500:
                continue
            gd = m.groupdict()
            if gd.get("lo") and gd.get("hi"):
                ci = (float(gd["hi"]) - float(gd["lo"])) / 2
            elif gd.get("ci"):
                ci = float(gd["ci"])
            else:
                ci = None
            if name in seen:
                continue
            seen.add(name)
            rows.append({"name": name, "elo": elo, "ci": ci, "vendor": (gd.get("vendor") or "").strip() or None})
        if len(rows) > len(best):
            best = rows
    return best


def fetch(url: str, timeout=40) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; unrendered/1.0)",
                                               "Accept": "text/html,application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


# ----------------------------------------------------------------------------- snapshots
def snapshot_name(s):
    return f"{s['source']}__{s['track']}__{s.get('category', 'overall')}.json"


def store_snapshot(reg_file: Path, snap: dict):
    if len(snap.get("rows", [])) < MIN_ROWS:
        raise ValueError(f"snapshot {snapshot_name(snap)} has only {len(snap.get('rows', []))} rows (<{MIN_ROWS})")
    for r in snap["rows"]:
        if "name" not in r or "elo" not in r:
            raise ValueError("each row needs name and elo")
    snap.setdefault("category", "overall")
    snap.setdefault("fetched", TODAY)
    (bench_dir(reg_file) / snapshot_name(snap)).write_text(json.dumps(snap, indent=2, ensure_ascii=False))


def load_snapshots(_reg_file: Path = None):
    """Bundled seed snapshots + user snapshots; for the same board the most recently fetched wins."""
    best = {}
    for d in (SKILL_DIR / "benchmarks", STATE_DIR / "benchmarks"):
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            try:
                snap = json.loads(f.read_text())
            except Exception:  # noqa: BLE001
                continue
            if f.name not in best or snap.get("fetched", "") >= best[f.name].get("fetched", ""):
                best[f.name] = snap
    return list(best.values())


# ----------------------------------------------------------------------------- decision
def merge_configs(rows):
    """Keep the best configuration per model (e.g. '(max)' over '(high)')."""
    best = {}
    for r in rows:
        k = slug(r["name"])
        if k not in best or r["elo"] > best[k]["elo"]:
            best[k] = dict(r, key=k, config=config_of(r["name"]))
    return sorted(best.values(), key=lambda r: -r["elo"])


def pick_board(snaps, track, rank):
    pri = [s for s in snaps if s["track"] == track and
           (s.get("rank") == rank or (rank == "primary" and s["source"] == "artificial_analysis")
            or (rank == "secondary" and s["source"] == "lmarena"))]
    for cat in CATEGORY_PRIORITY:
        for s in pri:
            if s.get("category", "overall").lower() == cat:
                return s
    return pri[0] if pri else None


def upsert_model(reg, row, track, source, category, date):
    m = find_model(reg, row["name"])
    if not m:
        m = {"id": row["key"], "aliases": [re.sub(r"\s*\([^)]*\)", "", row["name"]).strip()],
             "vendor": row.get("vendor"), "onboarded": False, "benchmarks": {},
             "note": "auto-added from leaderboard; needs onboarding (settings, dialect, capabilities) before first use"}
        reg["models"].append(m)
    key = f"{source}_{track}_{category}"
    m.setdefault("benchmarks", {})[key] = {"elo": row["elo"], "ci95": row.get("ci"), "config": row.get("config"),
                                          "rank": row.get("rank"), "date": date}
    return m


def decide(reg: dict, reg_file: Path, verbose=True):
    snaps = load_snapshots(reg_file)
    log = []
    for track in TRACKS:
        prim = pick_board(snaps, track, "primary")
        sec = pick_board(snaps, track, "secondary")
        current_id = reg["selected"].get(track) or reg["default"][track]
        if not prim:
            log.append(f"[{track}] no primary leaderboard data -> keep {current_id}")
            continue
        rows = merge_configs(prim["rows"])
        for i, r in enumerate(rows, 1):
            r["rank"] = i
            upsert_model(reg, r, track, prim["source"], prim.get("category", "overall"), prim.get("fetched", TODAY))
        srows = merge_configs(sec["rows"]) if sec else []
        for i, r in enumerate(srows, 1):
            r["rank"] = i
            upsert_model(reg, r, track, sec["source"], sec.get("category", "overall"), sec.get("fetched", TODAY))

        cur_m = next(m for m in reg["models"] if m["id"] == current_id) if any(m["id"] == current_id for m in reg["models"]) else None
        cur_row = next((r for r in rows if cur_m and r["key"] in model_keys(cur_m)), None)
        top = rows[0]
        top_m = find_model(reg, top["name"])
        reason = None
        if cur_row is None:
            new_id, reason = top_m["id"], f"current {current_id} not on primary board -> top model"
        elif top_m["id"] == current_id:
            new_id, reason = current_id, f"current is #1 ({top['elo']:.0f}±{top.get('ci') or '?'})"
        else:
            margin = top["elo"] - cur_row["elo"]
            ci_sum = (top.get("ci") or 15) + (cur_row.get("ci") or 15)
            sec_top = next((r for r in srows if r["key"] in model_keys(top_m)), None)
            sec_cur = next((r for r in srows if cur_m and r["key"] in model_keys(cur_m)), None)
            sec_agrees = bool(sec_top and sec_cur and sec_top["elo"] > sec_cur["elo"])
            sec_strongly_against = bool(sec_top and sec_cur and sec_cur["elo"] - sec_top["elo"] >
                                        (sec_cur.get("ci") or 10) + (sec_top.get("ci") or 10))
            duel = reg.get("duels", {}).get(track, {})
            duel_winner = duel.get("winner") if duel.get("pair") and set(duel["pair"]) == {top_m["id"], current_id} else None
            if margin > ci_sum and not sec_strongly_against:
                new_id, reason = top_m["id"], f"{top_m['id']} leads by {margin:.0f} Elo > combined CI {ci_sum:.0f}"
            elif margin >= 25 and sec_agrees:
                new_id, reason = top_m["id"], f"{top_m['id']} leads by {margin:.0f} Elo and secondary board agrees"
            elif duel_winner:
                new_id, reason = duel_winner, f"statistical tie ({margin:.0f} Elo < CI {ci_sum:.0f}) broken by local photoreal duel"
            else:
                new_id, reason = current_id, (f"{top_m['id']} ahead by only {margin:.0f} Elo "
                                              f"(combined CI {ci_sum:.0f}) = statistical tie; optional tie-break: local photoreal duel")
        changed = new_id != current_id
        reg["selected"][track] = new_id
        # ranking used for availability fallback: selected first, then by primary Elo
        order = [new_id] + [find_model(reg, r["name"])["id"] for r in rows if find_model(reg, r["name"])["id"] != new_id]
        reg.setdefault("ranking", {})[track] = order[:25]
        log.append(f"[{track}] {'SWITCH ' + current_id + ' -> ' + new_id if changed else 'keep ' + new_id}: {reason}")
        if changed:
            reg.setdefault("history", []).append({"date": TODAY, "track": track, "event": "switch", "from": current_id,
                                                  "to": new_id, "reason": reason,
                                                  "evidence": [u for s in (prim, sec) if s for u in [s.get("url")] if u]})
    reg["last_decided"] = TODAY
    if verbose:
        print("\n".join(log))
    return log


# ----------------------------------------------------------------------------- refresh
def refresh(reg, reg_file, force=False):
    fetched, failed = [], []
    for src in SOURCES:
        ok = False
        for url in src["urls"]:
            try:
                rows = parse_rows(fetch(url))
                if len(rows) >= MIN_ROWS:
                    store_snapshot(reg_file, {"source": src["source"], "track": src["track"], "category": src["category"],
                                              "rank": src["rank"], "url": url, "fetched": TODAY, "rows": rows})
                    fetched.append(f"{src['source']}/{src['track']}: {len(rows)} rows from {url}")
                    ok = True
                    break
            except Exception as e:  # noqa: BLE001
                last = f"{type(e).__name__}: {str(e)[:120]}"
                continue
        if not ok:
            failed.append({"source": src["source"], "track": src["track"], "rank": src["rank"], "urls": src["urls"]})
    primary_ok = {f.split(":")[0] for f in fetched if f.startswith("artificial_analysis")}
    reg["last_checked"] = TODAY if primary_ok else reg.get("last_checked")
    return fetched, failed


def is_due(reg) -> bool:
    last = dt.date.fromisoformat(reg.get("last_checked", "1970-01-01"))
    return (dt.date.today() - last).days > reg.get("refresh_interval_days", 14)


# ----------------------------------------------------------------------------- providers
def load_profiles():
    seen, out = set(), []
    for d in PROFILE_DIRS:
        if not d.exists():
            continue
        for f in sorted(d.glob("*.json")):
            if f.stem.startswith("_") or f.stem in seen:
                continue
            seen.add(f.stem)
            try:
                p = json.loads(f.read_text())
                p["_file"] = str(f)
                out.append(p)
            except Exception:  # noqa: BLE001
                pass
    return out


def profile_serves(p: dict, model: dict, task: str):
    """Return (serves: True/False/None, wire_id). None = unknown (wildcard profile)."""
    if p.get("disabled"):
        return False, None
    env = p.get("auth", {}).get("env")
    if env and not os.environ.get(env) and not p.get("auth", {}).get("optional"):
        return False, None
    op = p.get("operations", {}).get(task) if p.get("type") != "tool" else p.get("operations", {}).get(task, {})
    if op is None:
        return False, None
    keys = model_keys(model)
    maps = dict(p.get("model_map", {}))
    maps.update(op.get("model_map", {}) if isinstance(op, dict) else {})
    for canon, wire in maps.items():
        if slug(canon) in keys:
            return True, wire
    served = (op.get("models") if isinstance(op, dict) else None) or p.get("models") or []
    for s in served:
        if s == "*":
            continue
        if slug(s) in keys:
            return True, s
    cache = p.get("_live_models")
    if cache:
        for s in cache:
            if slug(s) in keys or any(k in slug(s) for k in keys):
                return True, s
        return False, None
    if "*" in served or p.get("serves_any_model"):
        return None, model["id"]
    return False, None


def probe_models(p: dict):
    """Use the profile's optional list_models operation (e.g. GET /models) to learn what it serves."""
    lm = p.get("list_models")
    if not lm:
        return None
    base = re.sub(r"\$\{([A-Z0-9_]+)\}", lambda m: os.environ.get(m.group(1), ""), p.get("base_url", "")).rstrip("/")
    url = lm.get("url") or base + lm.get("path", "/models")
    headers = {"User-Agent": "unrendered/1.0"}
    a = p.get("auth", {})
    key = os.environ.get(a.get("env", ""), "")
    if a.get("type", "header") == "header" and key:
        headers[a.get("header", "Authorization")] = a.get("prefix", "Bearer ") + key
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
            data = json.loads(r.read().decode())
    except Exception:  # noqa: BLE001
        return None
    path = lm.get("ids_path", "data[*].id")
    vals = [data]
    for t in re.findall(r"[^.\[\]]+|\[\*\]", path):
        nxt = []
        for v in vals:
            if t == "[*]" and isinstance(v, list):
                nxt += v
            elif isinstance(v, dict) and t in v:
                nxt.append(v[t])
        vals = nxt
    return [v for v in vals if isinstance(v, str)]


def plan(reg, reg_file, task, probe=True):
    actions = []
    if is_due(reg):
        fetched, failed = refresh(reg, reg_file)
        if failed:
            prim_failed = [f for f in failed if f["rank"] == "primary"]
            if prim_failed:
                actions.append({"action": "AGENT_FETCH_LEADERBOARDS",
                                "why": "auto-fetch of primary leaderboards failed/blocked in this environment",
                                "do": "Read these pages with your web tools, write the rows to a JSON file per `model_select.py schema`, "
                                      "then run `model_select.py ingest FILE` and re-run plan. If web access is impossible, continue "
                                      "with the current selection and tell the user the benchmark check could not run.",
                                "targets": prim_failed})
        decide(reg, reg_file, verbose=False)
        reg_file = save_registry(reg, reg_file)
    ranking = reg.get("ranking", {}).get(task) or [reg["selected"].get(task) or reg["default"][task]]
    if reg["default"][task] not in ranking:
        ranking.append(reg["default"][task])
    profiles = load_profiles()
    if probe:
        for p in profiles:
            live = probe_models(p)
            if live:
                p["_live_models"] = live
    chosen, unknown = None, []
    for mid in ranking:
        m = next((x for x in reg["models"] if x["id"] == mid), None)
        if not m:
            continue
        for p in profiles:
            serves, wire = profile_serves(p, m, task)
            if serves:
                chosen = (m, p, wire)
                break
            if serves is None:
                unknown.append((m, p, wire))
        if chosen:
            break
    best = ranking[0]
    result = {"task": task, "benchmark_best": best, "selected_by_policy": reg["selected"].get(task),
              "default": reg["default"][task], "ranking": ranking[:8], "registry": str(reg_file)}
    if not chosen and unknown:
        m, p, wire = unknown[0]
        result["action_hint"] = (f"profile '{p['name']}' may serve any model; verify that it serves {m['id']} "
                                 f"(provider docs or model list). Using it optimistically.")
        chosen = (m, p, wire)
    if chosen:
        m, p, wire = chosen
        s = m.get("settings", {})
        result.update({"model": m["id"], "provider_profile": p.get("name"), "provider_type": p.get("type", "http"),
                       "wire_model": wire,
                       "settings": {"candidate": s.get("candidate"), "final": s.get("final"), "edit": s.get("edit"),
                                    "edit_final": s.get("edit_final") or s.get("edit")},
                       "prompt_dialect": m.get("prompt_dialect"), "known_weaknesses": m.get("known_weaknesses", [])})
        if p.get("type") == "tool":
            result["tool"] = p.get("tool")
        if m["id"] != best:
            result["note"] = f"benchmark-best '{best}' is not available via configured providers; using next-best '{m['id']}'. Tell the user."
        if not m.get("onboarded", True):
            actions.append({"action": "ONBOARD_MODEL", "model": m["id"],
                            "do": "Read the vendor's official API + prompting docs for this model; fill capabilities, settings "
                                  "(candidate/final/edit: highest quality values), prompt_dialect, known_weaknesses in models.json; "
                                  "set onboarded=true. Until then use the provider's highest quality setting."})
    else:
        actions.append({"action": "CONNECT_PROVIDER",
                        "do": f"No configured provider serves any of {ranking[:5]} for '{task}'. Follow references/provider-adapters.md: "
                              "find the user's API/tool that offers the top-ranked model and create a profile (with model_map or models list). "
                              "If none exists, ask the user which API to connect."})
    if actions:
        result["actions"] = actions
    save_registry(reg, reg_file)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 10 if any(a["action"] in ("CONNECT_PROVIDER", "AGENT_FETCH_LEADERBOARDS") for a in actions) else 0


SCHEMA = {
    "source": "artificial_analysis | lmarena | <other arena>",
    "track": "generate | edit",
    "category": "overall | photorealistic | photography | people (use the most photo-specific category the board offers)",
    "rank": "primary (artificial_analysis) | secondary (lmarena)",
    "url": "page the rows were read from",
    "fetched": "YYYY-MM-DD",
    "rows": [{"name": "GPT Image 2.6 Sunburst (max)", "elo": 1261, "ci": 14, "vendor": "OpenAI"}],
    "_rules": "copy names exactly as listed (config in parentheses is fine); ci = half-width of the 95% interval; >= 5 rows; numbers only from the page, never estimated",
}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    r = sub.add_parser("refresh")
    r.add_argument("--force", action="store_true")
    i = sub.add_parser("ingest")
    i.add_argument("files", nargs="+")
    sub.add_parser("decide")
    pl = sub.add_parser("plan")
    pl.add_argument("--task", choices=TRACKS, default="generate")
    pl.add_argument("--no-probe", action="store_true")
    sub.add_parser("schema")
    du = sub.add_parser("duel", help="record a local photoreal duel result (tie-breaker only)")
    du.add_argument("--track", choices=TRACKS, required=True)
    du.add_argument("--pair", nargs=2, required=True, metavar=("MODEL_A", "MODEL_B"))
    du.add_argument("--winner", required=True)
    du.add_argument("--scores", required=True, help='JSON, e.g. {"model-a": 8.9, "model-b": 8.4} (mean rubric score over >= 3 briefs)')
    a = ap.parse_args()
    reg, reg_file = load_registry()

    if a.cmd == "schema":
        print(json.dumps(SCHEMA, indent=2))
    elif a.cmd == "status":
        print(f"registry: {reg_file}\nlast_checked: {reg.get('last_checked')}  due: {is_due(reg)}")
        for t in TRACKS:
            print(f"{t}: selected={reg['selected'].get(t)} default={reg['default'][t]} ranking={reg.get('ranking', {}).get(t, [])[:5]}")
        sys.exit(10 if is_due(reg) else 0)
    elif a.cmd == "refresh":
        fetched, failed = refresh(reg, reg_file, a.force)
        print("fetched:\n  " + "\n  ".join(fetched or ["(none)"]))
        if failed:
            print("FAILED (agent should read these pages and `ingest`):")
            for f in failed:
                print(f"  {f['source']}/{f['track']} ({f['rank']}): {f['urls'][0]}")
        decide(reg, reg_file)
        save_registry(reg, reg_file)
        sys.exit(10 if any(f["rank"] == "primary" for f in failed) else 0)
    elif a.cmd == "ingest":
        got_primary = False
        for f in a.files:
            snap = json.loads(Path(f).read_text())
            for s in (snap if isinstance(snap, list) else [snap]):
                store_snapshot(reg_file, s)
                got_primary |= s.get("rank", "primary") == "primary"
                print(f"ingested {snapshot_name(s)} ({len(s['rows'])} rows)")
        if got_primary:
            reg["last_checked"] = TODAY
        decide(reg, reg_file)
        save_registry(reg, reg_file)
    elif a.cmd == "decide":
        decide(reg, reg_file)
        save_registry(reg, reg_file)
    elif a.cmd == "duel":
        if a.winner not in a.pair:
            sys.exit("winner must be one of --pair")
        scores = json.loads(a.scores)
        if abs(scores.get(a.pair[0], 0) - scores.get(a.pair[1], 0)) < 0.3:
            print("difference < 0.3 rubric points: recorded as no winner (keep current)")
            a.winner = None
        reg.setdefault("duels", {})[a.track] = {"pair": a.pair, "winner": a.winner, "scores": scores, "date": TODAY}
        decide(reg, reg_file)
        save_registry(reg, reg_file)
    elif a.cmd == "plan":
        sys.exit(plan(reg, reg_file, a.task, probe=not a.no_probe))


if __name__ == "__main__":
    main()
