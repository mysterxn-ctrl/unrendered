# Photoreal playbook — why AI images look fake, and how real photos actually look

Image models are trained on billions of photos, but the most *upvoted*, *captioned* and *aesthetic* ones dominate what "a photo of X" means to them: glossy stock, retouched ads, cinematic stills. Real-life photos taken by humans are messier, more specific and more physically constrained. Believability comes from **physical consistency + human specificity + capture artifacts**, not from "more detail".

## 1. The core insight: realism ≠ beauty

The images people instantly accept as real are usually *ordinary*: a friend's phone shot at a kitchen table, a wedding guest's flash photo, a press photo with a crooked horizon. The images people instantly flag as AI are *too good*: perfect skin, perfect light from nowhere, perfect symmetry, perfect bokeh, no clutter, no reason to exist.

So for every request decide the **realism register**:
- **Vernacular** (phone snapshot, flash party pic, holiday photo) → most believable; amateur framing, computational-phone look, deep DOF.
- **Documentary / editorial** (photojournalism, street, reportage) → available light, decisive moment, grain, imperfect but intentional framing.
- **Professional commercial** (product, fashion, corporate portrait) → controlled light is fine, but real retouching standards: skin texture retained, real materials, real lighting setups you could draw.

Commercial ≠ CGI. A real commercial photo still has dust on the backdrop, a slightly hot specular, true lens perspective and skin pores.

## 2. Light (the #1 tell)

