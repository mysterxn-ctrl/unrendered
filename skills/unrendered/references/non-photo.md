# Non-photo requests (any topic)

Default output is a real-looking photograph. Use this file only when the user explicitly wants another medium. Model selection, providers, candidates, QA and repair stay the same; only the brief changes.

## Labeled spec
```
Use case: <slug below>
Asset type: <where it will be used>
Primary request: <user's main ask>
Input images: <Image 1: role; Image 2: role> (optional)
Scene/backdrop: <environment>
Subject: <main subject>
Style/medium: <illustration / 3D render / watercolor / flat vector-style / isometric …>
Composition/framing: <wide/close/top-down; placement; negative space for copy if needed>
Lighting/mood: <lighting + mood>
Color palette: <palette notes>
Materials/textures: <surface details>
Text (verbatim): "<exact text>"
Constraints: <must keep / must avoid>
Avoid: <negative constraints>
```

## Use cases
- **product-mockup** — packaging/catalog; clean silhouette, label clarity, verbatim text. (Usually still a photo → main playbook.)
- **ui-mockup** — state fidelity first (shippable mockup vs wireframe); layout, hierarchy, real UI elements; no concept-art words.
- **infographic-diagram** — audience, reading flow, every label verbatim; high quality for dense text; check every number.
- **scientific-educational** — lesson goal, required labels, scientific accuracy constraints, whitespace.
- **ads-marketing** — write like a creative brief: audience, positioning, vibe, scene, exact tagline.
- **productivity-visual** — slide/chart/workflow; give real data and labels; readable typography.
- **logo-brand** — simple, scalable, strong silhouette, balanced negative space; prefer vector tools if the user needs an editable logo.
- **illustration-story** — panel/scene beats, concrete actions, consistent character sheet.
- **stylized-concept** — style cues, material finish, rendering approach; don't invent story.
- **historical-scene** — place/date; period-accurate clothing, props, architecture.

## Rules carried over
- Don't add characters, brands, slogans or story beats the user didn't imply.
- Exact text in quotes; spell tricky words letter by letter; ask for no extra text.
- Transparent background: request it via the API parameter (`background=transparent`, PNG/WebP) if the model supports it — a drawn checkerboard is not transparency.
- If the request is better served by SVG/HTML/CSS (simple icons, diagrams in a codebase), say so and do that instead.
