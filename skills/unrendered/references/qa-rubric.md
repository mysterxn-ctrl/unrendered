# QA rubric — judge like a photo editor who hunts AI fakes

Used in Step 4 right after the one render. The same five areas are prevented in the brief by `prompt-compiler.md`, so a good brief leaves this check little to find.

The five things that give an image away are **limbs, pose, facial expression, texture and optics**. Check them in this order, on the whole frame and then on every enlarged tile from `scripts/qa_tiles.py` (corners and edges included). Write down what you actually see — "right hand, five fingers, holds the pen between thumb and index finger" — not "hands look fine".

## Inspection checklist

### 1. Limbs (whole frame first, then tiles)
- Count the people, including anyone only partly in frame. For each person count arms, hands, legs, feet: two of each, no more.
- Trace every arm from the shoulder through elbow and wrist to the hand. A limb that cannot be traced to a body that is visible or plausibly just outside the frame is a fail.
- Side check: a right hand has its thumb on the left when you see the back of the hand with fingers up; it belongs to the right arm. A right hand on a left sleeve, or two hands that would need crossed arms the pose does not show, is a fail.
- Sleeves run continuously from shoulder to cuff; the same fabric, colour and cuff on both arms of one person.
- Proportions: forearm about as long as the hand plus wrist; upper arm slightly longer than forearm; a hand roughly as long as the face from chin to hairline.
- Fingers: five per hand, three joints each (two on the thumb), nails on the correct side, no fingers merging with each other or with objects.
- Legs and feet under tables and chairs: the number fits the people sitting there.

### 2. Pose (body mechanics)
- Weight and support: a standing body has its weight over its feet; a seated body sits *on* the chair with hips back and knees bent; nothing floats.
- Joints bend only the way they can: elbows and knees in one direction, wrists not twisted beyond about 90°, no shoulder that would have to dislocate to reach.
- Contact: a hand resting on a table shows slight pressure and bent fingers; a hand holding a cup or pen grips it plausibly (a pen between thumb, index and middle finger, tip on the paper).
- The pose fits the action and the moment: someone writing leans slightly toward the paper, someone listening turns head and shoulders toward the speaker.
- Not a mannequin: no stiff, symmetric stance; shoulders, hips and head are slightly turned relative to each other.

