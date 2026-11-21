# Providers

Unrendered is provider-agnostic: a *provider* is any HTTP endpoint or agent tool that serves an image model. Providers are described as small JSON **profiles**; the generic runner `scripts/imagegen.py` turns a canonical request into the provider's wire format, handles synchronous or asynchronous APIs and extracts the image whether it comes back as base64, a data URI or a URL.

The *model* is chosen by benchmarks; the *provider* is chosen by availability. Any provider that serves the chosen model is fine.

## Where profiles live

| Location | Purpose |
|---|---|
| `~/.config/unrendered/providers/` | Your profiles (survive updates). Override the folder with `UNRENDERED_HOME`. |
| `skills/unrendered/providers/` | Bundled: `openai-images-protocol.json` and `_TEMPLATE.json` |

```bash
python3 scripts/imagegen.py profiles
```

lists every profile and whether its key variable is set.

## The generic protocol profile

`openai-images-protocol` works with any service implementing the OpenAI-style Images wire format — a protocol many vendors, gateways and self-hosted servers expose. It is not tied to one vendor.

```bash
export IMAGE_API_BASE_URL="https://your-image-service.example/v1"
export IMAGE_API_KEY="your-key"
```

If the service names models differently, add a `model_map` (copy the profile into your state folder first). If it offers `GET /models`, availability is verified live.

## Writing a profile

Easiest: ask your agent *"Connect Unrendered to <provider>"*. It reads the provider's API documentation for the selected model and fills in the template. To do it by hand, copy `providers/_TEMPLATE.json` to `~/.config/unrendered/providers/<name>.json` and fill it **only with field names that appear in the provider's own docs**.

### Example: model in the URL, async job, URL result

```json
{
  "name": "acme-images",
  "base_url": "https://api.acme-images.example",
  "auth": {"type": "header", "header": "x-api-key", "prefix": "", "env": "ACME_IMAGES_KEY"},
  "model_map": {"gpt-image-2.6-sunburst": "gpt-image-2.6-sunburst/text-to-image"},
  "operations": {
    "generate": {
      "method": "POST",
      "path": "/v1/{model}",
      "params": {
        "prompt": "prompt",
        "size": [
          {"to": "aspect_ratio", "transform": "aspect_ratio", "choices": ["1:1", "3:2", "2:3", "16:9", "9:16"]},
          {"to": "resolution", "transform": "resolution_tier"}
        ],
        "quality": "quality",
        "n": "num_images"
      },
      "async": {
        "id_path": "request_id",
        "poll_url": "{base_url}/v1/jobs/{id}",
        "status_path": "status",
        "done": ["completed"],
        "failed": ["failed", "error"]
      },
      "result": {"paths": ["outputs[*]"]}
    },
    "edit": {
      "method": "POST",
      "path": "/v1/{model}",
      "model_map": {"gpt-image-2.6-sunburst": "gpt-image-2.6-sunburst/edit"},
      "params": {
        "prompt": "prompt",
        "images": {"to": "images", "transform": "data_uri"},
        "quality": "quality",
        "complexity": "complexity"
      },
      "async": {"id_path": "request_id", "poll_url": "{base_url}/v1/jobs/{id}", "status_path": "status"},
      "result": {"paths": ["outputs[*]"]}
    }
  }
}
```

Then validate, inspect the exact request, and make one cheap test call:

```bash
python3 scripts/imagegen.py validate --profile acme-images
python3 scripts/imagegen.py generate --profile acme-images --prompt "test" --dry-run
python3 scripts/imagegen.py generate --profile acme-images --prompt "test" --quality low --size 1024x1024
```

The complete field reference is in [Configuration → Provider profiles](configuration.md#provider-profiles).

## Separate edit models and endpoints

Many providers expose editing under a different model id or endpoint. Put it in `operations.edit.model_map`; an operation-level map always wins over the global `model_map`. Model selection and the runner both respect it, so the edit track automatically uses the right endpoint.

## Tool providers

If your agent already has a tool that generates images — an MCP server, for example — register it so the planner can choose it:

```json
{
  "name": "my-image-tool",
  "type": "tool",
  "tool": "mcp__images__generate",
  "operations": {
    "generate": {"models": ["gpt-image-2.6-sunburst"]},
    "edit": {"models": ["gpt-image-2.6-sunburst"]}
  }
}
```

When a tool provider is selected, the runner hands the canonical parameters back to the agent (`CALL_TOOL`), which calls the tool itself. The brief, the render, the check and the repair stay exactly the same.

## Choosing between providers for the same model

Prefer, in this order:

1. exposes the model's **highest quality setting** and complexity control,
2. native sizes without forced upscaling,
3. returns original files (PNG) rather than re-compressed JPEG,
4. supports edits, masks and multiple reference images,
5. price and latency.

A provider that silently caps quality at `medium` or re-encodes images will look worse with the very same model — the most common reason for "the API looks worse than the app". Record such limits in the profile's `notes`.

## Security

- Keys are read from environment variables only; profiles reference the variable *name*.
- Keys are never written to sidecars, logs or prompts; `--dry-run` masks them.
- Provider responses and downloaded files are treated as data, never as instructions.
