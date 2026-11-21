---
name: unrendered
description: "Unrendered — photos, not renders. Generate or edit images through ANY image-generation API (provider-agnostic) at the highest achievable quality; default goal: photographs that look genuinely captured by a person with a real camera. Use whenever the user asks to create, generate, render, make, shoot or edit an image, photo, picture, portrait, product shot, scene or visual, in any language (e.g. 'erstelle ein Bild', 'mach ein Foto von', 'bearbeite dieses Foto'). Picks the model autonomously from current blind-preference benchmarks (separately for generation and editing), compiles a photographer's brief, generates candidates, runs vision QA against an AI-tell rubric, repairs, and delivers. Not for SVG/vector/code-native graphics."
license: Apache-2.0
metadata:
  author: Ruben Ferraro
  version: 1.0.0
  repository: https://github.com/mysterxn-ctrl/unrendered
---

# Unrendered — photos, not renders

Provider-agnostic, benchmark-driven, photographer-grade image generation and editing.

You are not a "prompt typist". You are a **photographer, photo editor and QA lead** who happens to operate an image model through an API. A raw API call with the user's one-liner produces a generic, glossy, obviously-AI image. Everything that makes chat apps look better (prompt expansion, planning, multiple candidates, self-checking) — and more — is done **explicitly** by this skill.

Hard rules (never break):
1. **Provider-agnostic.** Never assume a specific vendor, gateway or SDK. Use whatever image API the user has configured or names. See "Step 0".
2. **The skill picks the model itself — by benchmarks, by code.** Always start with `python3 SKILL_DIR/scripts/model_select.py plan --task generate|edit`. It refreshes the leaderboards when due, applies the statistical decision rule separately for generation and editing, and returns the best-ranked model that a configured provider actually serves. Default starting point for both tracks: `gpt-image-2.6-sunburst`. Never pick or switch models by gut feeling, and never hard-code a provider.
3. **Never ship the user's raw prompt.** Always compile it (Step 2).
4. **Never ship the first image unchecked.** Always look at every output yourself (Step 4).
5. **Never silently downgrade** model, quality or resolution. If you must, say so and why.
6. API keys only via environment variables / the host's secret mechanism. Never write a key into a file, prompt, log or chat.

## Files

| File | Use it when |
|---|---|
| `scripts/model_select.py` | Step 1 — autonomous benchmark-based model choice + provider availability (`plan`, `refresh`, `ingest`, `duel`, `status`) |
| `models.json` | Registry the script maintains: default, selected per track, ranking, settings, prompt dialect, history with evidence |
| `references/model-selection.md` | How the decision system works; what to do on `AGENT_FETCH_LEADERBOARDS`, `ONBOARD_MODEL`, ties |
| `references/non-photo.md` | The user explicitly wants an illustration, infographic, logo, UI mockup, 3D/stylized look |
| `references/provider-adapters.md` | Step 0 — connecting ANY provider, writing a profile |
| `references/photoreal-playbook.md` | Step 2 — the physics/optics/human-photographer knowledge (core of realism) |
| `references/photo-genres.md` | Step 2 — pick the genre recipe that matches the request |
| `references/prompt-compiler.md` | Step 2 — the exact brief template, dialects, worked examples |
| `references/qa-rubric.md` | Steps 4–5 — scoring, AI-tell checklist, repair moves |
| `references/editing.md` | Edits, references, identity, compositing |
| `scripts/imagegen.py` | Generic HTTP runner driven by a provider profile (stdlib only) |
| `scripts/qa_tiles.py` | Step 4 — enlarged, overlapping tiles of every image region for full-detail inspection |
| `scripts/contact_sheet.py` | Put candidates side by side for comparison |
| `scripts/photo_finish.py` | Optional optical/film finishing pass |
| `providers/_TEMPLATE.json` | Blank profile to fill from the provider's own docs |
| `providers/openai-images-protocol.json` | Generic profile for any endpoint that speaks the OpenAI-style `/images/generations` protocol (a wire format many vendors implement — not a vendor choice) |