### 3. Facial expression (Mimik)
- Eyes and mouth tell the same emotion. A real smile narrows the eyes and lifts the cheeks (crow's feet); a smile only in the mouth reads as fake.
- Both eyes look at the same point, and that point makes sense in the scene; catchlights match the light source in both eyes.
- Natural asymmetry: slightly different eyelid heights or mouth corners; not a mirrored face.
- Teeth: a plausible number and shape, not a single white strip.
- The expression fits the moment the brief describes (concentration, mid-sentence, surprise) — not the generic, pleasant stock face.
- Background faces: no melted or doubled features on any face that is in focus.

### 4. Texture (enlarged tiles)
- Skin in the focus plane: pores, fine lines, small irregularities in tone, vellus hair, natural shine on forehead and nose. Waxy, poreless or painted-looking skin is a fail.
- Hair: individual strands and flyaways at the edges, not a smooth helmet.
- Fabric: weave or knit visible at full detail, creases where the body bends, pilling or lint on wool.
- Materials: wood grain, paper fibre, scratches on metal, smudges on glass; detail scale consistent (pores not larger than freckles, wood grain not as coarse as bark).
- No repeated or cellular pattern in foliage, fur, fog, crowds or backgrounds.
- Detail follows focus: sharp, real texture in the focus plane, smooth blur outside it — not uniform sharpness everywhere, and not mushy "smeared" detail where things should be sharp.

### 5. Optics (the look)
- Depth of field fits focal length, aperture and distance; blur grows steadily with distance from the focus plane. A sharp subject pasted on uniform blur is a fail.
- Perspective: lines that are parallel in reality converge consistently; the horizon and vanishing points of table, window and floor agree.
- Lens character fits the stated camera: mild vignetting, slight chromatic fringing at hard edges, flare only from a light in or near the frame.
- No glow, bloom or halo around people or objects; no shiny "beauty" sheen on surfaces.
- Grain or noise is the same across the frame (in shadows as in midtones), not absent in some areas and present in others.
- Colour: each material keeps its own colour under the stated light; one tint laid over every surface (the "cinematic grade") is a tell.

Then check the rest: light direction and shadows, contact shadows, text letter by letter, reflections.

## Hard fails (any one → cannot ship; repair or regenerate)

1. **Limbs:** an extra, missing, duplicated or misplaced arm, hand, leg or foot; a limb that belongs to no plausible body; a hand on the wrong arm; extra, missing or fused fingers.
2. **Pose:** a joint bent the impossible way, a body that floats or is unsupported, a grip or contact that cannot work.
3. **Face:** eyes looking in different directions without reason, mismatched catchlights, melted or doubled features, wrong teeth.
4. **Texture:** waxy, poreless or plastic skin, or painted-looking surfaces, in the plane of focus.
5. Gibberish or misspelled text where text is visible and readable.
6. Physically impossible light: shadows in contradictory directions, subject lit by no source, missing contact shadows.
7. Objects fused together (hand into cup, glasses into hair, chair legs into floor); duplicated objects or repeating texture patterns.
8. A user must-have missing or a must-not present; an unrequested watermark or logo.
9. Distorted background people in focus.
10. For edits: anything changed outside the requested area.

## Scored criteria (0–10 each; weight)

| # | Criterion | Weight | 10 looks like |
|---|---|---|---|
| 1 | Limbs & anatomy | 1.5 | every limb counted, traced to its body, on the correct side, in proportion |
| 2 | Pose | 1.5 | weight, balance, contact and grip that physically work; a natural, slightly asymmetric posture fitting the action |
| 3 | Facial expression | 1.25 | eyes and mouth agree, gaze makes sense, asymmetry, an expression that belongs to this moment |
| 4 | Texture | 1.5 | real skin, hair, fabric and material detail in the focus plane; no waxy or painted surfaces |
| 5 | Optics | 1.25 | depth of field, perspective, lens character and grain consistent with the stated camera; no glow |
| 6 | Light physics | 1.0 | one coherent key; matching shadows, catchlights and colour temperature |
| 7 | Prompt fidelity | 1.0 | everything requested, nothing unrequested |
| 8 | Colour | 0.75 | believable white balance; each material keeps its own colour; no grade unless asked |
| 9 | Composition | 0.75 | a person would plausibly frame it this way for this purpose |
| 10 | Technical cleanliness | 0.5 | no artifacts, banding, halos or mushy areas at full detail |

Score = weighted mean. **Ship only if: no hard fail, weighted score ≥ 8.5, and each of criteria 1–5 is at least 8.** A high average must not hide one bad hand, a stiff pose, a dead expression or waxy skin.

Write the QA as a short table in your working notes; tell the user the score and any flaw found.

## Failure → repair map

| Observed | Global fix (revise brief → regenerate) | Local fix (masked edit) |
|---|---|---|
| Extra, duplicated or misplaced limb; hand on the wrong arm | Fewer people and fewer visible hands; state for each person where they sit or stand and what each hand does; for hand close-ups say whose hands they are and where the body is | Mask the limb: remove it and rebuild the area; restate the remaining pose |
| Bad fingers or grip | Give each hand one concrete task; describe the grip ("pen between thumb and index finger") | Mask the hand: "a natural relaxed right hand with five fingers holding X; keep everything else" |
| Stiff, impossible or floating pose | One simple, physically described pose: weight, support, what touches what | — (regenerate; pose edits rarely hold) |
| Fake or generic expression | Describe the moment and the face: eyes, brows, mouth, gaze target ("eyes on the paper, brows slightly drawn, lips pressed") | Mask the face: "change only the expression to …; keep identity, lighting and everything else identical" |
| Plastic, waxy or airbrushed skin | "unretouched, visible pores, fine vellus hair, uneven tone, T-zone shine"; documentary register; no beauty words | Mask the face or skin: "restore natural skin texture with visible pores; keep identity, expression, lighting identical" |
| Smooth, painted materials | Name each main material and its wear (scuffed oak, pilled wool, smudged glass) | Mask the area: "real <material> texture with <wear>" |
| Wrong depth of field or pasted-on subject | State focal length, aperture and distance consistently; "background mostly in focus, as from a phone" for phone shots | — |
| Glow, halo or "beauty" sheen | "no glow, no bloom, no halo, straight-out-of-camera" | — |
| One grade over everything | "ungraded, straight-out-of-camera colours; neutral white balance for <light>" | Edit: "neutral white balance and natural colours; change nothing else" |
| Warm or yellow cast | "neutral white balance, no warm or sepia cast" + Kelvin | Edit: "correct white balance to neutral daylight; change nothing else" |
| Light from nowhere | One key source with direction and Kelvin; what clips | — |
| Gibberish text | Remove text or quote exact text + typography; spell tricky words | Edit only the sign: exact text in quotes |
| Cellular texture in foliage, fur, fog, crowds | Less fine organic texture, move it out of focus; stay ≤ 2K | Edit region: "replace with clean natural texture" |
| Background people melted | Fewer people, farther away, out of focus | Edit: remove or blur them |
| Composition shifted at 2K+ | Generate at native ≤ 2560×1440 | — |
| Edit changed other areas | Restate every invariant, use a mask, describe only the change | Start again from the last approved version |

Rule: **one change per iteration**, restate all invariants, keep the last approved image as fallback.
