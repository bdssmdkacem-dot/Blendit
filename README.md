# Blendit — 3D Asset Production Workshop

Blendit is the central, reusable Blender asset-generation workshop for game development and video production.

## Goals

- Generate reusable 3D props, environments, materials, and scene building blocks with Blender Python.
- Export editable Blender scenes and engine-friendly glTF 2.0 / GLB assets.
- Render preview images and write a manifest for every generated pack.
- Run generation and smoke checks automatically in GitHub Actions.
- Keep source scripts in Git; publish generated binary packs as workflow artifacts so the repository stays lightweight.

## Current starter pack

The initial procedural pack contains stylized fantasy props (a wooden crate, brass lantern, crystal, barrel, and a mahogany/brass carriage-inspired prop). It is a foundation for expanding into characters, rigging, animation, environments, VFX, and cinematic shot templates.

## Requirements

- Blender 4.2 or newer (the CI workflow installs Blender on Ubuntu).
- Python scripts run through Blender's bundled Python and `bpy` API.

## Run locally

From the repository root, run:

```bash
blender --background --factory-startup --python tools/blender/generate_asset_pack.py -- --output-dir build/assets
```

Outputs include:
- `build/assets/blendit_asset_pack.blend`
- `build/assets/blendit_asset_pack.glb`
- `build/assets/preview.png`
- `build/assets/manifest.json`

## Automated generation

Use **Actions → Generate Blender Asset Pack → Run workflow**. The workflow installs Blender, generates the pack headlessly, checks that the expected files exist and are non-empty, then uploads the pack as a downloadable workflow artifact.

## Asset production rules

1. Prefer procedural, editable source over opaque one-off outputs.
2. Use sensible scale, named objects/materials, clean transforms, and predictable export settings.
3. Check that exports are produced before calling a generation run successful.
4. Keep mobile game assets reasonably lightweight; create higher-detail cinematic variants when needed.
5. Track third-party assets and their licenses separately. Generated assets should not silently bundle unlicensed external content.

## Planned expansion

- Modular environment and architecture generator
- Character base meshes, rigs, and animation-ready export
- Cinematic camera, lighting, and shot-sequence templates
- Material and texture libraries
- Batch generation by category and reusable presets
- Automated import/export smoke tests for Godot and other target tools
