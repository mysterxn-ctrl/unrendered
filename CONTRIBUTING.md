# Contributing to Unrendered

Thanks for helping make AI images look less rendered. Unrendered is created and maintained by **Ruben Ferraro**. This guide covers the development setup and the rules that keep the project trustworthy.

## Ways to contribute

- **Provider profiles** for APIs people use — fields only from the provider's official docs.
- **Model onboarding** — tuned settings, prompt dialect and known weaknesses for a newly ranked model, with sources.
- **Genre recipes and QA findings** — new failure modes and the fix that worked.
- **Documentation** — corrections and clearer examples.
- **Bug reports** — with the command, the profile (without keys) and the output.

## Development setup

```bash
git clone https://github.com/mysterxn-ctrl/unrendered.git
```

```bash
cd unrendered
```

The core needs only Python 3.9+. Optional extras for the image helpers:

```bash
pip install pillow numpy
```

### Run the tests

```bash
cd tests && python3 -m unittest -v
```

The suite is fully offline: a local mock image API stands in for real providers. Every change to the scripts needs a test.

### Check the docs

```bash
python3 tools/check_links.py
```

Verifies every relative link and anchor in the Markdown files.

### Validate the plugin

```bash
claude plugin validate .
```

## Rules

1. **Evidence over opinion.** The model registry changes only through `model_select.py` and public leaderboard data (`ingest` / `refresh`). Pull requests that edit `selected` or rankings by hand are declined.
2. **No vendor lock-in.** Code stays provider-agnostic. Vendor specifics belong in profiles (`providers/*.json`) and model entries, never in scripts.
3. **No secrets.** Profiles reference environment-variable names only. Never commit keys, tokens or real request logs.
4. **Standard library first.** The core scripts must keep working without third-party packages.
5. **Responsible use.** Contributions that strip or forge provenance data, fabricate camera metadata or target real private individuals are not accepted.
6. **Docs are the source of truth.** If you change behaviour, update `docs/` and the relevant file in `skills/unrendered/references/` in the same pull request.

## Licensing of contributions

Unrendered is licensed under the [Apache License 2.0](LICENSE). By submitting a contribution you agree that it is licensed under the same terms (Section 5 of the license). New source files start with:

```text
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Ruben Ferraro — Unrendered (https://github.com/mysterxn-ctrl/unrendered)
```

The files in `assets/brand/` and the name "Unrendered" are not covered by the Apache License; see [TRADEMARKS.md](TRADEMARKS.md).

## Pull requests

- Keep each pull request focused on one change.
- Describe what changed and how you tested it.
- Make sure CI is green: tests, JSON validation, link check and the README model table.
- Use clear commit messages in the imperative mood (`Add async polling for result URLs`).

## Maintaining the bundled benchmark data

A scheduled workflow refreshes `skills/unrendered/benchmarks/`, `models.json` and the model table in the README every week. To refresh by hand:

```bash
UNRENDERED_HOME=skills/unrendered python3 skills/unrendered/scripts/model_select.py refresh
```

```bash
python3 tools/update_readme.py
```

If a leaderboard blocks scripted access, write the rows per `model_select.py schema` and run `ingest` with the same `UNRENDERED_HOME`.
