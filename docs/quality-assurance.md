# Quality assurance

No image leaves Unrendered unchecked. The agent looks at every candidate — at full size and in zoomed regions — like a photo editor hunting for fakes. It first traces every arm and hand back to one plausible body, then checks eyes, teeth, ears, hands, hairline, jewellery, text, reflections, shadows, contact points, background people, repeating textures, subject edges.

## Hard fails

Any one of these disqualifies a candidate, whatever its score:

1. Wrong anatomy — duplicated or misplaced arms, hands or legs; limbs that belong to no plausible body; impossible body positions; extra, missing or fused fingers; impossible joints; mismatched eyes or catchlights; melted ears; too many teeth.
2. Gibberish or misspelled text where text is readable.
3. Physically impossible light — contradictory shadows, a subject lit by nothing, missing contact shadows.
4. Fused objects — a hand merging into a cup, glasses into hair, chair legs into the floor.
5. Duplicated faces or objects; repeating or cellular texture patterns.
6. A violated user requirement, or an unrequested watermark or logo.
7. Distorted background people in focus.
8. *Edits:* anything changed outside the requested area.

## Scored criteria

| # | Criterion | Weight | A 10 looks like |
|---|---|---|---|
| 1 | Prompt fidelity | 1.0 | everything requested, nothing unrequested |
| 2 | Light physics | 1.5 | one coherent key; matching shadows, catchlights, colour temperature |
| 3 | Optics coherence | 1.0 | depth of field and perspective match the stated lens and distance |
| 4 | Human realism | 1.5 | skin texture, asymmetry, natural expression, believable hands |
| 5 | Material and world realism | 1.0 | correct materials, wear, clutter, reflections |
| 6 | Capture authenticity | 1.0 | plausible noise, dynamic range, small imperfections |
| 7 | Composition plausibility | 0.75 | a person would plausibly frame it this way |
| 8 | Colour naturalness | 0.75 | believable white balance, restrained saturation and contrast |
| 9 | Absence of AI sheen | 1.5 | no plastic skin, glow or over-sharpened micro-contrast |
| 10 | Technical cleanliness | 1.0 | no artifacts, banding, halos or mushy textures |

**Shipping threshold: weighted score ≥ 8.5 and no hard fail.** For snapshot and documentary briefs, criterion 9 must be at least 8.

## Repair map

| Problem | Global fix (new brief) | Local fix (edit, low complexity) |
|---|---|---|
| Plastic, airbrushed skin | "unretouched, visible pores, uneven tone"; documentary register | restore skin texture, keep identity |
| Glossy stock look | amateur or photojournalist photographer; mundane clutter; one imperfection | — |
| Flat light from nowhere | one key source with direction and Kelvin | — |
| Creamy blur in a phone shot | "background mostly in focus, as from a phone" | — |
| Warm or yellow cast | "neutral white balance, no warm cast" | correct white balance only |
| Duplicated or misplaced limbs, impossible pose | fewer people and hands in frame; say who the hands belong to; one simple pose | remove the extra limb with a masked edit |
| AI-typical high contrast | soft, low-contrast natural light; open shadows; straight-out-of-camera colours | lower contrast and saturation only |
| Bad hands | give the hands a task, fewer visible hands | masked edit of the hand |
| Gibberish text | remove text or quote it exactly | edit only the sign |
| Cellular texture in foliage, fur, fog | less fine organic texture, out of focus, ≤ 2K size | replace the region |
| Edit changed other areas | lower complexity, restate invariants, use a mask | restart from last approved image |

One change per iteration, invariants restated every time, at most three rounds. If an image still has a flaw after that, the agent delivers the best one and names the flaw.

## Tools

**Contact sheet** — candidates side by side, optionally with a 3× centre crop row for texture inspection:

```bash
python3 scripts/contact_sheet.py images/*.png -o images/sheet.jpg --crops
```

**Photo finish** — an optional, subtle optical pass for images that still look too clean: luminance grain, lens vignetting, lateral chromatic aberration and a soft highlight shoulder. ICC profile, EXIF, XMP and DPI are kept and no camera data is invented. Files that carry C2PA provenance data are refused, because new pixels would drop the manifest.

```bash
python3 scripts/photo_finish.py in.png -o out.png --grain 0.25 --vignette 0.15 --ca 0.6 --rolloff 0.2
```
