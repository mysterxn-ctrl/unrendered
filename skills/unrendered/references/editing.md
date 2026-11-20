# Editing, references, identity, compositing

## Classify every input image
Label each image by index and role in the prompt: `Image 1: edit target`, `Image 2: subject reference (identity)`, `Image 3: style/lighting reference`, `Image 4: object to insert`. Images given only for inspiration → **generate with references**, not edit.

## Edit brief template
```
Edit Image 1.
Change only: <precise change, location in frame>.
Keep exactly unchanged: identity and face of every person, pose, expression, clothing, background, framing, lighting direction and colour, camera perspective, image grain/noise, all text.
Match: the new element must share the scene's light direction (<from left>), colour temperature (<~5000K>), perspective and lens blur, with a correct contact shadow.
Avoid: restyling, smoothing skin, sharpening, colour shifts, extra objects, watermark.
```
Settings: `complexity=low` (or `medium` for larger changes), quality `high`. Use a mask when the provider supports it (transparent = editable area, same pixel size as Image 1). Masks are guidance, not pixel-exact guarantees.

## Use-case notes
- **Identity-preserve (try-on, person in new scene):** lock face, hairline, skin tone, body proportions; describe the new clothing/scene; demand light matching. Accept only if the face is recognisably the same at a glance AND at zoom.
- **Precise object removal/replacement:** describe what fills the gap (continue the wall texture, floorboards continue with same grain direction).
- **Lighting/weather change:** change only light/atmosphere; geometry and identity fixed; adjust shadows physically (rain → wet reflective surfaces, overcast → soft shadows).
- **Background replacement:** match horizon height & lens perspective to the subject's camera; edge hair detail preserved; add environment colour spill on the subject's edges.
- **Compositing multiple images:** say what moves where, relative scale, who occludes whom, unified light.
- **Text localisation:** change only the text; keep font style, size, colour, kerning, alignment.
- **Sketch-to-photo:** keep layout, proportions and perspective of the sketch; choose real materials and a real light setup.

## Multi-turn consistency
- Always continue from the **last approved** image, not a degraded one.
- Restate invariants every turn; drift accumulates.
- For a series (same character, multiple shots): keep a "character sheet" paragraph (age, face specifics, hair, outfit, distinctive marks) and paste it verbatim into each brief; pass the best previous image as identity reference.
