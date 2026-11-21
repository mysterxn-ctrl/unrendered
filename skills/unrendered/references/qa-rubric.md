# QA rubric — judge like a photo editor who hunts AI fakes

Look at **every** candidate as a whole, then at every enlarged tile from `scripts/qa_tiles.py` — corners and edges included. **Count bodies and limbs first:** trace every hand and arm back to a shoulder of one plausible body; count arms, hands and fingers per person; check that each pose is physically possible. Then mentally zoom into: eyes, teeth, ears, hands/fingers, feet, hairline, jewellery, text/signage, reflections, shadows, contact points, background people, repeating textures, edges between subject and background.

## Hard fails (any one → cannot ship; repair or regenerate)

1. Wrong anatomy: extra, duplicated or misplaced arms, hands or legs; limbs that cannot belong to a visible or plausible body; anatomically impossible body positions; extra/missing/fused fingers, impossible joints, mismatched eyes (different iris size, direction or catchlights), melted ears, too many teeth.
2. Gibberish or misspelled text where text is visible and readable.
3. Physically impossible light: shadows in contradictory directions, subject lit with no source, missing contact shadows (floating objects).
4. Object fusion/merging: hand merges into cup, glasses merge into hair, chair legs disappear into floor.
5. Duplicated/cloned faces or objects; pattern repetition (tiling, Voronoi/cellular texture, mesh-like noise).
6. Violates a user must-have / must-not, or has a watermark/logo not requested.
7. Distorted background people (melted faces) in focus.
8. Unwanted change outside the edit area (for edits).

## Scored criteria (0–10 each; weight)

| # | Criterion | Weight | 10 looks like |
|---|---|---|---|
| 1 | Prompt fidelity | 1.0 | Every specified element present, nothing unrequested added |
| 2 | Light physics | 1.5 | One coherent key, matching shadows/catchlights/speculars, correct colour temperature |
| 3 | Optics coherence | 1.0 | DOF, perspective, distortion consistent with stated lens/aperture/distance |
| 4 | Human realism | 1.5 | Skin texture, asymmetry, natural expression, believable hands with a task |
| 5 | Material & world realism | 1.0 | Correct materials, wear, clutter, contact, reflections, refraction |
| 6 | Capture authenticity | 1.0 | Plausible noise/grain, dynamic range, slight imperfections fitting the genre |
| 7 | Composition plausibility | 0.75 | A human would plausibly frame it this way for this purpose |
| 8 | Colour naturalness | 0.75 | Neutral/believable WB, no grade unless requested, restrained saturation and contrast (no crushed blacks next to glowing highlights) |
| 9 | "AI sheen" absence | 1.5 | No plastic skin, no glow, no hyper-clean surfaces, no over-sharpened micro-contrast |
| 10 | Technical cleanliness | 1.0 | No artifacts, banding, halos, mushy textures at 100% |

Score = weighted mean. Ship threshold: **≥ 8.5 and no hard fail**. For vernacular/documentary briefs, criterion 9 must be ≥ 8.

Write the QA as a short table per candidate in your working notes; tell the user only the winner's score and any remaining flaw.

## Failure → repair map

| Observed | Global fix (revise brief → regenerate) | Local fix (masked edit) |
|---|---|---|
| Plastic/airbrushed skin | Add "unretouched, visible pores, fine vellus hair, uneven tone, T-zone shine"; switch register to documentary/vernacular; remove beauty words | Edit face: "restore natural skin texture with visible pores; keep identity, expression, lighting identical" |
| Glossy stock/ad look | Cast an amateur or photojournalist; add mundane clutter; available light only; add 1 imperfection | — |
| Light from nowhere / flat | Name one key source + direction + Kelvin; specify what clips | — |
| Too-perfect symmetry/pose | Mid-action verb, weight shift, look-away gaze | — |
| Creamy bokeh in a phone/wide shot | State deep DOF explicitly ("background mostly in focus, as from a phone") | — |
| Warm/yellow cast | "neutral white balance, no warm or sepia cast" + name the Kelvin | Edit: "correct white balance to neutral daylight; change nothing else" |
| Teal-orange / cinematic grade | "ungraded, straight-out-of-camera colours" | — |
| Duplicated/misplaced limbs, impossible pose | Fewer people and hands in frame; state who the hands belong to and where the person sits or stands; describe one simple pose | Masked edit: remove the extra limb and rebuild the area; restate the remaining pose |
| AI-typical high contrast / glossy look | "soft, low-contrast natural light, open shadows, unretouched, straight-out-of-camera colours"; drop dramatic or moody words | Edit: "lower contrast and saturation to natural levels; change nothing else" |
| Bad hands | Give hands a concrete task; reduce number of visible hands; choose framing that crops them naturally | Masked edit of the hand region: "a natural relaxed right hand with five fingers holding X; keep everything else" |
| Gibberish text | Remove text or quote exact text + typography; spell tricky words letter by letter | Edit only the sign: exact text in quotes |
| Cellular/noise texture in foliage, fur, fog, crowds | Reduce area of fine organic texture, move it out of focus, simpler subject; drop contradictory style words; stay ≤ 2K | Edit region: "replace with clean natural texture" |
| Background people melted | Fewer people, farther away, out of focus | Edit: remove or blur them |
| Composition shifted at 2K+ | Generate at native ≤ 2560×1440; upscale externally if needed | — |
| Edit changed other areas | restate every invariant, use a mask, describe only the change | Start again from the last approved version |

Rule: **one change per iteration**, restate all invariants, keep the last approved image as fallback.
