# Moroccan Parliament Asset Pack — Production Specification

## Goal
Build a complete, reusable Blendit asset library for the Moroccan Parliament as it stands in October 2026. The pack covers both constitutional chambers, not the government. It is a production task: generated files must be previewed, audited, imported into Godot, and checked before acceptance.

## Authoritative identity data
- House of Representatives: official 2026–2031 member directory: https://www.chambredesrepresentants.ma/ar/دليل-أعضاء-مجلس-النواب/2026-2031/
- Official election overview: https://maroc.ma/ar/الانتخابات-التشريعية-2026
- House of Councillors: use its official member directory and current institutional pages; do not infer its roster from the House of Representatives.
- Record each person's name as published, chamber, party/group when officially listed, office/role, source URL, source retrieval date, and reference-image status.
- Do not fabricate names, party affiliations, official positions, portraits, or likeness details. Missing data must be marked for verification, not guessed.
- The House of Representatives directory currently lists 395 seats/members for the 2026–2031 legislature. The two chambers have separate membership lists and different terms.

## Asset categories
1. Institutional environment: chamber interior, plenary seating, speaker's dais, lectern, desks, microphones, nameplates, lighting, doors, wall panels, architectural trim, and reusable seat/desk modules.
2. Shared human base assets: adult human base meshes, a balanced range of body proportions, formal clothing variants, shoes, hands, hair and facial-hair components, skin/hair/material presets, and neutral pose.
3. Individual representatives: one asset record per verified current member. A generic base model may be used only as a clearly labelled placeholder; it must not be presented as a faithful likeness. A likeness-specific asset requires a suitable, legally usable reference image and visual review.
4. Institutional roles: presiding officer and other office holders, with role metadata sourced from official pages. Do not conflate parliamentarians with ministers or candidates who did not win seats.
5. Presentation and technical assets: portrait turntables, neutral full-body previews, materials, rig/animation test scene, GLB exports, editable BLEND source, and manifest.

## Identity data schema
Use UTF-8 CSV or JSON with fields:
- id (stable slug)
- full_name_ar
- full_name_latin (when officially available)
- chamber (representatives | councillors)
- party_or_group
- official_role
- official_source_url
- source_checked_at (ISO date)
- reference_image_url
- reference_image_license_or_rights
- likeness_status (not_started | reference_needed | blocked_rights | generated | visually_reviewed)
- asset_status (not_started | placeholder | generated | audited | approved)
- notes

## Quality and acceptance gates
- Never claim that all individual character assets exist until every current member in both official directories has a row and a status.
- Validate roster uniqueness and completeness separately for each chamber; flag missing names and duplicates.
- Each generated GLB must have a valid glTF 2.0 header, non-empty meshes, sensible scale/origin, assigned materials, and no NaN/Inf transforms.
- Each individual asset needs a preview image and manifest entry tied to its stable member ID.
- Render the environment and representative assets with consistent studio lighting. Review actual preview images, not only a successful build.
- Import representative GLBs into a lit Godot test scene, inspect materials and orientation, test rig deformation if rigged, and record results.
- Keep high-detail source meshes and mobile-optimized variants separate where needed.
- Do not use party logos, national symbols, or institutional emblems unless sourced and cleared for the intended use.

## Delivery layout
- data/parliament/house_of_representatives_2026_2031.csv
- data/parliament/house_of_councillors_current.csv
- tools/blender/generate_parliament_pack.py
- build/parliament/manifest.json
- build/parliament/previews/
- build/parliament/glb/
- build/parliament/blend/
- build/parliament/godot-playtest.png
- build/parliament/quality-report.json

## Implementation sequence
1. Import and validate official rosters for both chambers; flag missing/ambiguous entries.
2. Build and visually review the chamber environment and reusable desk/seat modules.
3. Build the shared human base, clothing/material library, and rig test asset.
4. Generate per-member placeholders with correct metadata; keep placeholders visibly distinct from likeness-approved characters.
5. Add likenesses in batches only when reference images and rights are checked.
6. Run Blender generation, technical audit, preview review, and Godot import test. Publish generated binary packs as workflow artifacts rather than committing large binaries.
