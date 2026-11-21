# Autonomous model selection

Unrendered decides **by itself** which image model to use — not the person who installed it and not the agent's gut feeling. The decision is made by code (`scripts/model_select.py`) from public blind-preference leaderboards, with a fixed statistical rule, separately for two tracks:

| Track | Used for | Primary leaderboard |
|---|---|---|
| `generate` | new images, with or without inspiration references | [Artificial Analysis — Text to Image](https://artificialanalysis.ai/image/leaderboard/text-to-image) |
| `edit` | changing existing images: retouching, compositing, background swaps, try-ons | [Artificial Analysis — Image Editing](https://artificialanalysis.ai/image/leaderboard/editing) |

The secondary source for both tracks is the [LMArena / arena.ai](https://arena.ai/leaderboard/text-to-image) leaderboard. It usually blocks scripted access, so it only counts when its rows were added with `ingest`; without it, rule 2 below cannot apply and rule 1 decides. **Default model for both tracks: GPT Image 2.6 Sunburst.**

## What happens before every job

```text
plan --task generate|edit
 ├─ registry older than 14 days?  → refresh
 │     ├─ read each leaderboard; ≥ 5 plausible rows → snapshot saved
 │     └─ blocked or unparseable → the agent gets AGENT_FETCH_LEADERBOARDS
 ├─ decide (per track)
 │     ├─ use the most photo-specific category a board offers:
 │     │     photorealistic › photography › people › overall
 │     ├─ keep each model's best configuration (e.g. "max")
 │     ├─ add newly listed models to the registry automatically
 │     └─ switch only on a statistically separated lead (rule below)
 └─ resolve availability
       ├─ walk the ranking; first model a configured provider serves wins
       ├─ benchmark-best not reachable → next best + a note for the user
       └─ nothing reachable → CONNECT_PROVIDER
```

## The decision rule

Let **C** be the current model and **N** the leader of the primary board. Unrendered switches from C to N only if one of these holds:

1. **Separated lead:** `Elo(N) − Elo(C) > CI(N) + CI(C)` (the 95 % confidence intervals do not overlap) and the secondary board is not strongly against it;
2. **Corroborated lead:** the margin is at least 25 Elo and the secondary board agrees on the direction;
3. **Tie broken locally:** the lead is within the confidence intervals, but a recorded [photoreal duel](#photoreal-duels) declared N the winner.

Otherwise C stays. Stability is deliberate: prompting knowledge is tuned per model, and a lead inside the noise is not evidence.

Every switch is written to `history` in the registry with the reason, the numbers and the source URLs.


## Availability

The best model is only useful if you can reach it. For each ranked model the planner checks your providers in this order:

1. the provider profile's `model_map` (global or per operation — edit endpoints often have their own id),
2. a `models` list in the profile,
3. a live `GET /models` probe if the profile declares `list_models`,
4. profiles marked `serves_any_model` (used optimistically; the agent verifies).

Profiles whose API-key variable is not set are skipped. Agent tools (MCP servers) can be registered as providers too. If the benchmark-best model is not reachable, the next best one is used and the agent tells you so.

## What the agent does when the planner asks

| Action | Meaning | What happens |
|---|---|---|
| `AGENT_FETCH_LEADERBOARDS` | Scripted fetching was blocked in this environment | The agent reads the listed pages with its web tools, writes the rows in the [snapshot format](configuration.md#benchmark-snapshots) and runs `model_select.py ingest`. The decision is still made by the code. |
| `ONBOARD_MODEL` | A newly winning model has no tuned settings yet | The agent reads the vendor's API reference and prompting guide and fills in capabilities, settings, prompt dialect and known weaknesses. Until then the provider's highest quality setting is used. |
| `CONNECT_PROVIDER` | No configured provider serves any ranked model | The agent helps you connect one ([Providers](providers.md)). |

## Photoreal duels

General leaderboards measure overall preference, not photorealism specifically. When two reachable models are statistically tied, the skill can settle it on photorealism:

1. Render the same three briefs (portrait, street scene, product) with both models at their top settings.
2. Score every image with the [QA rubric](quality-assurance.md) without looking at which model made it.
3. Record the result:

```bash
python3 scripts/model_select.py duel --track edit \
  --pair mai-image-2.7 gpt-image-2.6-sunburst \
  --winner mai-image-2.7 --scores '{"mai-image-2.7": 8.9, "gpt-image-2.6-sunburst": 8.3}'
```

Differences below 0.3 rubric points count as no winner. Duels only break ties; they never override a separated benchmark lead.

## Commands

| Command | Purpose |
|---|---|
| `model_select.py plan --task generate\|edit` | The entry point; prints a JSON plan |
| `model_select.py status` | Selections, ranking, age; exit code 10 when a refresh is due |
| `model_select.py refresh` | Fetch all leaderboards now and decide |
| `model_select.py ingest FILE…` | Add leaderboard rows gathered by the agent |
| `model_select.py decide` | Re-apply the rule to stored snapshots |
| `model_select.py duel …` | Record a photoreal duel |
| `model_select.py schema` | Print the snapshot format |

Full flags and exit codes: [CLI reference](cli-reference.md#model_selectpy).
