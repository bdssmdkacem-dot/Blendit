# Blendit — 3D Asset Production Workshop

Blendit is the central, reusable Blender asset-generation workshop for game development and video production.

## Goals

- Generate reusable 3D props, environments, materials, and scene building blocks with Blender Python.
- Export editable Blender scenes and engine-friendly glTF 2.0 / GLB assets.
- Render preview images and write a manifest for every generated pack.
- Run generation and smoke checks automatically in GitHub Actions.
- Keep source scripts in Git; publish generated binary packs as workflow artifacts so the repository stays lightweight.

## Current starter pack

The procedural pack now contains nine stylized fantasy assets: a wooden crate, brass lantern, crystal, barrel, mahogany/brass carriage-inspired prop, low-poly rock cluster, evergreen pine, modular stone wall segment, and wooden bridge segment. These are reusable starting assets, not finished production art; inspect the preview and import representative GLBs into the target engine before shipping.

## Requirements

- Blender 4.2 or newer (the CI workflow installs Blender on Ubuntu).
- Python scripts run through Blender's bundled Python and `bpy` API.

## Run locally

From the repository root, run:

```bash
blender --background --factory-startup --python tools/blender/generate_asset_pack.py -- --output-dir build/assets
python3 tools/blender/audit_asset_quality.py build/assets
```

Outputs include:
- `build/assets/blendit_asset_pack.blend` — editable master scene
- `build/assets/blendit_asset_pack.glb` — combined GLB pack
- `build/assets/crate.glb`, `lantern.glb`, `crystal.glb`, `barrel.glb`, `carriage.glb`, `rock_cluster.glb`, `pine_tree.glb`, `stone_wall.glb`, `bridge_segment.glb` — standalone assets
- `build/assets/preview.png` — rendered Blender contact-sheet-style scene preview
- `build/assets/godot-playtest.png` — actual Godot 4 scene render with imported GLBs, game-style lighting, ground, and collision proxies
- `build/assets/manifest.json` — asset inventory and generator metadata
- `build/assets/asset_quality_report.json` — per-asset mesh/primitive/triangle/material counts from the technical GLB audit

## Automated generation

Use **Actions → Generate Blender Asset Pack → Run workflow**. The workflow installs Blender, generates the pack headlessly, checks that the expected files exist and are non-empty, validates each GLB header and each standalone asset's local coordinates, then runs a technical GLB audit (renderable primitives, vertex/triangle counts, and material assignments), imports the standalone GLBs into a lit Godot 4 play scene with collision proxies, and uploads the pack plus `asset_quality_report.json` as a downloadable workflow artifact. A passing technical audit does not replace visual review of `preview.png` or actual inspection of the Godot scene.

## Asset production rules

1. Prefer procedural, editable source over opaque one-off outputs.
2. Use sensible scale, named objects/materials, clean transforms, and predictable export settings.
3. Export every standalone GLB around its own local origin; scene-layout coordinates belong only in the combined pack/preview.
4. Check file structure, manifest completeness, PNG signature, and standalone GLB local coordinates before calling a generation run successful.
5. Keep mobile game assets reasonably lightweight; create higher-detail cinematic variants when needed.
6. Track third-party assets and their licenses separately. Generated assets should not silently bundle unlicensed external content.

## Planned expansion

- Modular environment and architecture generator
- Character base meshes, rigs, and animation-ready export
- Cinematic camera, lighting, and shot-sequence templates
- Material and texture libraries
- Batch generation by category and reusable presets
- Automated import/export smoke tests for Godot and other target tools

## Android companion app (PC-hosted Blender)

A first Android client lives in `android_app/`. It connects over a trusted local network to a computer running Blender and this repository's local bridge. The phone is the control panel; the computer performs the actual 3D generation.

### Run the bridge on your computer

1. Install Blender 4.2+ and Python 3.10+; clone this repository.
2. Open a terminal in the repository root.
3. Set a private token with at least 20 characters, then start the service:

   **Linux/macOS**
   ```bash
   export BLENDIT_TOKEN='replace-with-a-long-private-random-token'
   python3 tools/server/blendit_server.py
   ```

   **Windows PowerShell**
   ```powershell
   $env:BLENDIT_TOKEN = "replace-with-a-long-private-random-token"
   py tools/server/blendit_server.py
   ```

