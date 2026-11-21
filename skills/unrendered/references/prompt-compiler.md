# Prompt compiler — one shot, right the first time

An image model renders the brief literally and fills every gap with its own average: a glossy stock look, a generic face, a pose from nowhere, limbs it invents to connect hands it was told about. A one-shot result therefore depends on two things, both done **before** the render:

1. **Choose a composition the model renders reliably** (section 1).
2. **Leave no gap** in which an error can grow: every person placed, every visible hand assigned, every face, material, lens and light written out, nothing contradictory (sections 2–4).

There is no inspection afterwards by default, so the brief carries the whole quality.

## 0. Inputs to extract (silently, from the request + context)

| Field | Question | Default if unstated |
|---|---|---|
| Subject | Who/what exactly? | Make it specific (age, look, material) without adding new characters |
| Purpose | Where will it be used? | "realistic photo" |
| Register | vernacular / documentary / commercial | documentary for scenes & people, commercial for products |
| Genre | which recipe in `photo-genres.md` | best match |
| Place & time | where, season, time of day, weather | plausible & specific |
| Mood | what should a viewer feel | from the request |
| Exact text | any words visible? | none — "no readable text anywhere" |
| Must keep / must avoid | user constraints | — |
| Aspect | where shown | from genre |

Specificity policy:
- If the user wrote a detailed spec → **normalise** it into the template, keep their choices, add only what is missing (bodies, physics, capture).
- If the user wrote a one-liner → **decide like a professional photographer**: casting, place, light, lens, pose. Do NOT add extra main characters, brands, slogans or story beats that aren't implied.
- If reference images exist (a person, a pose, a product, a room), pass them as references — a reference removes more guesswork than any sentence.

## 1. Design out the failure points (before writing a word)

Never change *what* the user asked for. Among the ways to show it, pick the one with the fewest of these risk elements, and handle every risk element that remains exactly as described.

| Risk element | Why it fails | One-shot choice |
|---|---|---|
| Hands as the subject (close-up of hands) | The model invents arms to connect hands it cannot attach to a body | Keep forearms in frame and say whose hands they are, from which side they enter and where the body is ("seen over the shoulder of the man at the desk"); at most two hands |
| People touching (handshake, hug, holding hands, arm around a shoulder) | Limbs merge or swap between people | At most two people in contact; describe each person's arms separately and which hand touches what — or choose the moment just before or after the contact |
| More than three people in focus | Duplicated faces, extra limbs | At most three people in focus; everyone else far away, partly hidden or out of focus |
| Complex or athletic pose (dance, sport mid-air, yoga) | Impossible joints | A stable, well-known moment of that activity; describe it joint by joint |
| Small tools in hands (pen, chopsticks, needle, cards, phone) | Wrong grip, extra fingers | Name the grip exactly ("pen between thumb and index finger, resting on the middle finger"); choose a camera angle that shows the grip from the side |
| Interlaced fingers, crossed arms, hand on hand | Fused fingers | Keep hands apart, each on its own object |
| Big laughter, teeth in close-up | Wrong teeth | Closed or slightly open mouth, unless laughter is the point — then medium shot, not close-up |
| Legs under tables, people behind objects | Missing or extra legs | Frame above the table, or state where the legs are |
| Text in the image | Gibberish | Only when asked; quote it exactly; few, short lines, large and facing the camera; spell unusual words letter by letter; otherwise "no readable text anywhere" |
| Screens, charts, dashboards | Nonsense content | Screen dark, angled away or out of focus — or describe one simple, specific content |
| Mirrors, reflections, glass walls | Inconsistent reflections | Avoid unless asked; otherwise say exactly what is reflected |
| Fine repeating texture filling the frame (foliage, fur, crowds, fog) | Cellular patterns | Smaller area, partly out of focus |
| Wide lens close to a face | Distortion | 50–85 mm for faces, unless a selfie look is wanted |
| Sizes above 2560×1440 | More artifacts, composition shifts | Native size from `models.json` |

## 2. Writing rules the model follows

- **Most important first:** subject and action, then bodies and faces, then camera and light, then texture and colour.
- **One fact per sentence.** Long chains of adjectives get averaged away.
- **Anchor everything in the frame:** left/right third, foreground/background, distance, facing direction, and what is in front of what ("the cup is in front of his chin").
- **One block per person, always in the same order:** position → body and weight → right hand → left hand → face.
- **Describe the correct state positively.** "His right hand holds the pen between thumb and index finger" works; listing anatomy errors to avoid ("no extra fingers") names exactly what you do not want. The Avoid line is for style only.
- **Count:** number of people, visible hands, objects ("two cups, one phone").
- **Concrete nouns over adjectives:** "pilled navy merino sweater", not "cosy sweater".
- **No contradictions:** phone camera ↔ deep focus; f/1.8 at 85 mm ↔ blurred background; light from camera-left ↔ shadows falling right; time of day ↔ colour temperature.
- **No AI-art vocabulary** (`8k, ultra-detailed, hyperrealistic, masterpiece, award-winning, trending, octane, unreal engine, stunning, epic, flawless, perfect`).

