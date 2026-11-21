# Getting started

Unrendered is an **agent skill**: a folder of instructions, reference material and small scripts that teaches a coding agent (Claude Code, Codex, Cursor, OpenCode and others) to produce photorealistic images through an external image API. You talk to your agent as usual — "make a photo of…", "edit this picture so that…" — and the skill takes over model choice, prompt compilation, generation, quality control and repair.

## Requirements

- An agent that supports skills (`SKILL.md` folders) — or any agent you can point at a Markdown file.
- Python **3.9+** on the machine where the agent runs. The core scripts use only the standard library.
- Optional: `pip install pillow numpy` for contact sheets and the photo-finishing pass.
- Access to at least one image-generation API (any vendor, gateway or self-hosted endpoint) and its API key.

## Install

### Claude Code — plugin (recommended)

```text
/plugin marketplace add mysterxn-ctrl/unrendered
/plugin install unrendered@unrendered
```

Updates arrive through the plugin manager. Your own state (provider profiles, model registry, benchmark snapshots) lives in `~/.config/unrendered/` and is never touched by updates.

### Any agent — skills CLI

```bash
npx skills add mysterxn-ctrl/unrendered
```

Add `-g` to install for your user instead of the current project, and `-a <agent>` to target a specific agent (for example `-a claude-code` or `-a codex`).

### Manual install

```bash
git clone https://github.com/mysterxn-ctrl/unrendered.git
```

```bash
mkdir -p ~/.claude/skills && cp -r unrendered/skills/unrendered ~/.claude/skills/
```

| Agent | Copy `skills/unrendered/` to |
|---|---|
| Claude Code (all projects) | `~/.claude/skills/unrendered/` |
| Claude Code (one project) | `<project>/.claude/skills/unrendered/` |
| Codex | `~/.agents/skills/unrendered/` (or `<repo>/.agents/skills/unrendered/`) |
| Cursor, OpenCode and others | `<project>/.agents/skills/unrendered/` |
| Anything else | Put the folder in your project and add one line to your agent rules: *"For any image generation or editing, follow `unrendered/SKILL.md`."* |

## Connect an image API

Unrendered does not ship with a fixed vendor. You connect whatever you use; the skill then checks which of the benchmark-ranked models your connection can actually serve.

**Option A — the service speaks the OpenAI-style Images protocol** (`POST /images/generations`, `POST /images/edits`). Many vendors, gateways and self-hosted servers do. Set two environment variables in your shell profile or your agent's secret store:

```bash
export IMAGE_API_BASE_URL="https://your-image-service.example/v1"
export IMAGE_API_KEY="your-key"
```

The bundled profile `openai-images-protocol` uses them. If the service lists its models at `GET /models`, Unrendered verifies availability automatically.

**Option B — any other API.** Ask your agent: *"Connect Unrendered to <provider>."* It reads the provider's API documentation and writes a small JSON profile to `~/.config/unrendered/providers/<provider>.json` (field names, auth header, async polling, where the image is in the response, a separate edit endpoint if there is one). You can also write it yourself — see [Providers](providers.md).

**Option C — an MCP server or other agent tool that generates images.** Register it as a *tool provider* so model selection can choose it; see [Providers → Tool providers](providers.md#tool-providers).

Keys are only ever read from environment variables. Never paste a key into a chat or a profile.

## Check the setup

```bash
python3 ~/.claude/skills/unrendered/scripts/model_select.py plan --task generate
```

You get a JSON plan: the benchmark-best model, the provider profile that will serve it, the provider's own model id and the settings to use. If anything is missing, the `actions` field says exactly what (for example `CONNECT_PROVIDER`).

(Adjust the path to wherever the skill is installed. Plugin installs live under `~/.claude/plugins/`.)

## Your first image

Just ask your agent:

> Make a photo of an old fisherman mending a net on a pier at dawn.

The skill will:

1. pick the model from the blind-preference leaderboards (default model: GPT Image 2.6 Sunburst),
2. turn the one-liner into a photographer's brief — who shot it, where the fisherman sits, what each of his hands does with the net, his expression, the lens, the light, the materials — with the compositions models get wrong designed out,
3. render it once at the model's highest quality and complexity,
4. check the image as a whole and in enlarged tiles — limbs, pose, expression, texture, optics, text,
5. repair only what the check found, with a masked edit or a corrected brief,
6. save the image and report path, model, provider, settings, the brief and the check result.

## Your first edit

> Replace the sky in `photos/beach.jpg` with heavy overcast. Keep everything else identical.

Edits run on the **edit track**: the model that leads the image-editing leaderboard (which can differ from the generation leader), the provider's edit endpoint, low "complexity" so nothing outside the requested area changes, and an extra hard fail in QA for unwanted changes. See [Editing](editing.md).

## Where things live

| What | Where |
|---|---|
| Skill (instructions, references, scripts, seed data) | wherever you installed `skills/unrendered/` |
| Provider profiles you create | `~/.config/unrendered/providers/` |
| Live model registry and decisions | `~/.config/unrendered/models.json` |
| Leaderboard snapshots | `~/.config/unrendered/benchmarks/` |
| Generated images | the path you ask for, otherwise `./images/` |

Set `UNRENDERED_HOME` to move the state folder.

## Next steps

- [How it works](how-it-works.md) — the full pipeline and why raw API calls look worse.
- [Model selection](model-selection.md) — how the skill picks and switches models on its own.
- [Photorealism guide](photorealism.md) — the knowledge behind the briefs.