- **One motivated key source.** Name it: "late-afternoon sun from camera-left through a window", "overhead fluorescent tubes", "on-camera flash", "single softbox high camera-right". Fill comes from the environment (a white wall, the pavement), not from nowhere.
- **Direction → shadows.** Shadows must fall consistently away from the source, contact shadows under feet/objects must exist and be darkest at the contact point.
- **Colour temperature is physical:** candle ~1900K, tungsten ~2700–3200K, golden hour ~3500K, noon sun ~5500K, overcast ~6500K, shade ~7500K, cool-white LED/fluorescent with green tint. Mixed light (window + tungsten) gives a blue/orange split — real, not a "grade".
- **Dynamic range:** real cameras clip. A bright window behind a person either blows out or the person is silhouetted/dim (unless flash or phone HDR — which has its own look: flat, haloed edges). Say what clips.
- **Specular highlights** on skin (forehead, nose, cheekbones) and on materials reveal the light shape; eye catchlights must match the light source shape and position in **both** eyes.
- **Avoid**: "soft even lighting everywhere", "volumetric god rays" (unless there's actual dust/smoke and a hard source), "rim light" on every subject, "glowing".

## 3. Optics — make the camera consistent

| Framing | Typical focal length (FF equiv.) | Notes |
|---|---|---|
| Phone main camera | 24–26mm, f/1.6–1.9 tiny sensor | Deep DOF, slight wide-angle stretch at edges, computational HDR, oversharpening at 100% |
| Environmental portrait / street | 28–35mm | Context visible, mild perspective; subject not isolated |
| Documentary standard | 35–50mm | Natural perspective |
| Head-and-shoulders portrait | 85–135mm | Compressed background, flattering, shallow DOF at f/1.8–2.8 |
| Sports / wildlife | 300–600mm | Very compressed, creamy background, possible motion blur on limbs |
| Product tabletop | 90–100mm macro, f/8–f/11 | Mostly in focus; focus stacking only in pro work |
| Architecture / real estate | 16–24mm, verticals corrected | Straight verticals, HDR-bracketed or flash-ambient look |

Rules:
- **DOF must match** focal length × aperture × distance. A wide-angle phone photo does not have a creamy blurred background. A group of 6 people at f/1.4 will not all be sharp.
- Focus plane: name what is sharp ("focus on the near eye"). Real shots have slight misses; a tiny front-focus is credible.
- Lens character: mild vignetting wide open, slight lateral chromatic aberration at high-contrast edges, flare only when a light source is in or near frame, bokeh shape (onion-ring/cat-eye at frame edges with fast lenses).
- Perspective: wide lens close to a face enlarges the nose — only use when the register calls for it (selfies!).

## 4. Capture & processing artifacts (pick 1–3, never all)

- Sensor noise appropriate to ISO (ISO 100 clean; ISO 3200 visible luminance grain in shadows; phone night mode smeary noise reduction).
- Motion: slight motion blur on moving hands/feet at 1/60s; panning blur in sports.
- Film: Portra 400 (warm skin, soft pastel highlights, fine grain), Tri-X 400 (contrasty B/W, gritty grain), Cinestill 800T (halation red glow around lights, tungsten balance), disposable camera (flash falloff, vignette, soft corners, date stamp optional).
- Phone: HDR tone mapping (lifted shadows, slight halo at sky edges), oversharpening, JPEG compression, portrait-mode cutout errors around hair (only for vernacular register).
- Flash: hard shadow behind subject on the wall, bright foreground falloff to dark background, red-eye-free but specular skin, slightly blown highlights on foreheads.
- Composition imperfection: horizon tilt 1–3°, subject slightly off-centre, a cropped elbow or head of a passer-by at frame edge, foreground object partly blocking.

## 5. Human truth (people)

- **Skin**: visible pores especially on nose/cheeks, fine vellus hair, uneven tone, small blemishes, freckles/moles, under-eye texture, redness around nose, lip texture, natural shine on T-zone. Explicitly: "no airbrushing, no beauty filter, no skin smoothing".
- **Faces**: natural asymmetry, specific age markers, real teeth (not perfectly white/uniform), both eyes on the same specific target, slightly different eyelid heights.
- **Hair**: flyaways, uneven parting, strands crossing the face, hair that responds to wind/gravity.
- **Limbs & blocking** (the most common anatomy failure): models draw limbs from text statistics, not from a skeleton. So state how many people are in frame, place each one (seated/standing, side of the frame, facing where), and give **every visible hand a side and a task** ("his right hand holds the pen, his left hand keeps the paper flat"). Fewer visible hands mean fewer errors. Never ask for disembodied "hands doing X": say whose hands they are and where the body is ("seen over the shoulder of the woman at the desk"). Prefer framings in which arms visibly connect to shoulders; avoid interlocking hands, arms crossing between two people and many people touching.
- **Pose**: describe it as physics — where the weight is, what carries the body (chair, feet, elbow on the table), what touches what. Mid-action ("reaching for the salt"), weight shifted onto one leg, shoulders and hips slightly turned against each other; never a stiff, symmetric stance. A grip must work: a pen between thumb, index and middle finger; a cup by its handle; a phone with the thumb on the screen.
- **Expression (Mimik)**: never just "smiling". Write the emotion of the moment as visible muscle states and gaze: "eyes narrowed and cheeks lifted mid-laugh", "brows slightly drawn, lips pressed, eyes on the paper". A real smile reaches the eyes; a gaze needs a target in the scene. Allow asymmetry (one mouth corner higher) and in-between moments (half-closed eyes, mid-word mouth).
- **Clothing**: creases at elbows/waist, pilling on knitwear, lint, slightly crooked collar, real fabric names (heavyweight cotton, washed denim, merino, waxed canvas).
- **People in background**: few, small, doing ordinary things, partially occluded; crowds are high-risk → keep them out of focus or avoid.
- **Ethnicity, age, body type**: be specific and respectful; specificity reduces the model's "average stock person" face.

## 6. World truth (environments & objects)

- Specific over generic: not "a café" but "a narrow third-wave café in Lisbon, chipped azulejo tiles, chalkboard menu, a laptop sticker-covered".
- Clutter and evidence of use: receipts, cables, a half-drunk glass, crumbs, smudges on glass, scuffed floor, dust in light beams only where light actually crosses.
- Wear and weathering: chipped paint, rust streaks under bolts, worn handles, faded signage, sun-bleached plastic.
- Scale & contact: objects rest *on* surfaces (contact shadows, slight deformation of cushions), liquids have meniscus and refraction, reflections show the correct environment (windows, the photographer if appropriate).
- Text in the world: signs, labels, screens — keep minimal or quote exact text; gibberish text is the fastest AI giveaway. For background signage say "signage too far/blurred to read" if exact text isn't needed.

## 7. Colour & tone

- Default to **neutral, accurate white balance** for the stated light; say "no colour grading, no teal-and-orange look, no warm/sepia cast" unless the user wants a look.
- Real images have **limited saturation** in most areas, with colour concentrated in a few objects.
- Blacks are rarely pure black and whites rarely pure white except clipped areas.
- Avoid "vibrant", "rich colors", "dramatic", "cinematic" unless the brief is a film still or ad.

## 8. Vocabulary — what to write and what never to write

Write (photographic, physical, specific):
`candid`, `unposed`, `documentary photograph`, `shot on [camera] with [lens] at f/[x], 1/[y]s, ISO [z]`, `available light`, `on-camera flash`, `natural skin texture with visible pores`, `slight motion blur`, `fine film grain`, `JPEG straight out of camera`, `unretouched`, `slightly overexposed window`, `focus on the near eye`.

Never write (AI-art attractors):
`8k, 4k, ultra HD, ultra-detailed, hyperrealistic, hyper-detailed, photorealistic masterpiece, best quality, award-winning, trending on ArtStation, octane render, unreal engine, ray tracing, cinematic lighting, epic, stunning, gorgeous, flawless, perfect, beautiful lighting, sharp focus everywhere, highly detailed skin`.
"Photorealistic" itself is acceptable once (OpenAI guidance recommends it), but "a photograph taken by …" is stronger.

Camera/lens names are *appearance cues*, not physics simulation — use them for their associated look, and still state the physical facts (light, DOF, ISO effects) explicitly.

## 9. Why this beats the chat apps

Chat apps expand prompts generically ("a stunning, highly detailed photo…"), which pulls toward the glossy aesthetic average. This skill instead:
1. casts a real photographer and capture situation,
2. constrains physics (light, optics, DOF, colour temperature),
3. injects human/world specificity and plausible imperfection,
4. bans the AI-gloss vocabulary,
5. generates several candidates at the model's highest quality setting,
6. inspects every region of every image at full detail against a rubric and repairs locally.
