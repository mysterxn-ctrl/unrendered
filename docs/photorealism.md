# Photorealism guide: how to make AI images look like real photos

This is the knowledge Unrendered compiles into every brief. It is useful on its own, with any image model.

## Realism is not beauty

The images people instantly accept as real are usually *ordinary*: a friend's phone shot across a kitchen table, a flash photo from a party, a press photo with a slightly crooked horizon. The images people instantly flag as AI are *too good*: flawless skin, light from nowhere, perfect symmetry, creamy background blur everywhere, no clutter, no reason to exist.

Image models learned "a photo of X" mostly from the most aesthetic, retouched and captioned pictures on the internet. Left alone, they drift toward that glossy average. Believability comes from three things instead:

1. **Physical consistency** — light, optics and materials that obey physics.
2. **Human specificity** — a real person with a reason to take this exact picture.
3. **Capture truth** — the small artifacts every real camera leaves behind.

## Pick a realism register

| Register | Typical source | Looks like |
|---|---|---|
| **Vernacular** | phone snapshot, party flash, holiday photo | deep depth of field, imperfect framing, phone processing — the most believable register |
| **Documentary** | street, reportage, editorial | available light, decisive moment, grain, intentional but imperfect framing |
| **Commercial** | product, fashion, corporate portrait | controlled light you could draw as a diagram, real materials, retouching that keeps texture |

Commercial does not mean CGI: a real studio photo still has dust on the backdrop, a slightly hot specular highlight, true lens perspective and skin pores.

## Light — the first giveaway

- **One motivated key light.** Name it: "late-afternoon sun from camera left through a window", "overhead fluorescent tubes", "on-camera flash".
- **Fill comes from the environment** — a white wall, the pavement — not from nowhere.
- **Shadows** fall consistently away from the source; contact shadows are darkest where objects touch.
- **Colour temperature is physical:** candle ≈ 1900 K, tungsten 2700–3200 K, golden hour ≈ 3500 K, noon sun ≈ 5500 K, overcast ≈ 6500 K, shade ≈ 7500 K. Mixed light gives a real blue/orange split — not a colour grade.
- **Dynamic range:** cameras clip. A bright window behind a person either blows out or the person goes dark.
- **Catchlights** match the shape and position of the light source in *both* eyes.

## Optics — keep the camera consistent

| Framing | Focal length (full-frame equivalent) | Consequence |
|---|---|---|
| Phone main camera | 24–26 mm, tiny sensor | almost everything sharp, slight wide-angle stretch, HDR processing |
| Environmental portrait, street | 28–35 mm | context visible, subject not isolated |
| Documentary standard | 35–50 mm | natural perspective |
| Head-and-shoulders portrait | 85–135 mm | compressed, softly blurred background |
| Sports, wildlife | 300–600 mm | strongly compressed background, motion blur on limbs |
| Product tabletop | 90–100 mm macro at f/8–f/11 | most of the product sharp |
| Interiors | 16–24 mm | straight verticals |

Depth of field must follow focal length, aperture and distance. A wide-angle phone photo does not have a creamy background; six people at f/1.4 will not all be sharp. Name the focus point ("focus on the near eye").

## Capture artifacts — choose one to three

- sensor noise matching the ISO (clean at ISO 100, visible grain at ISO 3200),
- slight motion blur on moving hands at 1/60 s,
- film character: Portra 400 (warm skin, soft highlights), Tri-X (contrasty black and white), CineStill 800T (red halation around lights),
- phone processing: lifted shadows, slight halos at sky edges, over-sharpening,
- on-camera flash: hard shadow on the wall behind, fast fall-off into darkness,
- composition: horizon tilted 1–3°, a cropped elbow at the frame edge.

Never all at once — that becomes a filter, not a photograph.

## Design out what models get wrong

Unrendered renders once, so the brief has to be right the first time. Before writing, it keeps what you asked for but picks the version of the picture a model renders reliably:

| Risk | One-shot choice |
|---|---|
| Hands as the subject | Forearms in frame; say whose hands they are, from which side they enter, where the body is; at most two hands |
| People touching | At most two people in contact; each person's arms described separately — or the moment just before or after |
| Groups | At most three people in focus; everyone else far away or out of focus |
| Complex poses | A stable, well-known moment, described joint by joint |
| Small tools in hands | The grip named exactly, seen from the side |
| Interlaced fingers, crossed arms | Hands apart, each on its own object |
| Teeth in close-up | Closed or slightly open mouth, unless laughter is the point |
| Text | Only when asked; quoted, short, large, facing the camera |
| Screens, mirrors | Screen dark or simple; mirrors avoided or their reflection described |
| Frame-filling foliage, fur, crowds | Smaller area, partly out of focus |

How the brief is written matters as much: most important facts first, one fact per sentence, everything anchored in the frame (left third, foreground, what is in front of what), one block per person in the same order (position, weight, right hand, left hand, face), the correct state described positively rather than a list of anatomy errors, counts stated, and no contradictions between lens and blur or light and shadows.

## People

