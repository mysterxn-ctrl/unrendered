# Configuration

## Files and folders

| Path | Content |
|---|---|
| `skills/unrendered/SKILL.md` | The skill: workflow and rules the agent follows |
| `skills/unrendered/references/` | Photorealism playbook, genre recipes, prompt compiler, QA rubric, editing, providers, model selection, non-photo requests |
| `skills/unrendered/scripts/` | `imagegen.py`, `model_select.py`, `qa_tiles.py`, `contact_sheet.py`, `photo_finish.py` |
| `skills/unrendered/models.json` | Seed model registry |
| `skills/unrendered/benchmarks/` | Seed leaderboard snapshots |
| `skills/unrendered/providers/` | Bundled provider profiles and the template |
| `~/.config/unrendered/` | Your state: `providers/`, `models.json`, `benchmarks/` (override with `UNRENDERED_HOME`) |

The registry is read from the newer of the seed copy and your state copy (by last check date); models and duels that only exist in the other copy are merged in. Writes always go to your state folder, so updates never overwrite your decisions.

## Model registry (`models.json`)

```json
{
  "schema_version": 2,
  "last_checked": "2026-11-18",
  "refresh_interval_days": 14,
  "default":  {"generate": "gpt-image-2.6-sunburst", "edit": "gpt-image-2.6-sunburst"},
  "selected": {"generate": "gpt-image-2.6-sunburst", "edit": "gpt-image-2.6-sunburst"},
  "ranking":  {"generate": ["…"], "edit": ["…"]},
  "duels": {},
  "models": [ { "…": "see below" } ],
  "history": [ {"date": "…", "track": "…", "from": "…", "to": "…", "reason": "…", "evidence": ["…"]} ]
}
```

### Model entry

| Field | Description |
|---|---|
| `id` | Canonical id (kebab-case) |
| `aliases` | Names used by leaderboards and providers; matching is case- and punctuation-insensitive |
| `vendor`, `released` | Informational |
| `onboarded` | `false` for models auto-added from a leaderboard until settings are filled in |
| `benchmarks` | `{"<source>_<track>_<category>": {"elo", "ci95", "config", "rank", "date"}}` — maintained by the code |
| `capabilities` | `generate`, `edit`, `max_reference_images`, `mask`, `negative_prompt_param`, `seed`, `transparent_background`, size limits |
| `settings` | `quality_values`, `complexity_values` (every render uses the highest listed level), `candidate`, `final`, `edit`, `edit_final` (kept at the highest level), `preferred_sizes` |
| `prompt_dialect` | How to phrase briefs for this model |
| `known_weaknesses` | What QA should look for first |

## Benchmark snapshots

```json
{
  "source": "artificial_analysis",
  "track": "generate",
  "category": "overall",
  "rank": "primary",
  "url": "https://artificialanalysis.ai/image/leaderboard/text-to-image",
  "fetched": "2026-11-18",
  "rows": [{"name": "GPT Image 2.6 Sunburst (max)", "elo": 1261, "ci": 14, "vendor": "OpenAI"}]
}
```

- `category`: `overall`, or a photo-specific category (`photorealistic`, `photography`, `people`) which then takes precedence.
- `ci`: half-width of the 95 % confidence interval.
- At least five rows; numbers exactly as published.

## Provider profiles

```json
{
  "name": "my-provider",
  "notes": "where the field names come from",
  "base_url": "https://api.example.com",
  "auth": {"type": "header", "header": "Authorization", "prefix": "Bearer ", "env": "MY_PROVIDER_KEY"},
  "headers": {},
  "timeout_s": 300,
  "download_with_auth": false,
  "model_map": {"gpt-image-2.6-sunburst": "provider-model-id"},
  "models": [],
  "list_models": {"path": "/models", "ids_path": "data[*].id"},
  "serves_any_model": false,
  "operations": {
    "generate": {
      "method": "POST",
      "path": "/v1/images/{model}",
      "content_type": "json",
      "query": {},
      "static": {},
      "params": {},
      "async": null,
      "result": {"paths": ["data[*].b64_json", "data[*].url"], "meta_paths": {"revised_prompt": "data[*].revised_prompt"}}
    },
    "edit": {"model_map": {}, "...": "same keys as generate"}
  }
}
```

### Auth

| Form | Example |
|---|---|
| Header | `{"type": "header", "header": "Authorization", "prefix": "Bearer ", "env": "KEY_VAR"}` |
| Query parameter | `{"type": "query", "param": "key", "env": "KEY_VAR"}` |
| Optional (host injects credentials) | add `"optional": true` |
| None | `{"type": "none"}` |

`base_url` and `url` may contain `${ENV_VAR}`; `path` and `url` may contain `{model}`.

### Parameter mapping

`params` maps canonical names — `prompt, model, size, quality, complexity, n, output_format, output_compression, background, moderation, seed, negative_prompt, images, mask` — to provider fields. A spec is:

- a string: the provider field name, or
- an object `{"to": "a.b", "transform": "...", "map": {...}, "choices": [...], "tiers": {...}, "single": true}`, or
- a list of such specs (one canonical value → several provider fields).

| Transform | Effect |
|---|---|
| `aspect_ratio` | `WxH` → `"w:h"`, or the nearest of `choices` |
| `resolution_tier` | `WxH` → `1K` / `2K` / `4K` by megapixels (override with `tiers`) |
| `width`, `height` | split `WxH` |
| `int`, `float`, `bool` | type conversion |
| `list`, `first` | wrap / unwrap |
| `data_uri` | local file → data URI (URLs pass through) |
| `b64` | local file → base64 |
| `file` | multipart file upload (requires `"content_type": "multipart"`) |
| `template` | `{"template": "prefix-{value}"}` |

`map` translates values after the transform, e.g. `{"max": "ultra"}`. Unmapped canonical parameters are not sent (the runner warns); an unmapped `n` is looped client-side; an unmapped `negative_prompt` is appended to the prompt.

### Async jobs

```json
"async": {
  "id_path": "request_id",
  "poll_url": "{base_url}/jobs/{id}",
  "poll_url_path": null,
  "poll_method": "GET",
  "status_path": "status",
  "done": ["completed", "succeeded"],
  "failed": ["failed", "error"],
  "interval_s": 3,
  "timeout_s": 900,
  "result_url_path": null,
  "result_in_submit": true
}
```

Use `poll_url_path` when the submit response contains the status URL; `result_url_path` when the finished job points to a separate result document.

### Result extraction

`result.paths` are tried in order; `[*]` iterates lists. Values may be base64, data URIs or URLs (downloaded, with auth if `download_with_auth`). File types are detected from content (PNG, JPEG, WebP, GIF, SVG, AVIF).

### Tool providers

```json
{"name": "my-tool", "type": "tool", "tool": "mcp__server__generate",
 "operations": {"generate": {"models": ["gpt-image-2.6-sunburst"]}, "edit": {"models": ["gpt-image-2.6-sunburst"]}}}
```