## 3. Template (GPT-Image dialect — labelled natural-language sections)

```
A real photograph, not an illustration or render.

Photographer & purpose: <who took it, why, for what — e.g. "candid snapshot taken by a friend on a smartphone to share in a group chat">
Scene: <specific place, time of day, season, weather; specific objects and clutter, counted>
Subject: <person/object with concrete physical specifics; what they are doing; clothing materials and wear>
Bodies & pose: <whenever a person or any body part is visible — one block per person: where they are (seated/standing, which part of the frame, facing where); weight and support; right hand: what it does and how it grips; left hand: the same; which limbs leave the frame and where the body continues>
Face & expression: <the emotion of this moment as eyes, brows, mouth and gaze target; natural asymmetry — never just "smiling">
Composition: <shot size, camera height & angle, subject placement, what crosses the frame edges, aspect>
Camera & capture: <body/phone, focal length, aperture, shutter, ISO; focus point; resulting depth of field>
Light: <the one motivated key source + direction + colour temperature; fill from the environment; what clips; where shadows fall>
Texture & realism: <each main material with its texture and wear — skin pores, flyaway hair, fabric weave and creases, wood grain, scuffs, smudges; 1–3 capture artifacts: grain, slight motion blur, mild vignetting, slight horizon tilt>
Colour: <neutral white balance for this light; saturation level; no grade unless wanted>
Text: <"EXACT TEXT" with placement and typography | No readable text anywhere.>
Avoid: airbrushed or smoothed skin, plastic sheen, CGI/3D-render look, HDR glow, cinematic colour grade, watermark, logos<, + request-specific style items>.
```

Length: 120–250 words; up to ~300 with several people or exact text. Every sentence must change pixels.

## 4. Pre-flight (text only — before the one render)

Read the brief once against this list and fix it before sending:

- [ ] Section 1 applied: no avoidable risk element left, and every remaining one handled as described?
- [ ] People counted; each one placed in the frame and facing somewhere?
- [ ] Every visible hand: owner, side, task, grip? Hands close-up: whose, from which side, where the body is?
- [ ] Pose as physics: weight, support, what touches what?
- [ ] Expression as eyes + brows + mouth + gaze target for this moment?
- [ ] Each main material named with its texture and wear?
- [ ] Lens, aperture, distance and depth of field agree? Light direction, shadows and colour temperature agree?
- [ ] Exact text quoted and short — or "no readable text anywhere"?
- [ ] Zero AI-art words, zero anatomy negations, nothing the user did not imply?

## 5. Worked examples

### A) User: "Ein Mann trinkt Kaffee"
```
A real photograph, not an illustration or render.

Photographer & purpose: candid documentary photo taken by a friend sitting across the table, for a personal photo album.
Scene: small neighbourhood café in Hamburg on a grey November morning; rain-speckled window, condensation at the glass edges, one crumpled sugar wrapper and half a croissant on a scratched dark-wood table, two other customers far behind him, out of focus.
Subject: a man in his late 40s with a short salt-and-pepper beard and reading glasses pushed up on his head, wearing a pilled navy merino sweater, drinking his morning coffee.
Bodies & pose: one person, seated alone at a small table in the right half of the frame, body turned slightly towards the window on camera-left; right elbow on the table, his right hand holds a white ceramic cup by the handle just below his mouth; left forearm lies on the table, left hand flat beside the saucer; shoulders a little hunched forward, weight on the chair and both forearms.
Face & expression: lips pursed, blowing gently on the coffee; eyes half-lowered towards the window, brows relaxed; a quiet, still-tired early-morning look; the left corner of the mouth slightly higher than the right.
Composition: medium close-up from across the table at seated eye level, edge of the window frame entering left, 3:2.
Camera & capture: full-frame mirrorless, 50mm at f/2.8, 1/125s, ISO 1600; focus on his near eye; the café behind him softly blurred but recognisable.
Light: overcast daylight from the window camera-left as the only key (~6500K), a warm tungsten pendant faintly behind; the window side of his face brighter, gentle falloff into shadow on the right.
Texture & realism: visible skin pores and fine lines, stray beard hairs, pilled wool at the elbows, scratched and worn wood grain, faint steam against the dark background, slight ISO grain in the shadows, horizon very slightly tilted.
Colour: neutral cool-daylight white balance with a little warm spill from the pendant; muted saturation.
Text: no readable text anywhere.
Avoid: airbrushed skin, glossy commercial look, cinematic colour grade, watermark, logos.
```

