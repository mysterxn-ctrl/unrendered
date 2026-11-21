# Prompt compiler — from a one-liner to a photographer's brief

## 0. Inputs to extract (silently, from the request + context)

| Field | Question | Default if unstated |
|---|---|---|
| Subject | Who/what exactly? | Make it specific (age, look, material) without adding new characters |
| Purpose | Where will it be used? | "realistic photo" |
| Register | vernacular / documentary / commercial | documentary for scenes & people, commercial for products |
| Genre | which recipe in `photo-genres.md` | best match |
| Place & time | where, season, time of day, weather | plausible & specific |
| Mood | what should a viewer feel | from the request |
| Exact text | any words visible? | none — "no text, no logos, no watermark" |
| Must keep / must avoid | user constraints | — |
| Aspect | where shown | from genre |

Specificity policy:
- If the user wrote a detailed spec → **normalise** into the template, keep their choices, add only physics/capture consistency they omitted.
- If the user wrote a one-liner → **augment like a professional photographer** would: casting, place, light, lens, imperfection. Do NOT add extra main characters, brands, slogans or story beats that aren't implied.

## 1. Template (GPT-Image dialect — labeled natural-language sections)

```
A real photograph, not an illustration or render.

Photographer & purpose: <who took it, why, for what — e.g. "candid snapshot taken by a friend on a smartphone to share in a group chat">
Scene: <specific place, time of day, season, weather; specific objects and clutter>
Subject: <person/object with concrete physical specifics; what they are doing mid-action; clothing materials and wear>
Bodies & pose: <whenever a person or any body part is visible: how many people; for each, where they are (seated/standing, which side of the frame, facing where); what each visible hand does, left and right; which limbs leave the frame and where the body continues; weight, support, what touches what>
Face & expression: <the emotion of this moment as eyes, brows, mouth and gaze target; natural asymmetry — never just "smiling">
Composition: <shot size, camera height & angle, subject placement, what crosses the frame edges, aspect>
Camera & capture: <body/phone, focal length, aperture, shutter, ISO; focus point; DOF consequence>
Light: <the one motivated key source + direction + colour temperature; fill from environment; what clips; shadow behaviour>
Texture & realism: <each main material with its texture and wear — skin pores, flyaway hair, fabric weave and creases, wood grain, scuffs, smudges; 1–3 capture artifacts: grain/noise, slight motion blur, mild vignetting, slight horizon tilt>
Colour: <neutral accurate white balance for this light; saturation level; no grade unless wanted>
Text: <"EXACT TEXT" with placement/typography | No readable text anywhere.>
Avoid: no airbrushed or smoothed skin, no plastic sheen, no CGI/3D-render look, no HDR glow, no cinematic colour grade, no perfect symmetry, no stiff posed stance, no extra or disembodied arms, hands or fingers, no watermark, no logos<, + request-specific>.
```

Length target: 120–250 words (up to ~300 with several people). Every sentence must change pixels; delete filler. The `Bodies & pose` and `Face & expression` lines are mandatory whenever a person or a body part is visible — that is where limb and pose errors are prevented.

### Dialects for other model families (record the right one in `models.json`)
- **Natural-language models (GPT-Image, Gemini/Nano Banana, MAI, most 2025+ models):** the template above.
- **Tag/weight models (SD-family, some Flux/Kling deployments):** comma-separated physical descriptors in priority order; put the Avoid list into the `negative_prompt` field if the provider supports it; keep weights modest; still no AI-art vocabulary.
- **Short-prompt models:** compress to the 5 most load-bearing facts: register+photographer, subject+action, place+light, lens+DOF, imperfection.

## 2. Worked examples

