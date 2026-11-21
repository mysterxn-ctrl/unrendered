# FAQ

## What exactly is Unrendered?

An agent skill — instructions, reference knowledge and small scripts — that makes coding agents produce photorealistic images and edits through any image-generation API. It decides which model to use from public benchmarks, writes photographer-grade briefs, generates several candidates, checks them like a photo editor and repairs what fails.

## Which agents does it work with?

Anything that supports `SKILL.md` skills: Claude Code (as a plugin or a skill), Codex, Cursor, OpenCode and the other agents supported by the `skills` CLI. Agents without skill support can follow `SKILL.md` when you point them at it in their rules.

## Which image APIs does it work with?

Any. Services that speak the OpenAI-style Images protocol work out of the box through environment variables. For every other API, a small JSON profile describes its fields, auth and response format — your agent can write it from the provider's documentation. Agent tools (MCP servers) can be used as providers too. See [Providers](providers.md).

## Which model does it use?

Whatever leads the blind-preference leaderboards by a statistically meaningful margin — separately for generation and for editing — and is reachable through your providers. The default model for both is **GPT Image 2.6 Sunburst**. See [Model selection](model-selection.md).

## Will it switch models automatically when something better comes out?

Yes. Every 14 days it re-reads the leaderboards (the repository also refreshes its bundled data weekly). New models are added automatically; the selection changes only when a model's lead exceeds the combined confidence intervals, or is large and confirmed by a second leaderboard. Ties keep the current model unless a local photorealism duel says otherwise.

## Why do my API images look worse than the same model in a chat app?

Chat apps rewrite your prompt into a detailed one, may plan and generate several candidates, and pick quality settings for you. A raw API call sends your one-liner at whatever quality the gateway defaults to, sometimes `low` or `medium`. Unrendered does the rewriting, the candidates and the quality settings explicitly, plus photorealism-specific briefs and QA. See [How it works](how-it-works.md).

## Does it catch every flaw?

It catches the typical ones reliably, but not every subtle one. The checking is done by the vision of the agent that runs the skill, guided by a fixed rubric: it traces every arm and hand to one body, checks hands, faces, text, light, contrast and surfaces, and treats duplicated limbs, impossible poses and garbled text as hard fails. Fine defects at small scale can still slip through, and image models do not always fix a flaw on request. After three repair rounds the agent delivers the best image and names any flaw that remains, instead of calling it perfect.

## What does it cost?

Unrendered is free. You pay your image provider. A typical job is three candidates at high quality plus one final render at the model's top setting; one or two repair rounds add more. Ask for "one quick draft" to use a single low-cost render.

## Why are briefs written in English?

Image models follow English photographic vocabulary most reliably. You can talk to your agent in any language; the brief sent to the model is English.

## Can it make images that aren't photos?

Yes. Photographs are the default; when you explicitly ask for an illustration, infographic, logo, UI mock-up or 3D look, a dedicated brief format is used with the same candidates-QA-repair discipline.

## Does it remove watermarks or provenance data so images pass as real photos?

No. "Looks real" is an aesthetic goal. Unrendered never strips or forges provenance data (such as C2PA) or invents camera metadata, and it declines photoreal depictions of real private individuals without consent, fake evidence, or fabricated news events.

## Where are my settings stored? Will an update overwrite them?

In `~/.config/unrendered/` (or `UNRENDERED_HOME`). Updates only replace the skill folder; your profiles, registry and snapshots stay.

## The leaderboard fetch fails in my environment. What now?

Some sandboxes block scripted web requests. The planner then hands the agent a precise task: read the listed leaderboard pages with its own web tools, write the numbers in the snapshot format and run `model_select.py ingest`. The decision itself is still made by the code. Without any web access, the current selection is kept and you are told.

## How do I add a provider by hand?

Copy `skills/unrendered/providers/_TEMPLATE.json` to `~/.config/unrendered/providers/<name>.json`, fill it from the provider's docs, then run `imagegen.py validate --profile <name>` and a `--dry-run`. See [Configuration](configuration.md#provider-profiles).

## How do I run the tests?

```bash
cd tests && python3 -m unittest -v
```

The suite is fully offline: it uses a local mock image API.