### B) User: "Hände haken eine Checkliste ab" (hands as the subject — the classic failure case)
A one-liner like this produces disembodied, misplaced arms: the model is told about hands but not about a body. The one-shot version gives the hands an owner, a position and a grip:
```
A real photograph, not an illustration or render.

Photographer & purpose: candid photo taken by a colleague across the meeting table, for the company's internal newsletter.
Scene: bright meeting room with floor-to-ceiling windows onto green alpine slopes, overcast midday; a dark oak table with one printed A4 checklist, one espresso cup on a saucer and one phone lying face down.
Subject: a man in his 50s with short grey hair, navy wool suit, white shirt, steel wristwatch on his left wrist.
Bodies & pose: one person, seated at the table in the right half of the frame, facing camera-left, torso leaning slightly over the paper; his right forearm rests on the table edge, his right hand holds a black ballpoint pen between thumb and index finger, resting on the middle finger, the tip ticking the third box; his left hand lies flat on the upper corner of the sheet, holding it still. Both forearms are visible up to the elbows, his shoulders and head are in frame.
Face & expression: concentrated; brows slightly drawn, lips closed, eyes on the pen tip.
Composition: three-quarter view from across the table, camera slightly above table height, the sheet in the lower third, 4:5.
Camera & capture: full-frame camera, 50mm at f/4, 1/125s, ISO 400; focus on the pen tip and the sheet; his face slightly soft, the windows behind him blurred.
Light: overcast daylight from the windows behind him and camera-left (~6000K); soft shadows of hand and pen on the paper, falling to the right.
Texture & realism: paper fibre and a slight curl at the sheet's corner, fine wool weave of the suit, creases at the knuckles, scuffs on the oak, slight grain.
Colour: neutral daylight white balance, natural muted colours.
Text: the sheet is headed "STRATEGISCHE ANALYSE" in bold sans-serif; below it six printed lines, each a box and one word: "Marktpotenziale", "Wettbewerbsanalyse", "Wachstumsstrategie", "Risikobewertung", "Investitionsbedarf", "Umsetzungsplan"; black on white, large enough to read.
Avoid: airbrushed skin, glossy commercial look, cinematic colour grade, watermark, logos.
```

### C) User: "Produktfoto von einer Ledertasche für Onlineshop"
```
A real commercial product photograph, not a 3D render.

Photographer & purpose: e-commerce studio photographer shooting the hero image for a product page.
Scene: seamless warm-light-grey paper backdrop with a gentle falloff towards the top; the bag stands on the paper.
Subject: a medium-size cognac full-grain leather tote with visible pores and natural grain variation, slightly darker burnished edges, hand-stitched seams with tiny irregularities, brass hardware with soft micro-scratches, handles relaxed (not perfectly upright), slight creasing where the handles meet the body.
Composition: three-quarter front view from slightly above product mid-height, product fills ~65% of a 4:5 frame, centred with even padding.
Camera & capture: 100mm macro lens at f/11, 1/160s, ISO 100, tethered; everything on the bag sharp.
Light: large strip softbox camera-left at 45° as key (5500K), white bounce board camera-right for fill, small gridded backlight creating a subtle rim on the handle edge; soft, physically correct contact shadow under the base.
Texture & realism: true leather sheen (satin, not plastic), one or two tiny dust specks on the backdrop, real stitching thread texture.
Colour: accurate, colour-managed product colour; no grading.
Text: no logos, no text, no watermark.
Avoid: CGI-smooth surfaces, plastic sheen, impossible reflections.
```

### D) User: "Freunde auf einer Party"
→ **On-camera flash snapshot**, compact camera, 28mm, hard flash shadows on the wall behind. Three friends standing side by side, each written as one block: left — woman, right hand holding a plastic cup at chest height, left arm hanging; centre — man, left arm around the woman's shoulder (his hand visible on her far shoulder), right hand in his jeans pocket; right — woman, both hands around a bottle at waist height. Mid-laugh with crinkled eyes and closed or slightly open mouths, one of them blinking. String lights blown to white dots, foreground shoulder of another guest cut by the frame edge, slight overexposure on the closest face, 3:2, fine grain. Avoid: posed line-up, studio light.

### E) User: "Skyline von Frankfurt bei Nacht"
→ **Night ambient / tripod landscape** from the Main river bank (Eiserner Steg area), 35mm f/8, 10s, ISO 100 on a tripod: light trails, reflections broken by water ripples, sodium and LED mix, sky deep blue not black (blue hour, 20 min after sunset), some windows lit at random, mild flare stars from f/8, no fireworks, no dramatic storm clouds, no readable signage.

## 6. Dialects for other model families (record the right one in `models.json`)

- **Natural-language models (GPT-Image, Gemini/Nano Banana, MAI, most 2025+ models):** the template above.
- **Tag/weight models (SD-family, some Flux/Kling deployments):** comma-separated physical descriptors in priority order; bodies and hands still assigned explicitly; put the Avoid list into the `negative_prompt` field if the provider supports it; keep weights modest; no AI-art vocabulary.
- **Short-prompt models:** compress to the most load-bearing facts: register and photographer, subject and action, each visible hand's task, place and light, lens and depth of field, one imperfection.
