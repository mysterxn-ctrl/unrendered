# Autonomous model selection — how the skill decides by itself

The model is **not** chosen by the person who installed the skill, nor by the agent's opinion. It is chosen by `scripts/model_select.py` from public blind-preference benchmarks, with a fixed statistical rule, separately for two tracks:

| Track | Used for | Primary board (auto-fetched) |
|---|---|---|
| `generate` | new images (text-to-image, with or without inspiration references) | Artificial Analysis Text-to-Image arena — `artificialanalysis.ai/image/leaderboard/text-to-image` |
| `edit` | editing/compositing/retouching existing images | Artificial Analysis Image-Editing arena — `artificialanalysis.ai/image/leaderboard/editing` |

Secondary board for both: LMArena / arena.ai (`/leaderboard/text-to-image`, `/leaderboard/image-edit`). It usually blocks scripted access; it only counts once its rows were added with `ingest`. Without it, rule (b) cannot apply.
Default starting point for both tracks (`models.json → default`): **gpt-image-2.6-sunburst**.

## Pipeline (what `plan` does)

```
plan --task T
 ├─ registry older than refresh_interval_days (14)?  → refresh
 │     ├─ fetch each board (urllib), parse rows (HTML table / rendered text / embedded JSON)
 │     ├─ ≥5 plausible rows → snapshot saved to benchmarks/<source>__<track>__<category>.json
 │     └─ blocked/unparseable → action AGENT_FETCH_LEADERBOARDS (agent reads page, `ingest`)
 ├─ decide (per track)
 │     ├─ board = most photo-specific category available: photorealistic > photography > people > overall
 │     ├─ merge configs per model (keep best, e.g. "(max)")
 │     ├─ new models on the board are auto-added to models.json (onboarded=false)
 │     ├─ SWITCH from current C to top N only if
 │     │     (a) Elo(N) − Elo(C) > CI(N) + CI(C)  and the secondary board is not strongly against, or
 │     │     (b) margin ≥ 25 Elo and the secondary board agrees, or
 │     │     (c) statistical tie, but a recorded local photoreal duel declared N the winner
 │     ├─ otherwise keep C (stability; prompting is tuned per model)
 │     └─ ranking[T] = [selected] + rest by Elo  (+ default appended)
 └─ resolve availability
       ├─ walk ranking[T]; first model that a configured provider serves for operation T wins
       │     (profile model_map / operations.T.model_map / models list / live GET /models probe;
       │      providers whose API-key env var is missing are skipped; tool-type providers count)
       ├─ benchmark-best not reachable → next-best + note "tell the user"
       ├─ winner not onboarded → action ONBOARD_MODEL
       └─ nothing reachable → action CONNECT_PROVIDER
```

All switches are logged in `models.json → history` with reason and evidence URLs.

## Agent duties when the script asks

### AGENT_FETCH_LEADERBOARDS
Some environments block scripted fetching (bot protection, sandbox). Then:
1. Open the listed URLs with your web tools (web fetch / browser). If a board is unavailable, use a mirror that copies it with dates (e.g. `benchmarklist.com/arenas/artificial_analysis_text_to_image/`) — never blog estimates.
2. Look for a category filter; if a **photorealistic / photography / people** category exists, also capture it (separate file with that `category`).
3. Write rows exactly as shown (`model_select.py schema`), ≥5 rows, with 95% CI half-width.
4. `python3 scripts/model_select.py ingest file1.json [file2.json …]` → it decides and saves.

### ONBOARD_MODEL
A model that just won (or a fallback) has no tuned settings. Read the vendor's **official** API reference and prompting guide; fill in `models.json`: `capabilities`, `settings.candidate/final/edit/edit_final` (the top quality values the vendor offers), `prompt_dialect` (natural language vs tags, negative prompt support, ideal length), `known_weaknesses`, `aliases` (names used by providers/leaderboards), `onboarded: true`. Then run 3 calibration briefs (portrait, street scene, product) through the normal QA loop and append weaknesses you observe.

### Ties → optional local photoreal duel
When `decide` reports a statistical tie and both models are reachable, the skill may settle it on **photorealism specifically** (the arenas measure general preference):
1. Pick 3 briefs from `prompt-compiler.md` (or 3 user-relevant ones), same size and top settings for both models.
2. Score every image blind-ish with `qa-rubric.md` (don't look at which model made it before scoring; use the contact sheet).
3. `python3 scripts/model_select.py duel --track <generate|edit> --pair A B --winner A --scores '{"A": 8.9, "B": 8.3}'`
   - differences < 0.3 points are recorded as no winner.
Duels only break ties; they never override a statistically separated benchmark lead.

## Commands
```
model_select.py status                 # selections, age, due?
model_select.py plan --task generate   # the entry point (JSON)
model_select.py refresh [--force]      # fetch + decide now
model_select.py ingest FILE...         # agent-gathered rows
model_select.py decide                 # re-run the rule
model_select.py duel ...               # record tie-break
model_select.py schema                 # ingest format
```
Registry location: `~/.config/unrendered/models.json` if present (user-writable, survives skill updates), else the skill's `models.json`. Snapshots live next to it in `benchmarks/`.

