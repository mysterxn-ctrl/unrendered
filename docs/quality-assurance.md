# Quality assurance

Unrendered works one-shot: the brief prevents the errors, the image is rendered once and delivered, and no inspection pass runs afterwards — checks cost tokens. This page describes what happens **when you ask for a check or point out a flaw**. The same five areas are what the brief controls in advance ([Photorealism guide](photorealism.md)).

On request, the agent inspects the image like a photo editor hunting for fakes: the whole frame, then the relevant regions at full detail through enlarged, overlapping tiles, because an agent usually sees a whole image downscaled.

The five things that give an image away are checked first, in this order: **limbs, pose, facial expression, texture and optics**. The agent writes down what it actually sees ("right hand, five fingers, holds the pen between thumb and index finger"), not "hands look fine".

## What the agent checks

| | Checks |
|---|---|
| **Limbs** | Counts the people and each person's arms, hands, legs and feet. Traces every arm from shoulder to hand; a limb that belongs to no plausible body fails. Checks that each hand sits on the correct arm, sleeves run continuously, proportions fit, and every hand has five fingers with the right joints. |
| **Pose** | Weight over the feet or on the seat, nothing floating; joints bending only the way they can; contact and grip that work (a pen between thumb, index and middle finger, tip on the paper); a posture that fits the action instead of a stiff, symmetric stance. |
| **Facial expression** | Eyes and mouth tell the same emotion (a real smile narrows the eyes); both eyes look at the same, sensible point; natural asymmetry; plausible teeth; an expression that belongs to the moment, not the generic stock face. |
| **Texture** | Pores, fine lines and vellus hair on skin in focus; strands and flyaways in hair; weave, creases and pilling in fabric; grain, fibre, scratches and smudges on materials; no repeating patterns; sharp detail in the focus plane and smooth blur outside it. |
| **Optics** | Depth of field that fits lens, aperture and distance, with blur growing steadily away from the focus plane; consistent perspective; lens character of the stated camera; no glow, bloom or halo; the same grain across the frame; each material keeping its own colour instead of one tint over everything. |

Then light and shadows, contact shadows, text letter by letter and reflections.

## Hard fails

Any one of these fails an image, whatever its score:

1. **Limbs:** an extra, missing, duplicated or misplaced arm, hand, leg or foot; a limb that belongs to no plausible body; a hand on the wrong arm; extra, missing or fused fingers.
2. **Pose:** a joint bent the impossible way, a body that floats or is unsupported, a grip or contact that cannot work.
3. **Face:** eyes looking in different directions without reason, mismatched catchlights, melted or doubled features, wrong teeth.
4. **Texture:** waxy, poreless or plastic skin, or painted-looking surfaces, in the plane of focus.
5. Gibberish or misspelled text where text is readable.
6. Physically impossible light — contradictory shadows, a subject lit by nothing, missing contact shadows.
7. Fused objects, duplicated objects or repeating texture patterns.
8. A violated user requirement, or an unrequested watermark or logo.
9. Distorted background people in focus.
10. *Edits:* anything changed outside the requested area.

## Scored criteria

| # | Criterion | Weight | A 10 looks like |
|---|---|---|---|
| 1 | Limbs & anatomy | 1.5 | every limb counted, traced to its body, on the correct side, in proportion |
| 2 | Pose | 1.5 | weight, balance, contact and grip that physically work; natural posture for the action |
| 3 | Facial expression | 1.25 | eyes and mouth agree, gaze makes sense, an expression that belongs to the moment |
| 4 | Texture | 1.5 | real skin, hair, fabric and material detail in focus; no waxy or painted surfaces |
| 5 | Optics | 1.25 | depth of field, perspective, lens character and grain consistent; no glow |
| 6 | Light physics | 1.0 | one coherent key; matching shadows, catchlights and colour temperature |
| 7 | Prompt fidelity | 1.0 | everything requested, nothing unrequested |
| 8 | Colour | 0.75 | believable white balance; each material keeps its own colour |
| 9 | Composition | 0.75 | a person would plausibly frame it this way |
| 10 | Technical cleanliness | 0.5 | no artifacts, banding, halos or mushy areas |

**An image passes only with no hard fail, a weighted score of at least 8.5, and at least 8 in each of criteria 1–5.** A high average cannot hide one bad hand, a stiff pose, a dead expression or waxy skin.

## Repair map

| Problem | Global fix (new brief) | Local fix (masked edit) |
|---|---|---|
| Extra, duplicated or misplaced limb | fewer people and visible hands; for each person where they sit or stand and what each hand does; for hand close-ups whose hands they are and where the body is | remove the limb, rebuild the area |
| Bad fingers or grip | one concrete task per hand; describe the grip | masked edit of the hand |
| Stiff, impossible or floating pose | one simple, physically described pose: weight, support, what touches what | — (regenerate) |
| Fake or generic expression | describe the moment and the face: eyes, brows, mouth, gaze target | change only the expression, keep identity |
| Plastic, waxy skin | "unretouched, visible pores, fine vellus hair, uneven tone"; documentary register | restore skin texture, keep identity |
| Smooth, painted materials | name each main material and its wear | real material texture in the masked area |
| Wrong depth of field, pasted-on subject | consistent focal length, aperture and distance | — |
| Glow, halo, "beauty" sheen | "no glow, no bloom, no halo, straight-out-of-camera" | — |
| One grade over everything, warm cast | "ungraded, neutral white balance for <light>" | correct white balance only |
| Gibberish text | remove text or quote it exactly | edit only the sign |
| Cellular texture in foliage, fur, fog | less fine organic texture, out of focus, ≤ 2K size | replace the region |
| Edit changed other areas | restate every invariant, use a mask, describe only the change | restart from last approved image |

One change per iteration, invariants restated every time, always continuing from the last approved image.

## Tools

**Tiles** — an image cut into enlarged, overlapping tiles plus one whole-frame view, each tile labelled with its position:

```bash
python3 scripts/qa_tiles.py images/candidate-1.png -o images/qa
```

**Contact sheet** — several images side by side, optionally with a 3× centre crop row:

```bash
python3 scripts/contact_sheet.py images/*.png -o images/sheet.jpg --crops
```

**Photo finish** — an optional, subtle optical pass when you want a less clean look: luminance grain, lens vignetting, lateral chromatic aberration and a soft highlight shoulder. ICC profile, EXIF, XMP and DPI are kept and no camera data is invented. Files that carry C2PA provenance data are refused, because new pixels would drop the manifest.

```bash
python3 scripts/photo_finish.py in.png -o out.png --grain 0.25 --vignette 0.15 --ca 0.6 --rolloff 0.2
```
