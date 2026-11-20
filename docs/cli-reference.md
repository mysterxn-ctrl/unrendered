# CLI reference

All scripts live in `skills/unrendered/scripts/` and run with Python 3.9+. Agents call them for you; this page is for people who want to script or debug.

## imagegen.py

Provider-agnostic runner. Standard library only.

```bash
python3 imagegen.py profiles
python3 imagegen.py validate --profile NAME
python3 imagegen.py generate [options]
python3 imagegen.py edit --image TARGET [--image REF ...] [--mask MASK] [options]
```

### Options for `generate` and `edit`

| Option | Default | Description |
|---|---|---|
| `--profile NAME\|PATH` | `auto` | Provider profile. `auto` asks `model_select.py plan` for the best available provider. |
| `--model ID` | `auto` | Canonical model id from the registry. `auto` = benchmark-best available model for this track. |
| `--final` | off | With automatic settings, use the model's final (highest) settings instead of candidate settings. |
| `--prompt TEXT` / `--prompt-file FILE` | — | The compiled brief. One of the two is required. |
| `--size WxH` | `1536x1024` | Canonical size; profiles translate it to sizes, aspect ratios or resolution tiers. |
| `--quality` | from model settings, else `high` | e.g. `low`, `medium`, `high`, `xhigh`, `max`, `auto` (model-dependent). |
| `--complexity` | from model settings, else `high` (generate) / `low` (edit) | Planning effort for models that support it. |
| `--n N` | `1` | Number of images. Looped client-side when the provider has no batch parameter. |
| `--negative-prompt TEXT` | — | Sent as a field if the provider has one, otherwise appended to the prompt as "Avoid: …". |
| `--output-format`, `--output-compression`, `--background`, `--moderation`, `--seed` | — | Passed through when the profile maps them. |
| `--set key=value` | — | Raw provider field (repeatable; JSON values allowed; dotted keys create nested objects). |
| `--out-dir DIR` | `images` | Output folder. |
| `--slug NAME` | `img` | File name prefix. |
| `--dry-run` | off | Print the exact HTTP request (keys masked) without sending it. |
| `--image FILE` | — | *edit only, repeatable:* edit target first, then references. |
| `--mask FILE` | — | *edit only:* mask image (transparent = editable). |

Every saved image gets a sidecar `.json` with the canonical request, the profile used and provider metadata such as a revised prompt. Keys are never written.

### Exit codes

| Code | Meaning |
|---|---|
| 0 | success |
| 2 | configuration or usage error (missing key variable, unknown profile, empty prompt) |
| 3 | HTTP failure after retries |
| 4 | no image in the response / no job id |
| 5 | generation failed or timed out |
| 10 | agent action required (tool provider selected, or no provider available) |

Transient HTTP errors (408, 409, 425, 429, 5xx) are retried with exponential back-off.

## model_select.py

Benchmark-driven model selection and availability resolution.

| Command | Description | Exit code |
|---|---|---|
| `plan --task generate\|edit [--no-probe]` | Refresh if due, decide, resolve availability; prints the plan as JSON | 0, or 10 when the agent must act |
| `status` | Registry path, last check, selections and rankings | 0 fresh, 10 refresh due |
| `refresh` | Fetch all leaderboards now, then decide | 0, or 10 if a primary board could not be read |
| `ingest FILE…` | Store leaderboard snapshots gathered by the agent, then decide | 0 |
| `decide` | Re-apply the decision rule to stored snapshots | 0 |
| `duel --track T --pair A B --winner A --scores JSON` | Record a photoreal duel (tie-break only) | 0 |
| `schema` | Print the snapshot format | 0 |

### Plan output

```json
{
  "task": "generate",
  "benchmark_best": "gpt-image-2.6-sunburst",
  "model": "gpt-image-2.6-sunburst",
  "provider_profile": "openai-images-protocol",
  "provider_type": "http",
  "wire_model": "gpt-image-2.6-sunburst",
  "settings": {
    "candidate": {"quality": "high", "complexity": "high"},
    "final": {"quality": "max", "complexity": "high"},
    "edit": {"quality": "high", "complexity": "low"},
    "edit_final": {"quality": "max", "complexity": "low"}
  },
  "prompt_dialect": "natural-language labeled sections, 120-250 words; …",
  "known_weaknesses": ["…"],
  "ranking": ["gpt-image-2.6-sunburst", "gpt-image-2.5-sunburst", "…"]
}
```

Optional fields: `note` (the benchmark-best model was not reachable), `tool` (for tool providers), `actions` (`AGENT_FETCH_LEADERBOARDS`, `ONBOARD_MODEL`, `CONNECT_PROVIDER`, each with a `do` instruction).

## contact_sheet.py

```bash
python3 contact_sheet.py IMG [IMG ...] -o sheet.jpg [--cell 768] [--crops]
```

Labelled side-by-side sheet; `--crops` adds a 3× centre-crop row. Requires Pillow.

## photo_finish.py

```bash
python3 photo_finish.py in.png -o out.png [--grain 0.25] [--vignette 0.15] [--ca 0.6] [--rolloff 0.2] [--jpeg 92] [--seed 7]
```

| Option | Effect |
|---|---|
| `--grain` | luminance-weighted grain, stronger in shadows and mid-tones (0–1) |
| `--vignette` | natural lens fall-off (0–1) |
| `--ca` | lateral chromatic aberration in pixels at the corners |
| `--rolloff` | soft highlight shoulder against harsh digital whites (0–1) |
| `--jpeg Q` | save as JPEG at quality Q |

Requires Pillow and NumPy. Existing metadata is kept; nothing is invented.

## Environment variables

| Variable | Used by | Purpose |
|---|---|---|
| `UNRENDERED_HOME` | all | State folder (default `~/.config/unrendered`) |
| `IMAGE_API_BASE_URL`, `IMAGE_API_KEY` | `openai-images-protocol` profile | Endpoint and key for OpenAI-protocol services |
| *your profile's `auth.env`* | your profiles | API key for that provider |
