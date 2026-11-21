---
name: unrendered
description: "Unrendered — photos, not renders. Generate or edit images through ANY image-generation API (provider-agnostic) at the highest achievable quality; default goal: photographs that look genuinely captured by a person with a real camera. Use whenever the user asks to create, generate, render, make, shoot or edit an image, photo, picture, portrait, product shot, scene or visual, in any language (e.g. 'erstelle ein Bild', 'mach ein Foto von', 'bearbeite dieses Foto'). Picks the model autonomously from current blind-preference benchmarks (separately for generation and editing), designs out the compositions models get wrong, compiles a photographer's brief that specifies every person, hand, face and material, and renders once at the highest quality; checks and repairs only on request. Not for SVG/vector/code-native graphics."
license: Apache-2.0
metadata:
  author: Ruben Ferraro
  version: 1.0.0
  repository: https://github.com/mysterxn-ctrl/unrendered
---

# Unrendered — photos, not renders

Provider-agnostic, benchmark-driven, photographer-grade image generation and editing.

You are not a "prompt typist". You are a **photographer** who happens to operate an image model through an API. A raw API call with the user's one-liner produces a generic, glossy, obviously-AI image, because the model fills every gap with its own average. This skill works **one-shot**: the brief leaves no gap — every person placed, every hand assigned, every face, material, lens and light written out, risky compositions designed out — and the image is rendered once at the highest quality. No inspection pass afterwards unless the user asks for one.

Hard rules (never break):
1. **Provider-agnostic.** Never assume a specific vendor, gateway or SDK. Use whatever image API the user has configured or names. See "Step 0".
2. **The skill picks the model itself — by benchmarks, by code.** Always start with `python3 SKILL_DIR/scripts/model_select.py plan --task generate|edit`. It refreshes the leaderboards when due, applies the statistical decision rule separately for generation and editing, and returns the best-ranked model that a configured provider actually serves. Default starting point for both tracks: `gpt-image-2.6-sunburst`. Never pick or switch models by gut feeling, and never hard-code a provider.
3. **Never ship the user's raw prompt.** Always compile it (Step 2) — the brief carries the whole quality.
4. **One shot, no post-check by default.** Render once and deliver. Inspect or repair only when the user asks or reports a flaw ("On request" below).
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
| `references/prompt-compiler.md` | Step 2 — risk design, writing rules, the brief template, pre-flight, worked examples |
| `references/qa-rubric.md` | On request — checklist, scoring and repair moves when the user asks for a check or reports a flaw |
| `references/editing.md` | Edits, references, identity, compositing |
| `scripts/imagegen.py` | Generic HTTP runner driven by a provider profile (stdlib only) |
| `scripts/qa_tiles.py` | On request — enlarged, overlapping tiles for a full-detail check |
| `scripts/contact_sheet.py` | On request — several images side by side |
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
4. **Always the highest quality.** Every render and edit is sent at the model's highest quality and complexity level. `imagegen.py` does this automatically from the registry (`quality_values`, `complexity_values`); for GPT Image 2.6 Sunburst that is `quality=max`, `complexity=high`, for generation and edits alike. Never pass a lower level, never accept a gateway default. If the runner stops with `ONBOARD_MODEL` (quality levels of the model unknown), read the provider's API reference, add the levels, and run again.
   - Size: native ≤ 2560×1440 (beyond that is *experimental*: more artifacts).
   - Edits at high complexity can also touch areas outside the instruction: always restate every invariant, and use a mask where supported.
5. Aspect ratio follows the photographic genre (3:2 for full-frame/DSLR, 4:3 for phone, 4:5 / 9:16 for social, 16:9 for video stills). Use the provider's exact allowed sizes.

## Step 2 — Design and compile the brief (this is where the result is decided)

Follow `references/prompt-compiler.md` exactly. In short:

