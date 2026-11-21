# Editing

Editing an existing image is its own track in Unrendered — with its own leaderboard, its own model choice, the provider's edit endpoint and edit-specific settings.

## Generate or edit?

| The user… | Track |
|---|---|
| wants a new picture, possibly "in the style of" or "like" a reference | `generate` (references are inspiration) |
| wants to change an existing picture while keeping the rest | `edit` |
| wants to combine several pictures (person into scene, product onto table) | `edit` (compositing) |

Every input image is labelled by index and role in the prompt: `Image 1: edit target`, `Image 2: identity reference`, `Image 3: lighting reference`.

## What the edit track changes

- **Model:** the leader of the [image-editing leaderboard](model-selection.md) after the decision rule — which can differ from the generation leader.
- **Endpoint:** the provider's edit model id or endpoint (`operations.edit.model_map`).
- **Settings:** the model's highest quality and complexity, like every render. High complexity plans more and can also touch areas outside the instruction, so every edit brief restates the invariants, uses a mask where the provider supports it, and the result is compared region by region with the original.
- **QA:** an extra hard fail — *anything changed outside the requested area*.

```bash
python3 scripts/imagegen.py edit --prompt-file edit.txt \
  --image photo.jpg --image reference.png --mask mask.png --n 2 --out-dir images/edit
```

## The edit brief

```text
Edit Image 1.
Change only: <precise change and where in the frame>.
Keep exactly unchanged: identity and face of every person, pose, expression, clothing, background,
framing, light direction and colour, camera perspective, grain and noise, all text.
Match: the new element shares the scene's light direction (<from left>), colour temperature
(<≈5000 K>), perspective and lens blur, with a correct contact shadow.
Avoid: restyling, skin smoothing, sharpening, colour shifts, extra objects, watermark.
```

Masks (where the provider supports them): transparent = editable, same pixel size as Image 1. Masks guide the model; they are not pixel-exact guarantees.

## Common edits

| Edit | Key instructions |
|---|---|
| **Identity-preserving** (try-on, person in a new scene) | Lock face, hairline, skin tone, proportions; demand light matching; accept only if the person is recognisably the same at a glance *and* when zoomed in. |
| **Object removal / replacement** | Describe what fills the gap ("floorboards continue with the same grain direction"). |
| **Light or weather** | Change only light and atmosphere; adjust shadows physically (rain → wet, reflective surfaces; overcast → soft shadows). |
| **Background replacement** | Match horizon height and lens perspective; keep hair edges; add the new environment's colour spill on the subject's edges. |
| **Compositing** | Say what goes where, relative scale, who occludes whom, unified light. |
| **Text localisation** | Change only the text; keep font, size, colour, kerning, alignment. |
| **Sketch to photo** | Keep layout, proportions and perspective; choose real materials and a real light setup. |

## Multi-step edits and series

- Continue from the **last approved** image, never from a degraded one.
- Restate the invariants on every turn — drift accumulates.
- For a series with the same person or product, keep a fixed description paragraph (age, face details, hair, outfit, distinctive marks) and paste it verbatim into every brief; pass the best previous image as identity reference.
