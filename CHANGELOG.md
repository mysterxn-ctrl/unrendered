# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/).

Benchmark refreshes committed by the scheduled workflow are data updates and are not listed individually.

## [1.0.0] — 2026-11-21

First public release by Ruben Ferraro.

### Added
- Agent skill `unrendered` (`skills/unrendered/SKILL.md`) with a one-shot workflow: plan, brief, one render at the highest quality, delivery; checks and repairs on request.
- Autonomous, benchmark-based model selection (`model_select.py`) with separate generation and editing tracks, a confidence-interval decision rule, automatic onboarding of new models, availability resolution across providers and photoreal duels as tie-breakers.
- Provider-agnostic runner (`imagegen.py`): JSON provider profiles, sync and async APIs, JSON and multipart bodies, base64 / data-URI / URL results, per-operation edit model ids, tool providers, `--model auto`.
- Generic OpenAI-protocol provider profile and a profile template.
- Photorealism playbook, twenty photo-genre recipes, brief compiler, realism QA rubric, editing guide and non-photo brief format.
- Briefs block every body and face: people counted and placed, every visible hand with a side and a task, weight and support, expression as eyes, brows, mouth and gaze.
- Briefs design out the compositions models get wrong (risk table) and pass a text-only pre-flight before the render.
- On-request QA built around limbs, pose, facial expression, texture and optics, each with its own minimum score of 8.
- Every render at the model's highest quality and complexity; the runner stops rather than fall back to a provider default.
- `qa_tiles.py` for full-detail checks on request, plus `contact_sheet.py` and `photo_finish.py` helpers.
- Claude Code plugin and marketplace manifests; compatible with the skills CLI.
- Documentation, offline test suite, CI, Markdown link check and a scheduled benchmark refresh.
- Apache License 2.0 with NOTICE; brand assets kept outside the open-source license.
- Website on GitHub Pages: live-surface landing page and the full documentation, built from `docs/`.

[1.0.0]: https://github.com/mysterxn-ctrl/unrendered/releases/tag/v1.0.0