1. **Interpret intent:** subject, purpose (ad, editorial, social, stock, family snapshot…), mood, must-haves, must-not-haves, any exact text. Use reference images the user supplies (person, pose, product, room) as references.
2. **Design out the failure points** (`prompt-compiler.md` §1): keep what the user asked for, but choose the way of showing it with the fewest risk elements — hands without a visible owner, people touching, more than three people in focus, complex poses, small tools in hands, interlaced fingers, teeth in close-up, legs under tables, text, screens, mirrors, frame-filling fine texture. Handle every remaining one exactly as the table says.
3. **Cast the photographer:** *who* took this photo, *with what*, *why*, *when* (`references/photo-genres.md`). This fixes camera, lens, light, framing and the kind of imperfection.
4. **Block every body and face** (mandatory whenever a person or any body part is visible): one block per person — position in the frame and facing; weight and support; right hand: task and grip; left hand: task and grip; where limbs leave the frame and the body continues. Never ask for disembodied hands. Expression as eyes, brows, mouth and gaze target for this exact moment, never just "smiling".
5. **Write the physical scene:** concrete place, time, weather, counted objects, one motivated key light with direction and colour temperature, where shadows fall, what is in focus and what is not.
6. **Inject material and capture truth** (`references/photoreal-playbook.md`): skin with pores and uneven tone, flyaway hair, each main material with its texture and wear; depth of field matched to focal length, aperture and distance; noise at the stated ISO; white balance that fits the light.
7. **Write it the way the model follows** (`prompt-compiler.md` §2): most important first, one fact per sentence, everything anchored in the frame, correct states described positively (no anatomy negations), counts stated, no contradictions, no AI-art vocabulary. The Avoid line is for style only.
8. **Pre-flight** (`prompt-compiler.md` §4): read the brief once against the checklist and fix it. This costs no image tokens and is the only check in the default flow.
9. Format in the model's `prompt_dialect` (for GPT-Image: labelled sections in natural language, 120–250 words, up to ~300 with several people or exact text).

Default is a real photograph. If the user explicitly wants a non-photo look (illustration, infographic, logo, UI, 3D, painting), use `references/non-photo.md`, with the same one-shot discipline.

If the user's prompt is already a detailed brief, normalise it — keep their creative choices and add only what is missing (bodies, physics, capture). Ask a question only if something blocking is unknown (which person, which product, exact copy); otherwise decide like a professional and state the decisions.

## Step 3 — Render once

- Write the brief to a file, then:
  `python3 SKILL_DIR/scripts/imagegen.py generate --prompt-file brief.txt --size <native size for the aspect> --out-dir out/<slug> --slug <slug>`
  Model, provider, `quality` and `complexity` (always the highest) come from Step 1 automatically.
- **Edits** (see `references/editing.md`): `imagegen.py edit --prompt-file edit.txt --image target.png [--image ref.png] [--mask mask.png] --out-dir out/<slug>` → edit-track model, the provider's edit endpoint, highest quality and complexity. Use a mask where supported and restate every invariant.
- One image by default. Render more only when the user asks for variations.
- Every output gets a sidecar `.json` with the full request (no key).

## Step 4 — Deliver

1. Save to the user's requested location (or `./images/<slug>.<ext>`); never overwrite without being asked.
2. Report: file path, model + provider + settings, and the brief (collapsed).
3. Optional `scripts/photo_finish.py` (grain, subtle vignette, lateral chromatic aberration, highlight roll-off) only if the user wants a less clean look. It refuses files that carry C2PA provenance data (exit 3).

## On request — check and repair

Only when the user asks for a check or points out a flaw:

- **Check:** `python3 SKILL_DIR/scripts/qa_tiles.py <image> -o out/<slug>/qa` cuts the image into enlarged, overlapping tiles; open the tiles that show the part in question (or all of them for a full check) and judge with `references/qa-rubric.md` — limbs, pose, facial expression, texture, optics.
- **Repair, one change at a time:** a wrong limb or an impossible pose → fix the brief per `prompt-compiler.md` §1 and the rubric's repair map, then render again; a single hand, expression, skin area, sign or object → masked edit that restates every invariant. Continue from the last approved image.

## Ethics & provenance (non-negotiable)

- Do not remove or forge provenance data (C2PA, watermarks) and do not fabricate camera EXIF to pass images off as real photographs. "Looks real" is an aesthetic goal, not a deception tool.
- No photoreal depictions of real, identifiable private individuals without consent; no fake evidence, documents, or news events presented as real; follow the provider's policy. If a request crosses these lines, decline that part and offer a safe alternative.

## Quick reference — the 12 realism levers (memorise)

1. A specific photographer with a reason to take the shot.
2. One motivated light source with direction + colour temperature.
3. Lens/focal length consistent with framing; DOF consistent with aperture and distance.
4. Real imperfections: noise, slight tilt, clipped highlight, imperfect focus plane.
5. Skin: pores, uneven tone, fine hair, no airbrushing.
6. Every body blocked: people counted and placed, every visible hand with a side and a task, weight and support; mid-action, never a stiff pose; expression as eyes + mouth + gaze.
7. Mundane, specific background clutter.
8. Wear: scratches, dust, creases, fingerprints, stains.
9. Neutral, believable colour (no default warm/sepia cast, no teal-orange).
10. No AI-art vocabulary.
11. Risky compositions designed out before writing; highest quality on every render.
12. Correct states written positively, nothing contradictory, the brief pre-flighted once — then one render.