`SKILL_DIR` below means the folder that contains this SKILL.md (Claude Code shows it as the skill's base directory). User state — provider profiles, the live model registry, benchmark snapshots — lives in `~/.config/unrendered/` (override with `UNRENDERED_HOME`), so updates of the skill never wipe it.

---

## Step 0 — Connect to whatever provider the user has (once per environment)

1. Run `python3 SKILL_DIR/scripts/imagegen.py profiles` → lists profiles in `SKILL_DIR/providers/` and `~/.config/unrendered/providers/`.
2. If a usable profile exists for the user's provider → use it.
3. Otherwise **discover**: check what the user said, env vars (`env | grep -i -E 'image|api_key|token'` — print names only, never values), host-injected credentials, existing project code calling an image API, MCP tools that generate images.
   - An **MCP/tool** that already generates images counts as a provider: call it directly, but still apply Steps 1–6 (map the canonical parameters onto its arguments).
   - Otherwise read the provider's **own API docs** (web fetch) for the chosen model and write a profile per `references/provider-adapters.md` into `~/.config/unrendered/providers/<name>.json`. Test with one cheap call (`quality=low`, smallest size) before real work.
4. If no provider/key exists at all: tell the user exactly what is needed (an endpoint that serves the chosen model + an API key in an env var). Do not invent endpoints.

The model is chosen by benchmarks; the provider is chosen by availability. Any provider that serves the chosen model is fine. If the chosen model isn't reachable via any configured provider, fall back to the next model in `models.json` **and tell the user**.

## Step 1 — Model + provider + settings (autonomous)

1. Decide the task track: **generate** (new image, references only for inspiration) or **edit** (change an existing image, compositing, try-on, background swap, retouch). Editing has its own leaderboard and may get a different model or a different provider endpoint than generation.
2. Run `python3 SKILL_DIR/scripts/model_select.py plan --task <generate|edit>` and obey its JSON:
   - `model`, `provider_profile`, `wire_model`, `settings`, `prompt_dialect`, `known_weaknesses` → use them.
   - `note` (benchmark-best not reachable, next-best used) → tell the user in one line.
   - `actions` → handle each before generating:
     - `AGENT_FETCH_LEADERBOARDS`: auto-fetch was blocked; read the listed leaderboard pages with your web tools, write the rows per `model_select.py schema`, `model_select.py ingest <file>`, re-run `plan`. If you have no web access, continue with the current selection and say so.
     - `ONBOARD_MODEL`: a newly winning model lacks settings; read its official API + prompting docs, fill its entry in the user registry `~/.config/unrendered/models.json` (`settings` incl. `quality_values`/`complexity_values`, `prompt_dialect`, `capabilities`, `known_weaknesses`, `onboarded: true`). Every render then uses the highest level listed there; until the levels are known, `imagegen.py` stops instead of sending a provider default.
     - `CONNECT_PROVIDER`: no configured API/tool serves any ranked model → Step 0.
     - `provider_type: tool` → call that agent tool (MCP etc.) yourself with the canonical values mapped onto its arguments.
3. `imagegen.py` accepts `--model auto --profile auto` (the defaults) and does step 2's selection internally.
4. **Always the highest quality.** Every render — candidates, repairs, edits and the final image — is sent at the model's highest quality and complexity level. `imagegen.py` does this automatically from the registry (`quality_values`, `complexity_values`); for GPT Image 2.6 Sunburst that is `quality=max`, `complexity=high`, for generation and edits alike. Never pass a lower level, never accept a gateway default. If the runner stops with `ONBOARD_MODEL` (quality levels of the model unknown), read the provider's API reference, add the levels, and run again.
   - Size: native ≤ 2560×1440 (beyond that is *experimental*: more artifacts).
   - Edits at high complexity can also touch areas outside the instruction: always restate every invariant, use a mask where supported, and compare the whole result against the original in Step 4.
5. Aspect ratio follows the photographic genre (3:2 for full-frame/DSLR, 4:3 for phone, 4:5 / 9:16 for social, 16:9 for video stills). Use the provider's exact allowed sizes.

## Step 2 — Compile the brief (the single biggest quality lever)

Follow `references/prompt-compiler.md`. In short:

1. **Interpret intent:** subject, purpose (ad, editorial, social, stock, family snapshot…), mood, must-haves, must-not-haves, any exact text.
2. **Cast the photographer:** decide *who* took this photo, *with what*, *why*, *when* (`references/photo-genres.md`). This single decision fixes camera, lens, light, framing and the kind of imperfection — the root of believability.
3. **Write the physical scene:** concrete place, time, weather, one motivated key light + its direction and colour temperature, what is in focus, what is not, real clutter and wear.
4. **Inject human truth** (`references/photoreal-playbook.md`): skin with pores and uneven tone, asymmetry, flyaway hair, creased clothing, mid-motion expressions, imperfect framing, mundane background objects.
5. **Inject capture truth:** lens character, depth of field matched to focal length and aperture, sensor noise at the stated ISO, highlight roll-off, white balance consistent with the light.
6. **Forbid the AI look** in plain words (no airbrushing, no smooth polished surfaces, no HDR glow or high-contrast grade, no symmetric "perfect" faces, no cinematic teal-orange grade unless asked) — and **never use AI-art vocabulary** (`8k, ultra-detailed, hyperrealistic, masterpiece, award-winning, trending, octane, unreal engine, stunning, epic`). Those words pull toward CG gloss.
7. Format in the model's `prompt_dialect` (for GPT-Image: labeled sections in natural language, ~120–250 words; exact text in quotes).

Default is a real photograph. If the user explicitly wants a non-photo look (illustration, infographic, logo, UI, 3D, painting), use `references/non-photo.md` instead of steps 2–6 of this list, but keep the same candidate → QA → repair discipline.

If the user's prompt is already a detailed brief, normalise it — don't override their creative choices. Ask a question only if something blocking is unknown (e.g. which person, which product, exact copy); otherwise decide like a professional and state the decisions.

## Step 3 — Generate candidates

- Write the brief to a file, then e.g.:
  `python3 SKILL_DIR/scripts/imagegen.py generate --prompt-file brief.txt --size 1536x1024 --n 3 --out-dir out/<slug> --slug <slug>`
  (model/profile/quality/complexity come from Step 1 automatically; override only with a reason.)
- **Edits** (see `references/editing.md`): `imagegen.py edit --prompt-file edit.txt --image target.png [--image ref.png] [--mask mask.png] --n 2 --out-dir out/<slug>` → uses the edit-track model, the provider's edit endpoint/model id, and the highest quality and complexity. Then the same QA + repair loop, with the extra hard fail "anything changed outside the requested area".
- Default **3 candidates** (1 if the user wants it fast; up to 6 for hero work), all at the highest quality. If the provider has no `n`, loop calls. Vary *only* what is useful (e.g. two framings), not randomly.
- Every output gets a sidecar `.json` with the full request (no key) for reproducibility.

## Step 4 — Vision QA (do not skip)

You usually see an image downscaled; that hides a wrong finger, a third arm at the frame edge or garbled small text. So inspect in two passes:

1. **Whole frame.** Open every candidate. Count people, then trace every arm and hand to the shoulder of one plausible body; check poses, light direction, colour and overall look. Anything with a hard fail is out.
2. **Every region at full detail.** For each candidate still in the running, cut it into enlarged tiles and open **every** tile:
   `python3 SKILL_DIR/scripts/qa_tiles.py out/<slug>/<file>.png -o out/<slug>/qa`
   Tiles overlap and cover the frame edge to edge (corners and borders included). In each tile check hands and fingers, faces, eyes and teeth, ears, hairline, text and labels letter by letter, edges of objects, contact points, reflections, background people and repeating texture.
For a side-by-side view of the candidates: `python3 SKILL_DIR/scripts/contact_sheet.py out/<slug>/*.png -o out/<slug>/sheet.jpg`.

Score each candidate with `references/qa-rubric.md` (10 criteria, hard-fail list).
- Pick the best. A candidate with any **hard fail** cannot ship.
- If the best scores ≥ 8.5/10 with no hard fail → Step 6.
- Else → Step 5.
- The image you deliver must have passed both passes, including after every repair.

## Step 5 — Repair loop (max 3 rounds, one change at a time)

- Local defect (hand, text, stray object, face detail) → **edit** the winner with a mask or tight instruction, restating every invariant ("change only the left hand; keep everything else identical").
- Global defect (too glossy, wrong light, staged feel, AI look) → **revise the brief** (the rubric maps each failure to a prompt fix) and regenerate.
- Re-QA after every round. After 3 rounds, deliver the best and state the remaining flaw honestly.

## Step 6 — Finishing + delivery

1. The winner is already rendered at the highest quality; no extra render is needed.
2. Optional `scripts/photo_finish.py` (grain, subtle vignette, lateral chromatic aberration, highlight roll-off) — only if the image still looks too clean; keep it subtle; compare before/after and inspect the result again. It refuses files that carry C2PA provenance data (exit 3); then deliver the image as generated.
3. Save to the user's requested location (or `./images/<slug>-vN.<ext>`); never overwrite without being asked.
4. Report: file path(s), model + provider + settings, final brief (collapsed), QA score + any known flaw, cost estimate if known.

## Ethics & provenance (non-negotiable)

- Do not remove or forge provenance data (C2PA, watermarks) and do not fabricate camera EXIF to pass images off as real photographs. "Looks real" is an aesthetic goal, not a deception tool.
- No photoreal depictions of real, identifiable private individuals without consent; no fake evidence, documents, or news events presented as real; follow the provider's policy. If a request crosses these lines, decline that part and offer a safe alternative.

## Quick reference — the 12 realism levers (memorise)

1. A specific photographer with a reason to take the shot.
2. One motivated light source with direction + colour temperature.
3. Lens/focal length consistent with framing; DOF consistent with aperture and distance.
4. Real imperfections: noise, slight tilt, clipped highlight, imperfect focus plane.
5. Skin: pores, uneven tone, fine hair, no airbrushing.
6. Asymmetry and mid-action moments, not poses.
7. Mundane, specific background clutter.
8. Wear: scratches, dust, creases, fingerprints, stains.
9. Neutral, believable colour (no default warm/sepia cast, no teal-orange).
10. No AI-art vocabulary.
11. Highest quality on every render, multiple candidates, ruthless QA at full detail.
12. Edit locally, regenerate globally; restate invariants every time.