- **Skin:** visible pores, fine vellus hair, uneven tone, small blemishes, natural shine on the T-zone. Say "unretouched, no skin smoothing".
- **Faces:** natural asymmetry, real teeth, both eyes on the same specific target.
- **Hair:** flyaways, strands crossing the face, reacting to wind and gravity.
- **Limbs:** models draw arms and hands from text statistics, not from a skeleton. State how many people are in frame, place each one, and give every visible hand a side and a task ("his right hand holds the pen, his left keeps the paper flat"). Fewer visible hands mean fewer errors. Never ask for disembodied "hands doing X" — say whose hands they are and where the body is.
- **Pose:** describe it as physics — where the weight is, what carries the body, what touches what. Mid-action ("reaching for the salt"), shoulders and hips slightly turned against each other, never a stiff, symmetric stance. A grip must work: a pen between thumb, index and middle finger; a cup by its handle.
- **Expression:** never just "smiling". Write the moment as eyes, brows, mouth and gaze target: "eyes narrowed and cheeks lifted mid-laugh", "brows slightly drawn, lips pressed, eyes on the paper". A real smile reaches the eyes.
- **Clothing:** creases at elbows and waist, pilling on knitwear, real fabric names.
- **Background people:** few, small, out of focus.

## Places and objects

- Specific beats generic: not "a café" but "a narrow neighbourhood café, chipped tiles, chalkboard menu, rain on the window".
- Evidence of use: receipts, cables, crumbs, fingerprints on glass, scuffed floors.
- Wear: chipped paint, rust streaks, faded signage.
- Contact and physics: objects rest *on* surfaces, liquids refract, reflections show the actual environment.
- Text: keep it minimal and quote it exactly — gibberish signage is the fastest AI giveaway. Otherwise ask for signage too far away to read.

## Colour

Default to neutral white balance for the stated light. Real photos have restrained saturation with colour concentrated in a few objects. Ask for "no colour grading, no teal-and-orange look, no warm cast" unless a look is wanted.

## Words that help — and words that hurt

**Use:** candid · unposed · documentary photograph · shot on a 35 mm lens at f/2.8, 1/125 s, ISO 1600 · available light · on-camera flash · unretouched · visible pores · slight motion blur · fine grain · slightly overexposed window · focus on the near eye.

**Avoid:** 8k · 4k · ultra-detailed · hyperrealistic · masterpiece · best quality · award-winning · trending · octane render · unreal engine · cinematic lighting · epic · stunning · flawless · perfect. These pull the image toward glossy CGI.

Camera and lens names are cues for a *look*, not physics simulation — always state the physical facts (light, depth of field, noise) as well.

## The brief template

```text
A real photograph, not an illustration or render.

Photographer & purpose: <who took it, why>
Scene: <specific place, time, weather; specific objects and clutter>
Subject: <concrete physical details; mid-action; materials and wear>
Bodies & pose: <people counted and placed; what each visible hand does, left and right; weight and support>
Face & expression: <eyes, brows, mouth and gaze target for this moment>
Composition: <shot size, camera height, placement, what crosses the frame edges, aspect>
Camera & capture: <camera, focal length, aperture, shutter, ISO; focus point; resulting DOF>
Light: <one key source, direction, colour temperature; fill; what clips>
Texture & realism: <each main material with its texture and wear; 1–3 capture artifacts>
Colour: <neutral white balance for this light; saturation; no grade>
Text: <"exact text" with placement | No readable text anywhere.>
Avoid: airbrushed skin, plastic sheen, CGI look, HDR glow, cinematic grade, watermark, logos.
```

### Example — "a man drinking coffee"

```text
A real photograph, not an illustration or render.

Photographer & purpose: candid documentary photo taken by a friend sitting across the table.
Scene: small neighbourhood café on a grey November morning; rain-speckled window, condensation at
the edges, a crumpled sugar wrapper and a half-eaten croissant on a scratched dark-wood table.
Subject: a man in his late 40s with a short salt-and-pepper beard, reading glasses pushed up on his
head, pilled navy merino sweater.
Bodies & pose: one person, seated alone; right elbow on the table, right hand holds a white ceramic
cup by the handle just below his mouth; left forearm on the table, left hand flat beside the saucer.
Face & expression: lips pursed, blowing on the coffee; eyes half-lowered towards the window, brows
relaxed; a still-tired early-morning look.
Composition: medium close-up from across the table at seated eye level, subject right of centre,
edge of the window frame entering left, 3:2.
Camera & capture: full-frame mirrorless, 50 mm at f/2.8, 1/125 s, ISO 1600; focus on the near eye.
Light: overcast daylight from the window camera-left as the only key (~6500 K), faint warm pendant
behind; gentle fall-off into shadow.
Texture & realism: visible pores and fine lines, stray beard hairs, pilled wool, worn wood grain,
faint steam, slight ISO grain, horizon very slightly tilted.
Colour: neutral cool daylight with a little warm spill; muted saturation.
Text: no readable text anywhere.
Avoid: airbrushed skin, glossy commercial look, cinematic grade, watermark, logos.
```

## Genre recipes

The skill ships twenty genre recipes — each defines who shoots, the gear, the light, the look and what to avoid:

phone snapshot · on-camera flash snapshot · street / documentary · photojournalism style · environmental portrait · classic headshot · wedding and events · studio product · lifestyle product · food · real estate and interiors · landscape and travel · sports · night ambient · film emulation · selfie · corporate and office · drone / aerial · macro and nature · archival / historical.

They live in `skills/unrendered/references/photo-genres.md`.