4. Find your computer's private LAN IP address (for example `192.168.1.10`). Allow TCP port `8765` only on your private/home network if the firewall asks.
5. Keep the phone and computer on the same trusted Wi-Fi. In the app, enter `http://COMPUTER-LAN-IP:8765` and the same token.
6. Tap **توليد الحزمة الأولية على الحاسوب**. The app will show the job state and let you preview/share the resulting files.

Do not expose port 8765 to the public internet or use this plain-HTTP bridge on an untrusted network. The token is a local-network safeguard, not a replacement for TLS on the internet.

### Android project status

- The first client includes connection settings, a generation-job status view, preview, asset listing, and file sharing.
- The first bridge release deliberately runs only the reviewed starter-pack generator. It does not execute arbitrary code or claim to create custom prompts, rigged characters, animations, or full scenes yet.
- CI runs bridge API safety tests, Flutter analysis/widget tests, and builds a debug APK artifact. A green workflow is required before calling that build verified.
- The current workflow generates Android platform scaffolding during CI; run `flutter create --platforms=android --project-name blendit_mobile --org com.blendit .` from `android_app/`, then run `python tool/prepare_android.py` there before building locally for the first time. The helper enables cleartext HTTP for the private-LAN bridge; do not expose this development setup to the public internet.

## Moroccan Parliament architecture pack

A separate procedural Blender generator now creates a reference-led exterior building asset and an interior domed plenary-chamber asset. It is an architectural interpretation for prototyping, not a survey-accurate replica; compare against licensed/current references before claiming exact fidelity.

### Generate locally

```bash
blender --background --factory-startup --python tools/blender/generate_parliament_pack.py -- --output-dir build/parliament --samples 32
```

Outputs:
- `build/parliament/moroccan_parliament_master.blend` — editable combined scene
- `build/parliament/parliament_exterior.glb` — exterior building, entrance, forecourt and landscaping
- `build/parliament/parliament_domed_chamber.glb` — circular plenary room, dome, radial ribs, seating, desks, microphones, dais and lighting
- `build/parliament/preview_exterior.png` and `preview_interior.png` — rendered review images
- `build/parliament/manifest.json` — output inventory and review status

GitHub Actions → **Generate Moroccan Parliament Architecture Pack** runs the generator and validates output existence, GLB headers and PNG signatures, then uploads an artifact. These checks do not replace visual review or import testing in Godot. The Android bridge currently runs only the starter pack; this custom generator is run locally or through its dedicated workflow, not yet through the phone app.

## Fictional satirical parliament character cast

The purpose of the parliament assets is now video production as well as environment prototyping. A separate generator creates six **fictional, anonymous caricature archetypes** to stage inside the domed chamber: an over-the-top orator, a phone-scroller, a sleepy member, a paper-shuffler, a defensive shrugger, and an opposition-style speaker. These are satire-ready placeholders, not portraits or claims about any real member. The first pass exports separate named character parts, GLBs, per-character rendered previews, and a manifest. It is **not yet armature-rigged**; body parts are separated to support a later rigging/animation pass.

### Generate locally

```bash
blender --background --factory-startup --python tools/blender/generate_parliament_satire_characters.py -- --output-dir build/parliament-characters --samples 16
```

GitHub Actions → **Generate Fictional Parliament Satire Characters** creates the cast and checks each GLB structure, material variety, and rendered preview dimensions. Download the `fictional-parliament-satire-characters` artifact, inspect every preview, then import representative characters and the chamber into the target scene before accepting them. A passing technical check is not proof of visual quality. The Android companion app does not yet expose these custom generators.

Suggested production sequence: establish the chamber as a reusable stage; review the six characters; add a verified rig and short reusable animation clips (speaking, listening, looking at a phone, dozing, shuffling papers, reacting); then build camera shots and edit the satirical scene. Keep invented dialogue/actions clearly fictional and avoid presenting caricatures as real-person likenesses.