### A) User: "Ein Mann trinkt Kaffee"
```
A real photograph, not an illustration or render.

Photographer & purpose: candid documentary photo taken by a friend sitting across the table, for a personal photo album.
Scene: small neighbourhood café in Hamburg on a grey November morning; rain-speckled window, condensation at the glass edges, a crumpled sugar wrapper and a half-eaten croissant on a scratched dark-wood table, other customers soft and out of focus.
Subject: a man in his late 40s with a short salt-and-pepper beard and reading glasses pushed up on his head, wearing a pilled navy merino sweater, drinking his morning coffee.
Bodies & pose: one person, seated alone at a small table, body turned slightly towards the window on camera-left; right elbow on the table, his right hand holds a white ceramic cup by the handle just below his mouth; left forearm lies on the table, left hand flat beside the saucer; shoulders a little hunched forward, weight on the chair and both forearms.
Face & expression: lips pursed, blowing gently on the coffee; eyes half-lowered towards the window, brows relaxed; a quiet, still-tired early-morning look; the left side of the mouth slightly higher than the right.
Composition: medium close-up from across the table at seated eye level, subject slightly right of centre, edge of the window frame entering left, 3:2.
Camera & capture: full-frame mirrorless, 50mm at f/2.8, 1/125s, ISO 1600; focus on his near eye; background cafe softly blurred but recognisable.
Light: overcast daylight from the window camera-left as the only key (~6500K), warm tungsten pendant faintly behind; the window side of his face brighter, gentle falloff into shadow.
Texture & realism: visible skin pores and fine lines, stray beard hairs, pilled wool at the elbows, scratched and worn wood grain, steam faint against the dark background, slight ISO grain in shadows, horizon very slightly tilted.
Colour: neutral cool-daylight white balance with a little warm spill from the pendant; muted saturation.
Text: no readable text anywhere.
Avoid: no airbrushed skin, no glossy commercial look, no cinematic grade, no perfect symmetry, no watermark, no logos.
```

### B) User: "Produktfoto von einer Ledertasche für Onlineshop"
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
Avoid: no floating product, no impossible reflections, no CGI-smooth surfaces, no plastic sheen.
```

### C) User: "Freunde auf einer Party"
→ choose **On-camera flash snapshot**: compact camera direct flash, 28mm, hard shadows on wall, three friends standing shoulder to shoulder, each placed left/centre/right with one hand on a plastic cup and the other arm hanging or on a friend's shoulder (say which), mid-laugh with crinkled eyes, one blinking, plastic cups, string lights blown to white dots, foreground shoulder cut off, slight overexposure on the closest face, 3:2, fine grain. Avoid: posed lineup, studio light.

### D) User: "Skyline von Frankfurt bei Nacht"
→ **Night ambient / tripod landscape**: from the Main river bank (Eiserner Steg area), 35mm f/8, 10s, ISO 100 on tripod: light trails, reflections broken by water ripples, sodium and LED mix, sky deep blue not black (blue hour 20 min after sunset), some windows lit randomly, mild flare stars from f/8 aperture, no fireworks, no dramatic storm clouds.

## 3. Brief self-check before sending (30 seconds)

- [ ] Could I draw a lighting diagram from this? (one key, direction, temperature)
- [ ] Do focal length, aperture and distance agree with the described background blur?
- [ ] Number of people stated, each placed (seated/standing, side, facing)?
- [ ] Every visible hand assigned to a person and a side (left/right), with one concrete task and a grip that works?
- [ ] Close-up of hands or another body part: is it said whose they are and where the rest of the body is?
- [ ] Pose physically described — weight, support, what touches what?
- [ ] Expression written as eyes + brows + mouth + gaze target, tied to this moment?
- [ ] Each main material named with its texture and wear?
- [ ] Is there at least one specific, mundane, real-world object?
- [ ] 1–3 imperfections named — not more?
- [ ] Zero AI-art words? (`grep -i -E '8k|ultra|hyper|masterpiece|award|octane|unreal|stunning|epic|flawless|perfect'`)
- [ ] Exact text quoted, or "no readable text"?
- [ ] Nothing added that the user didn't imply (extra people, brands, story)?
