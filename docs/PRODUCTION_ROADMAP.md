# Blendit production roadmap

Blendit is intended to be a reusable production workshop, not a single-project asset dump. Keep procedural source, output validation, and usage notes alongside each generator.

## Phase 1 — Reliable asset factory
- [x] Install Blender in a clean GitHub Actions runner.
- [x] Generate a starter procedural prop pack.
- [x] Save an editable .blend master scene.
- [x] Export a combined GLB and individual GLBs.
- [x] Render a PNG preview.
- [x] Validate the GLB header/declared length, PNG signature, manifest entries, and non-empty outputs.
- [ ] Confirm the latest GitHub Actions run is green and inspect the rendered preview.

## Phase 2 — Game-ready modular packs
- Modular environment pieces: walls, floors, stairs, doors, bridges, platforms, rocks, trees, and foliage.
- Export profiles for Godot and other glTF-compatible engines.
- Per-asset scale, origin, collision proxy, object naming, and polygon-budget metadata.
- Separate mobile/low-poly and cinematic/high-detail variants.
- Automated validation for mesh presence, missing materials, dimensions, and polygon counts.

## Phase 3 — Video and cinematic production
- Reusable scene templates with camera rigs, key/fill/rim lighting, and render profiles.
- Shot-sequence templates with camera cuts and timeline markers.
- Reusable environment and prop libraries.
- Animation-ready scene organization and render previews.
- Optional output presets for vertical, widescreen, and square video.

## Phase 4 — Character and animation pipeline
- Character base meshes and modular accessories.
- Rigging and animation test scenes.
- Export checks for skeletons, actions, material slots, and transforms.
- Keep generated character geometry as a starting point; production characters require visual review and cleanup.

## Production rules
1. A successful commit is not a successful generation run.
2. A successful generation run is not visual approval: inspect the PNG preview and open representative exports in the target engine.
3. Never overwrite source assets with generated output.
4. Store large generated binaries as workflow artifacts or release assets, not routine Git commits.
5. Record the Blender version and generator version in every manifest.
6. Keep third-party assets and their licenses documented.
